"""Pulumi infrastructure for Auth service.

Deploys:
- ECS Fargate service for API
- Lambda functions for async processing
- DynamoDB tables for user data
- Secrets in Parameter Store
"""

import json
import os

import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
env = pulumi.get_stack()
project_name = pulumi.get_project()
service_name = "auth"

# Get foundation stack outputs
foundation_stack = pulumi.StackReference(
    config.require("foundation_stack"),
    pulumi.StackReference
)
vpc_id = foundation_stack.require_output("vpc_id")
subnet_ids = foundation_stack.require_output("public_subnet_ids")
ecr_url = foundation_stack.require_output("ecr_repository_url")
redis_endpoint = foundation_stack.require_output("redis_endpoint")
event_bus_arn = foundation_stack.require_output("event_bus_arn")
main_queue_url = foundation_stack.require_output("main_queue_url")

# Tagging
tags = {
    "Project": project_name,
    "Service": service_name,
    "Environment": env,
    "ManagedBy": "Pulumi"
}

# DynamoDB tables
users_table = aws.dynamodb.Table(
    "users-table",
    name=f"{service_name}-users-{env}",
    billing_mode="PAY_PER_REQUEST",
    hash_key="userId",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="userId", type="S"),
        aws.dynamodb.TableAttributeArgs(name="email", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="EmailIndex",
            hash_key="email",
            projection_type="ALL"
        )
    ],
    stream_enabled=True,
    stream_view_type="NEW_AND_OLD_IMAGES",
    tags=tags
)

sessions_table = aws.dynamodb.Table(
    "sessions-table",
    name=f"{service_name}-sessions-{env}",
    billing_mode="PAY_PER_REQUEST",
    hash_key="sessionId",
    attributes=[
        aws.dynamodb.TableAttributeArgs(name="sessionId", type="S"),
        aws.dynamodb.TableAttributeArgs(name="userId", type="S"),
    ],
    global_secondary_indexes=[
        aws.dynamodb.TableGlobalSecondaryIndexArgs(
            name="UserIdIndex",
            hash_key="userId",
            projection_type="KEYS_ONLY"
        )
    ],
    ttl=aws.dynamodb.TableTtlArgs(
        attribute_name="ttl",
        enabled=True
    ),
    tags=tags
)

# Secrets in Parameter Store
jwt_secret = aws.ssm.Parameter(
    "jwt-secret",
    name=f"/{service_name}/{env}/jwt-secret",
    type="SecureString",
    value=config.get_secret("jwt_secret") or pulumi.Output.secret("change-me-in-production"),
    tags=tags
)

supabase_url = aws.ssm.Parameter(
    "supabase-url",
    name=f"/{service_name}/{env}/supabase-url",
    type="String",
    value=config.get("supabase_url") or "http://localhost:54321",
    tags=tags
)

supabase_key = aws.ssm.Parameter(
    "supabase-key",
    name=f"/{service_name}/{env}/supabase-anon-key",
    type="SecureString",
    value=config.get_secret("supabase_anon_key") or pulumi.Output.secret("development-key"),
    tags=tags
)

# IAM role for Lambda functions
lambda_role = aws.iam.Role(
    f"{service_name}-lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Effect": "Allow"
        }]
    }),
    tags=tags
)

# Lambda policy
lambda_policy = aws.iam.Policy(
    f"{service_name}-lambda-policy",
    policy=pulumi.Output.all(
        users_table.arn,
        sessions_table.arn,
        jwt_secret.arn,
        main_queue_url,
        event_bus_arn
    ).apply(lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [args[0], args[1], f"{args[0]}/index/*", f"{args[1]}/index/*"]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters"
                ],
                "Resource": args[2]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:SendMessage",
                    "sqs:GetQueueAttributes"
                ],
                "Resource": "*"  # Queue ARN would be better
            },
            {
                "Effect": "Allow",
                "Action": [
                    "events:PutEvents"
                ],
                "Resource": args[4]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ses:SendEmail",
                    "ses:SendRawEmail"
                ],
                "Resource": "*"
            }
        ]
    }))
)

aws.iam.RolePolicyAttachment(
    f"{service_name}-lambda-attachment",
    role=lambda_role.name,
    policy_arn=lambda_policy.arn
)

