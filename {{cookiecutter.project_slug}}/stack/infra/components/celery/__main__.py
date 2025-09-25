"""Pulumi infrastructure for Celery worker deployment.

Deploys:
- ECS Fargate service for Celery workers
- ECS Fargate service for Celery Beat scheduler
- ECS Fargate service for Flower monitoring
"""

import json

import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
env = pulumi.get_stack()
project_name = pulumi.get_project()

# Get foundation stack outputs
foundation_stack = pulumi.StackReference(
    config.require("foundation_stack"), pulumi.StackReference
)
vpc_id = foundation_stack.require_output("vpc_id")
subnet_ids = foundation_stack.require_output("public_subnet_ids")
ecr_url = foundation_stack.require_output("ecr_repository_url")
redis_endpoint = foundation_stack.require_output("redis_endpoint")
event_bus_arn = foundation_stack.require_output("event_bus_arn")
main_queue_url = foundation_stack.require_output("main_queue_url")
dlq_url = foundation_stack.require_output("dlq_url")

# Tagging
tags = {
    "Project": project_name,
    "Component": "celery",
    "Environment": env,
    "ManagedBy": "Pulumi",
}

# IAM roles for ECS tasks
task_role = aws.iam.Role(
    "celery-task-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Effect": "Allow",
                }
            ],
        }
    ),
    tags=tags,
)

task_execution_role = aws.iam.Role(
    "celery-execution-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Effect": "Allow",
                }
            ],
        }
    ),
    tags=tags,
)

aws.iam.RolePolicyAttachment(
    "celery-execution-policy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# Task policy for Celery workers
task_policy = aws.iam.Policy(
    "celery-task-policy",
    policy=pulumi.Output.all(event_bus_arn).apply(
        lambda args: json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": ["events:PutEvents"],
                        "Resource": args[0],
                    },
                    {"Effect": "Allow", "Action": ["sqs:*"], "Resource": "*"},
                    {
                        "Effect": "Allow",
                        "Action": ["dynamodb:*"],
                        "Resource": "*",  # Should be more restrictive in production
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["ssm:GetParameter", "ssm:GetParameters"],
                        "Resource": "*",
                    },
                    {
                        "Effect": "Allow",
                        "Action": ["ses:SendEmail", "ses:SendRawEmail"],
                        "Resource": "*",
                    },
                ],
            }
        )
    ),
)

aws.iam.RolePolicyAttachment(
    "celery-task-attachment", role=task_role.name, policy_arn=task_policy.arn
)

# CloudWatch Log Groups
worker_log_group = aws.cloudwatch.LogGroup(
    "celery-worker-logs",
    name=f"/ecs/celery-worker-{env}",
    retention_in_days=7,
    tags=tags,
)

beat_log_group = aws.cloudwatch.LogGroup(
    "celery-beat-logs", name=f"/ecs/celery-beat-{env}", retention_in_days=7, tags=tags
)

flower_log_group = aws.cloudwatch.LogGroup(
    "celery-flower-logs",
    name=f"/ecs/celery-flower-{env}",
    retention_in_days=7,
    tags=tags,
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster("celery-cluster", name=f"celery-{env}", tags=tags)

# Security Group
celery_security_group = aws.ec2.SecurityGroup(
    "celery-sg",
    vpc_id=vpc_id,
    description="Security group for Celery workers",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            from_port=5555,
            to_port=5555,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],  # For Flower UI
            description="Flower monitoring UI",
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0, to_port=0, protocol="-1", cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags=tags,
)

