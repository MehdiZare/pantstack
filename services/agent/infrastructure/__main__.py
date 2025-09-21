"""Infrastructure for Agent Service"""
import pulumi
import pulumi_aws as aws
from pulumi import Config, Output, export

# Get configuration
config = Config()
env = config.require("env")
project_name = config.require("project_name")

# Service configuration
service_name = "agent"
cpu = config.get_int("cpu") or 512
memory = config.get_int("memory") or 1024
desired_count = config.get_int("desired_count") or 2

# Import shared infrastructure components
# In production, these would be imported from stack references
vpc_id = config.require("vpc_id")
subnet_ids = config.require_object("subnet_ids")
cluster_arn = config.require("cluster_arn")
load_balancer_arn = config.require("load_balancer_arn")

# Create CloudWatch log group
log_group = aws.cloudwatch.LogGroup(
    f"{service_name}-logs",
    name=f"/ecs/{project_name}/{env}/{service_name}",
    retention_in_days=7,
)

# Create task execution role
task_execution_role = aws.iam.Role(
    f"{service_name}-task-execution-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            }
        }]
    }""",
)

# Attach policies to execution role
aws.iam.RolePolicyAttachment(
    f"{service_name}-execution-policy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# Create task role for application permissions
task_role = aws.iam.Role(
    f"{service_name}-task-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            }
        }]
    }""",
)

# Create SQS queue for task processing
task_queue = aws.sqs.Queue(
    f"{service_name}-task-queue",
    name=f"{project_name}-{env}-{service_name}-tasks",
    visibility_timeout_seconds=300,
    message_retention_seconds=86400,  # 1 day
    redrive_policy={
        "deadLetterTargetArn": dlq.arn,
        "maxReceiveCount": 3,
    },
)

# Create dead letter queue
dlq = aws.sqs.Queue(
    f"{service_name}-dlq",
    name=f"{project_name}-{env}-{service_name}-dlq",
    message_retention_seconds=1209600,  # 14 days
)

# Add SQS permissions to task role
sqs_policy = aws.iam.RolePolicy(
    f"{service_name}-sqs-policy",
    role=task_role.id,
    policy=pulumi.Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:SendMessage",
                "sqs:GetQueueAttributes",
                "sqs:ChangeMessageVisibility",
            ],
            "Resource": [task_queue.arn, dlq.arn],
        }],
    }),
)

# Create S3 bucket for task artifacts
artifact_bucket = aws.s3.Bucket(
    f"{service_name}-artifacts",
    bucket=f"{project_name}-{env}-{service_name}-artifacts",
    versioning={"enabled": True},
    server_side_encryption_configuration={
        "rule": {
            "apply_server_side_encryption_by_default": {
                "sse_algorithm": "AES256",
            },
        },
    },
)

# Add S3 permissions to task role
s3_policy = aws.iam.RolePolicy(
    f"{service_name}-s3-policy",
    role=task_role.id,
    policy=pulumi.Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
            ],
            "Resource": [
                artifact_bucket.arn,
                pulumi.Output.concat(artifact_bucket.arn, "/*"),
            ],
        }],
    }),
)

# Create ECS task definition for API
api_task_definition = aws.ecs.TaskDefinition(
    f"{service_name}-api-task",
    family=f"{project_name}-{env}-{service_name}-api",
    cpu=str(cpu),
    memory=str(memory),
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.json_dumps([{
        "name": f"{service_name}-api",
        "image": f"{project_name}/{service_name}-api:latest",
        "portMappings": [{
            "containerPort": 8000,
            "protocol": "tcp",
        }],
        "environment": [
            {"name": "ENV", "value": env},
            {"name": "SERVICE_NAME", "value": service_name},
            {"name": "QUEUE_URL", "value": task_queue.url},
            {"name": "BUCKET_NAME", "value": artifact_bucket.bucket},
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": log_group.name,
                "awslogs-region": aws.get_region().name,
                "awslogs-stream-prefix": "api",
            },
        },
        "healthCheck": {
            "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
            "interval": 30,
            "timeout": 5,
            "retries": 3,
            "startPeriod": 60,
        },
    }]),
)