# Lambda functions
verify_token_lambda = aws.lambda_.Function(
    "verify-token",
    name=f"{service_name}-verify-token-{env}",
    runtime="python3.11",
    role=lambda_role.arn,
    handler="services.auth.src.lambdas.verify_token:handler",
    code=pulumi.FileArchive("../../dist/auth_verify_token.zip"),  # Built by Pants
    timeout=10,
    memory_size=256,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "JWT_SECRET_PARAM": jwt_secret.name,
            "ENVIRONMENT": env
        }
    ),
    tags=tags
)

process_signup_lambda = aws.lambda_.Function(
    "process-signup",
    name=f"{service_name}-process-signup-{env}",
    runtime="python3.11",
    role=lambda_role.arn,
    handler="services.auth.src.lambdas.process_signup:handler",
    code=pulumi.FileArchive("../../dist/auth_process_signup.zip"),
    timeout=30,
    memory_size=512,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "USERS_TABLE": users_table.name,
            "ENVIRONMENT": env,
            "FROM_EMAIL": config.get("from_email") or "noreply@example.com"
        }
    ),
    tags=tags
)

token_refresh_lambda = aws.lambda_.Function(
    "token-refresh",
    name=f"{service_name}-token-refresh-{env}",
    runtime="python3.11",
    role=lambda_role.arn,
    handler="services.auth.src.lambdas.token_refresh:handler",
    code=pulumi.FileArchive("../../dist/auth_token_refresh.zip"),
    timeout=10,
    memory_size=256,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "JWT_SECRET_PARAM": jwt_secret.name,
            "JWT_REFRESH_SECRET_PARAM": jwt_secret.name,  # Could be separate
            "ROTATE_REFRESH_TOKENS": "true" if env == "prod" else "false",
            "ENVIRONMENT": env
        }
    ),
    tags=tags
)

# SQS trigger for process_signup Lambda
sqs_trigger = aws.lambda_.EventSourceMapping(
    "signup-sqs-trigger",
    event_source_arn=main_queue_url,
    function_name=process_signup_lambda.name,
    batch_size=10,
    maximum_batching_window_in_seconds=5
)

# EventBridge rule for user events
user_event_rule = aws.cloudwatch.EventRule(
    "user-events-rule",
    name=f"{service_name}-user-events-{env}",
    event_bus_name=event_bus_arn.apply(lambda arn: arn.split("/")[-1]),
    event_pattern=json.dumps({
        "source": [f"{service_name}.service"],
        "detail-type": ["User Registered", "User Updated", "User Deleted"]
    }),
    tags=tags
)

aws.cloudwatch.EventTarget(
    "user-events-target",
    rule=user_event_rule.name,
    arn=process_signup_lambda.arn,
    event_bus_name=event_bus_arn.apply(lambda arn: arn.split("/")[-1])
)

# Lambda permission for EventBridge
aws.lambda_.Permission(
    "eventbridge-invoke-permission",
    statement_id="AllowExecutionFromEventBridge",
    action="lambda:InvokeFunction",
    function=process_signup_lambda.name,
    principal="events.amazonaws.com",
    source_arn=user_event_rule.arn
)

# ECS Task Definition for API
task_role = aws.iam.Role(
    f"{service_name}-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Effect": "Allow"
        }]
    }),
    tags=tags
)

task_execution_role = aws.iam.Role(
    f"{service_name}-execution-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Effect": "Allow"
        }]
    }),
    tags=tags
)

aws.iam.RolePolicyAttachment(
    f"{service_name}-execution-policy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)

# Task policy for DynamoDB and other services
task_policy = aws.iam.Policy(
    f"{service_name}-task-policy",
    policy=pulumi.Output.all(
        users_table.arn,
        sessions_table.arn,
        jwt_secret.arn,
        supabase_url.arn,
        supabase_key.arn,
        event_bus_arn
    ).apply(lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:*"
                ],
                "Resource": [args[0], args[1], f"{args[0]}/index/*", f"{args[1]}/index/*"]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters"
                ],
                "Resource": [args[2], args[3], args[4]]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "events:PutEvents"
                ],
                "Resource": args[5]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:*"
                ],
                "Resource": "*"
            }
        ]
    }))
)