# Celery Worker Task Definition
worker_task_definition = aws.ecs.TaskDefinition(
    "celery-worker-task",
    family=f"celery-worker-{env}",
    cpu="512",
    memory="1024",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(
        ecr_url, redis_endpoint, worker_log_group.name, main_queue_url
    ).apply(
        lambda args: json.dumps(
            [
                {
                    "name": "celery-worker",
                    "image": f"{args[0]}:celery-worker-{env}-latest",
                    "cpu": 512,
                    "memory": 1024,
                    "essential": True,
                    "command": [
                        "celery",
                        "-A",
                        "entry_points.celery_worker.app",
                        "worker",
                        "--loglevel=info",
                        "--concurrency=2",
                    ],
                    "environment": [
                        {"name": "ENVIRONMENT", "value": env},
                        {
                            "name": "CELERY_BROKER_URL",
                            "value": f"redis://{args[1]}:6379/0",
                        },
                        {
                            "name": "CELERY_RESULT_BACKEND",
                            "value": f"redis://{args[1]}:6379/0",
                        },
                        {"name": "REDIS_HOST", "value": args[1]},
                        {"name": "REDIS_PORT", "value": "6379"},
                        {"name": "SQS_QUEUE_URL", "value": args[3]},
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": args[2],
                            "awslogs-region": aws.get_region().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                }
            ]
        )
    ),
    tags=tags,
)

# Celery Beat Task Definition
beat_task_definition = aws.ecs.TaskDefinition(
    "celery-beat-task",
    family=f"celery-beat-{env}",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(
        ecr_url, redis_endpoint, beat_log_group.name
    ).apply(
        lambda args: json.dumps(
            [
                {
                    "name": "celery-beat",
                    "image": f"{args[0]}:celery-worker-{env}-latest",
                    "cpu": 256,
                    "memory": 512,
                    "essential": True,
                    "command": [
                        "celery",
                        "-A",
                        "entry_points.celery_worker.app",
                        "beat",
                        "--loglevel=info",
                    ],
                    "environment": [
                        {"name": "ENVIRONMENT", "value": env},
                        {
                            "name": "CELERY_BROKER_URL",
                            "value": f"redis://{args[1]}:6379/0",
                        },
                        {
                            "name": "CELERY_RESULT_BACKEND",
                            "value": f"redis://{args[1]}:6379/0",
                        },
                        {"name": "REDIS_HOST", "value": args[1]},
                        {"name": "REDIS_PORT", "value": "6379"},
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": args[2],
                            "awslogs-region": aws.get_region().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                }
            ]
        )
    ),
    tags=tags,
)

# Flower Task Definition
flower_task_definition = aws.ecs.TaskDefinition(
    "celery-flower-task",
    family=f"celery-flower-{env}",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(
        redis_endpoint, flower_log_group.name
    ).apply(
        lambda args: json.dumps(
            [
                {
                    "name": "celery-flower",
                    "image": "mher/flower:latest",
                    "cpu": 256,
                    "memory": 512,
                    "essential": True,
                    "command": [
                        "celery",
                        "--broker=redis://" + args[0] + ":6379/0",
                        "flower",
                        "--port=5555",
                    ],
                    "portMappings": [{"containerPort": 5555, "protocol": "tcp"}],
                    "environment": [
                        {
                            "name": "CELERY_BROKER_URL",
                            "value": f"redis://{args[0]}:6379/0",
                        },
                        {"name": "FLOWER_PORT", "value": "5555"},
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": args[1],
                            "awslogs-region": aws.get_region().name,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                }
            ]
        )
    ),
    tags=tags,
)

# ECS Service for Celery Worker (can scale horizontally)
worker_service = aws.ecs.Service(
    "celery-worker-service",
    name=f"celery-worker-{env}",
    cluster=ecs_cluster.id,
    task_definition=worker_task_definition.arn,
    desired_count=config.get_int("worker_count") or 2,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=subnet_ids,
        security_groups=[celery_security_group.id],
        assign_public_ip=True,
    ),
    tags=tags,
)

# ECS Service for Celery Beat (only one instance)
beat_service = aws.ecs.Service(
    "celery-beat-service",
    name=f"celery-beat-{env}",
    cluster=ecs_cluster.id,
    task_definition=beat_task_definition.arn,
    desired_count=1,  # Only one Beat scheduler
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=subnet_ids,
        security_groups=[celery_security_group.id],
        assign_public_ip=True,
    ),
    tags=tags,
)

# ALB for Flower
flower_alb = aws.lb.LoadBalancer(
    "flower-alb",
    name=f"flower-{env}",
    internal=False,
    load_balancer_type="application",
    security_groups=[celery_security_group.id],
    subnets=subnet_ids,
    tags=tags,
)

flower_target_group = aws.lb.TargetGroup(
    "flower-tg",
    name=f"flower-{env}",
    port=5555,
    protocol="HTTP",
    vpc_id=vpc_id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        healthy_threshold=2,
        interval=30,
        matcher="200-299",
        path="/",
        port="5555",
        protocol="HTTP",
        timeout=5,
        unhealthy_threshold=3,
    ),
    tags=tags,
)

flower_listener = aws.lb.Listener(
    "flower-listener",
    load_balancer_arn=flower_alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward", target_group_arn=flower_target_group.arn
        )
    ],
)

# ECS Service for Flower
flower_service = aws.ecs.Service(
    "celery-flower-service",
    name=f"celery-flower-{env}",
    cluster=ecs_cluster.id,
    task_definition=flower_task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=subnet_ids,
        security_groups=[celery_security_group.id],
        assign_public_ip=True,
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=flower_target_group.arn,
            container_name="celery-flower",
            container_port=5555,
        )
    ],
    depends_on=[flower_listener],
    tags=tags,
)

# Auto-scaling for Celery workers
app_scaling_target = aws.appautoscaling.Target(
    "worker-scaling-target",
    service_namespace="ecs",
    resource_id=pulumi.Output.concat(
        "service/", ecs_cluster.name, "/", worker_service.name
    ),
    scalable_dimension="ecs:service:DesiredCount",
    min_capacity=1,
    max_capacity=10,
)

# CPU-based auto-scaling
cpu_scaling_policy = aws.appautoscaling.Policy(
    "worker-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=app_scaling_target.resource_id,
    scalable_dimension=app_scaling_target.scalable_dimension,
    service_namespace=app_scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
        predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
            predefined_metric_type="ECSServiceAverageCPUUtilization"
        ),
        target_value=70.0,
        scale_in_cooldown=300,
        scale_out_cooldown=60,
    ),
)

# Outputs
pulumi.export("worker_service", worker_service.name)
pulumi.export("beat_service", beat_service.name)
pulumi.export("flower_service", flower_service.name)
pulumi.export("flower_url", flower_alb.dns_name)
pulumi.export("ecs_cluster", ecs_cluster.name)
pulumi.export("worker_count", worker_service.desired_count)