# Create ECS task definition for Worker
worker_task_definition = aws.ecs.TaskDefinition(
    f"{service_name}-worker-task",
    family=f"{project_name}-{env}-{service_name}-worker",
    cpu=str(cpu * 2),  # Workers need more CPU
    memory=str(memory * 2),  # Workers need more memory
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.json_dumps([{
        "name": f"{service_name}-worker",
        "image": f"{project_name}/{service_name}-worker:latest",
        "environment": [
            {"name": "ENV", "value": env},
            {"name": "SERVICE_NAME", "value": service_name},
            {"name": "QUEUE_URL", "value": task_queue.url},
            {"name": "BUCKET_NAME", "value": artifact_bucket.bucket},
            {"name": "WORKER_CONCURRENCY", "value": "4"},
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": log_group.name,
                "awslogs-region": aws.get_region().name,
                "awslogs-stream-prefix": "worker",
            },
        },
    }]),
)

# Create security group for services
security_group = aws.ec2.SecurityGroup(
    f"{service_name}-sg",
    vpc_id=vpc_id,
    description=f"Security group for {service_name} service",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
)

# Create target group for API
target_group = aws.lb.TargetGroup(
    f"{service_name}-api-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc_id,
    target_type="ip",
    health_check={
        "enabled": True,
        "path": "/health",
        "port": "traffic-port",
        "protocol": "HTTP",
        "interval": 30,
        "timeout": 5,
        "healthy_threshold": 2,
        "unhealthy_threshold": 3,
    },
)

# Create ECS service for API
api_service = aws.ecs.Service(
    f"{service_name}-api-service",
    cluster=cluster_arn,
    task_definition=api_task_definition.arn,
    desired_count=desired_count,
    launch_type="FARGATE",
    network_configuration={
        "subnets": subnet_ids,
        "security_groups": [security_group.id],
        "assign_public_ip": True,
    },
    load_balancers=[{
        "target_group_arn": target_group.arn,
        "container_name": f"{service_name}-api",
        "container_port": 8000,
    }],
)

# Create ECS service for Worker
worker_service = aws.ecs.Service(
    f"{service_name}-worker-service",
    cluster=cluster_arn,
    task_definition=worker_task_definition.arn,
    desired_count=desired_count,
    launch_type="FARGATE",
    network_configuration={
        "subnets": subnet_ids,
        "security_groups": [security_group.id],
        "assign_public_ip": True,
    },
)

# Create Auto Scaling for API service
api_scaling_target = aws.appautoscaling.Target(
    f"{service_name}-api-scaling-target",
    service_namespace="ecs",
    resource_id=pulumi.Output.concat("service/", cluster_arn.apply(lambda arn: arn.split("/")[-1]), "/", api_service.name),
    scalable_dimension="ecs:service:DesiredCount",
    min_capacity=1,
    max_capacity=10,
)

# Create CPU-based scaling policy
cpu_scaling_policy = aws.appautoscaling.Policy(
    f"{service_name}-api-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=api_scaling_target.resource_id,
    scalable_dimension=api_scaling_target.scalable_dimension,
    service_namespace=api_scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration={
        "predefined_metric_specification": {
            "predefined_metric_type": "ECSServiceAverageCPUUtilization",
        },
        "target_value": 70.0,
    },
)

# Create Auto Scaling for Worker service based on SQS queue depth
worker_scaling_target = aws.appautoscaling.Target(
    f"{service_name}-worker-scaling-target",
    service_namespace="ecs",
    resource_id=pulumi.Output.concat("service/", cluster_arn.apply(lambda arn: arn.split("/")[-1]), "/", worker_service.name),
    scalable_dimension="ecs:service:DesiredCount",
    min_capacity=1,
    max_capacity=20,
)

# Export outputs
export("api_service_name", api_service.name)
export("worker_service_name", worker_service.name)
export("task_queue_url", task_queue.url)
export("artifact_bucket_name", artifact_bucket.bucket)
export("target_group_arn", target_group.arn)
export("log_group_name", log_group.name)