aws.iam.RolePolicyAttachment(
    f"{service_name}-task-attachment",
    role=task_role.name,
    policy_arn=task_policy.arn
)

# CloudWatch Log Group
log_group = aws.cloudwatch.LogGroup(
    f"{service_name}-logs",
    name=f"/ecs/{service_name}-{env}",
    retention_in_days=7,
    tags=tags
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    f"{service_name}-cluster",
    name=f"{service_name}-{env}",
    tags=tags
)

# Security Group for ECS Service
ecs_security_group = aws.ec2.SecurityGroup(
    f"{service_name}-sg",
    vpc_id=vpc_id,
    description=f"Security group for {service_name} ECS service",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            from_port=8000,
            to_port=8000,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"]  # Restrict in production
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"]
        )
    ],
    tags=tags
)

# Task Definition
task_definition = aws.ecs.TaskDefinition(
    f"{service_name}-task",
    family=f"{service_name}-{env}",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(
        ecr_url,
        jwt_secret.arn,
        supabase_url.arn,
        supabase_key.arn,
        redis_endpoint,
        log_group.name
    ).apply(lambda args: json.dumps([{
        "name": service_name,
        "image": f"{args[0]}:{service_name}-{env}-latest",
        "cpu": 256,
        "memory": 512,
        "essential": True,
        "portMappings": [{
            "containerPort": 8000,
            "protocol": "tcp"
        }],
        "environment": [
            {"name": "SERVICE_NAME", "value": service_name},
            {"name": "ENVIRONMENT", "value": env},
            {"name": "REDIS_HOST", "value": args[4]},
            {"name": "REDIS_PORT", "value": "6379"},
            {"name": "CELERY_BROKER_URL", "value": f"redis://{args[4]}:6379/0"},
            {"name": "PORT", "value": "8000"},
            {"name": "USERS_TABLE", "value": users_table.name},
            {"name": "SESSIONS_TABLE", "value": sessions_table.name},
        ],
        "secrets": [
            {"name": "JWT_SECRET", "valueFrom": args[1]},
            {"name": "DB_SUPABASE_URL", "valueFrom": args[2]},
            {"name": "DB_SUPABASE_ANON_KEY", "valueFrom": args[3]}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": args[5],
                "awslogs-region": aws.get_region().name,
                "awslogs-stream-prefix": "ecs"
            }
        }
    }])),
    tags=tags
)

# Application Load Balancer
alb = aws.lb.LoadBalancer(
    f"{service_name}-alb",
    name=f"{service_name}-{env}",
    internal=False,
    load_balancer_type="application",
    security_groups=[ecs_security_group.id],
    subnets=subnet_ids,
    tags=tags
)

target_group = aws.lb.TargetGroup(
    f"{service_name}-tg",
    name=f"{service_name}-{env}",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc_id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        healthy_threshold=2,
        interval=30,
        matcher="200-299",
        path="/health",
        port="8000",
        protocol="HTTP",
        timeout=5,
        unhealthy_threshold=3
    ),
    tags=tags
)

listener = aws.lb.Listener(
    f"{service_name}-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=target_group.arn
    )]
)

# ECS Service
ecs_service = aws.ecs.Service(
    f"{service_name}-service",
    name=f"{service_name}-{env}",
    cluster=ecs_cluster.id,
    task_definition=task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=subnet_ids,
        security_groups=[ecs_security_group.id],
        assign_public_ip=True
    ),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        target_group_arn=target_group.arn,
        container_name=service_name,
        container_port=8000
    )],
    depends_on=[listener],
    tags=tags
)

# Outputs
pulumi.export("service_url", alb.dns_name)
pulumi.export("users_table", users_table.name)
pulumi.export("sessions_table", sessions_table.name)
pulumi.export("verify_token_lambda", verify_token_lambda.name)
pulumi.export("process_signup_lambda", process_signup_lambda.name)
pulumi.export("token_refresh_lambda", token_refresh_lambda.name)
pulumi.export("ecs_cluster", ecs_cluster.name)
pulumi.export("ecs_service", ecs_service.name)