import os
import pulumi
import pulumi_aws as aws


PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "")

MODULE = "api"

# Derive image tags from CI env if present
BRANCH = os.getenv("GITHUB_REF_NAME", "dev")
SHORT_SHA = (os.getenv("GITHUB_SHA", "") or "dev")[:7]
ECR_REPO = os.getenv("ECR_REPOSITORY", PROJECT_SLUG)
ECR_BASE = f"{AWS_ACCOUNT_ID}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO}"

image_tag_api = f"{ECR_BASE}:{MODULE}-{BRANCH}-{SHORT_SHA}"
image_tag_worker = f"{ECR_BASE}:{MODULE}-worker-{BRANCH}-{SHORT_SHA}"

provider = aws.Provider("aws", region=AWS_REGION)


# Queues (DLQ + main) for events
dlq = aws.sqs.Queue(
    "api-dlq",
    message_retention_seconds=1209600,
    opts=pulumi.ResourceOptions(provider=provider),
)

queue = aws.sqs.Queue(
    "api-queue",
    redrive_policy=dlq.arn.apply(lambda arn: f'{{"deadLetterTargetArn":"{arn}","maxReceiveCount":5}}'),
    visibility_timeout_seconds=60,
    opts=pulumi.ResourceOptions(provider=provider),
)


# S3 bucket for async status
bucket = aws.s3.Bucket(
    "api-status",
    force_destroy=True,
    opts=pulumi.ResourceOptions(provider=provider),
)
aws.s3.BucketServerSideEncryptionConfigurationV2(
    "api-bucket-sse",
    bucket=bucket.id,
    rules=[
        aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256"
            )
        )
    ],
)
aws.s3.BucketPublicAccessBlock(
    "api-bucket-block",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)
aws.s3.BucketLifecycleConfiguration(
    "api-bucket-lifecycle",
    bucket=bucket.id,
    rules=[
        aws.s3.BucketLifecycleConfigurationRuleArgs(
            id="expire-results",
            status="Enabled",
            filter=aws.s3.BucketLifecycleConfigurationRuleFilterArgs(prefix="results/"),
            expiration=aws.s3.BucketLifecycleConfigurationRuleExpirationArgs(days=14),
        )
    ],
)


# ECS Fargate API service (ALB)
# Create a minimal VPC for the module to avoid relying on a default VPC.
vpc = aws.ec2.Vpc(
    "api-vpc",
    cidr_block="10.99.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
)

igw = aws.ec2.InternetGateway("api-igw", vpc_id=vpc.id)
rt = aws.ec2.RouteTable(
    "api-rt",
    vpc_id=vpc.id,
    routes=[aws.ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0", gateway_id=igw.id)],
)

azs = aws.get_availability_zones()
subnet_ids: list[pulumi.Output[str]] = []
for idx, az in enumerate(azs.names[:2]):
    sn = aws.ec2.Subnet(
        f"api-subnet-{idx}",
        vpc_id=vpc.id,
        cidr_block=f"10.99.{idx}.0/24",
        map_public_ip_on_launch=True,
        availability_zone=az,
    )
    aws.ec2.RouteTableAssociation(f"api-rta-{idx}", route_table_id=rt.id, subnet_id=sn.id)
    subnet_ids.append(sn.id)

log_group_api = aws.cloudwatch.LogGroup("api-logs", retention_in_days=14)

api_task_role = aws.iam.Role(
    "api-task-role",
    assume_role_policy='{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Effect":"Allow"}]}',
)

api_exec_role = aws.iam.Role(
    "api-exec-role",
    assume_role_policy='{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Effect":"Allow"}]}',
)

aws.iam.RolePolicyAttachment(
    "api-exec-attach",
    role=api_exec_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

api_policy_doc = aws.iam.get_policy_document_output(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            actions=["sqs:SendMessage"],
            resources=[queue.arn],
        ),
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            actions=["s3:GetObject"],
            resources=[bucket.arn.apply(lambda a: f"{a}/*")],
        ),
    ]
)
aws.iam.RolePolicy("api-inline", role=api_task_role.id, policy=api_policy_doc.json)

api_task_def = aws.ecs.TaskDefinition(
    "api-task",
    family=f"{PROJECT_SLUG}-api",
    requires_compatibilities=["FARGATE"],
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    execution_role_arn=api_exec_role.arn,
    task_role_arn=api_task_role.arn,
    container_definitions=pulumi.Output.all(image_tag_api, log_group_api.name, queue.url, bucket.bucket, AWS_REGION).apply(
        lambda vals: pulumi.Output.secret(
            f"[{{\"name\":\"api\",\"image\":\"{vals[0]}\",\"essential\":true,\"portMappings\":[{{\"containerPort\":8000,\"protocol\":\"tcp\"}}],\"environment\":[{{\"name\":\"QUEUE_URL\",\"value\":\"{vals[2]}\"}},{{\"name\":\"STATUS_BUCKET\",\"value\":\"{vals[3]}\"}},{{\"name\":\"AWS_REGION\",\"value\":\"{vals[4]}\"}}],\"logConfiguration\":{{\"logDriver\":\"awslogs\",\"options\":{{\"awslogs-group\":\"{vals[1]}\",\"awslogs-region\":\"{AWS_REGION}\",\"awslogs-stream-prefix\":\"api\"}}}}}]"
        )
    ),
)

lb_sg = aws.ec2.SecurityGroup("api-alb-sg", vpc_id=vpc.id)
aws.ec2.SecurityGroupRule("api-alb-http", type="ingress", security_group_id=lb_sg.id, from_port=80, to_port=80, protocol="tcp", cidr_blocks=["0.0.0.0/0"])
aws.ec2.SecurityGroupRule("api-alb-egress", type="egress", security_group_id=lb_sg.id, from_port=0, to_port=0, protocol="-1", cidr_blocks=["0.0.0.0/0"])

svc_sg = aws.ec2.SecurityGroup("api-svc-sg", vpc_id=vpc.id)
aws.ec2.SecurityGroupRule("api-svc-ingress", type="ingress", security_group_id=svc_sg.id, from_port=8000, to_port=8000, protocol="tcp", source_security_group_id=lb_sg.id)
aws.ec2.SecurityGroupRule("api-svc-egress", type="egress", security_group_id=svc_sg.id, from_port=0, to_port=0, protocol="-1", cidr_blocks=["0.0.0.0/0"])

lb = aws.lb.LoadBalancer("api-lb", security_groups=[lb_sg.id], subnets=subnet_ids)
tg = aws.lb.TargetGroup("api-tg", port=8000, protocol="HTTP", target_type="ip", vpc_id=vpc.id, health_check=aws.lb.TargetGroupHealthCheckArgs(path="/healthz"))
lst = aws.lb.Listener("api-listener", load_balancer_arn=lb.arn, port=80, default_actions=[aws.lb.ListenerDefaultActionArgs(type="forward", target_group_arn=tg.arn)])

cluster = aws.ecs.Cluster("api-cluster")

api_svc = aws.ecs.Service(
    "api-svc",
    cluster=cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=api_task_def.arn,
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(container_name="api", container_port=8000, target_group_arn=tg.arn)],
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(subnets=subnet_ids, assign_public_ip=True, security_groups=[svc_sg.id]),
)


# ECS Fargate worker consuming from SQS and writing to S3
log_group = aws.cloudwatch.LogGroup("api-worker-logs", retention_in_days=14)

task_role = aws.iam.Role(
    "api-worker-task-role",
    assume_role_policy='{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Effect":"Allow"}]}',
)

aws.iam.RolePolicyAttachment(
    "api-worker-logs",
    role=task_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

worker_policy_doc = aws.iam.get_policy_document_output(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            actions=["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
            resources=[queue.arn],
        ),
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            actions=["s3:PutObject"],
            resources=[bucket.arn.apply(lambda a: f"{a}/*")],
        ),
    ]
)

aws.iam.RolePolicy("api-worker-inline", role=task_role.id, policy=worker_policy_doc.json)

exec_role = aws.iam.Role(
    "api-worker-exec-role",
    assume_role_policy='{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Effect":"Allow"}]}',
)

aws.iam.RolePolicyAttachment(
    "api-worker-exec-attach",
    role=exec_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

cluster = aws.ecs.Cluster("api-cluster")

task_def = aws.ecs.TaskDefinition(
    "api-worker-task",
    family=f"{PROJECT_SLUG}-api-worker",
    requires_compatibilities=["FARGATE"],
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    execution_role_arn=exec_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.all(image_tag_worker, log_group.name, queue.url, bucket.bucket, AWS_REGION).apply(
        lambda vals: pulumi.Output.secret(
            f"[{{\"name\":\"worker\",\"image\":\"{vals[0]}\",\"essential\":true,\"environment\":[{{\"name\":\"QUEUE_URL\",\"value\":\"{vals[2]}\"}},{{\"name\":\"STATUS_BUCKET\",\"value\":\"{vals[3]}\"}},{{\"name\":\"AWS_REGION\",\"value\":\"{vals[4]}\"}}],\"logConfiguration\":{{\"logDriver\":\"awslogs\",\"options\":{{\"awslogs-group\":\"{vals[1]}\",\"awslogs-region\":\"{AWS_REGION}\",\"awslogs-stream-prefix\":\"worker\"}}}}}]"
        )
    ),
)

sg = aws.ec2.SecurityGroup("api-worker-sg", vpc_id=vpc.id, description="api worker sg")

svc = aws.ecs.Service(
    "api-worker-svc",
    cluster=cluster.arn,
    desired_count=1,
    launch_type="FARGATE",
    task_definition=task_def.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=subnet_ids,
        assign_public_ip=True,
        security_groups=[sg.id],
    ),
)


pulumi.export("api_url", api.api_endpoint)
pulumi.export("alb_dns", lb.dns_name)
pulumi.export("alb_name", lb.name)
pulumi.export("queue_url", queue.url)
pulumi.export("status_bucket", bucket.bucket)
