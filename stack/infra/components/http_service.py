import os
from typing import Mapping, Sequence

import pulumi_aws as aws

import pulumi


class EcsHttpService(pulumi.ComponentResource):
    """Minimal ECS Fargate HTTP service behind an ALB.

    Inputs:
      - name: logical name prefix
      - image: container image (ECR URL)
      - port: container port (default 8000)
      - env: dict of environment vars for the container
      - vpc_id, subnet_ids: optional explicit network; if not provided, attempts
        to load from a foundation stack via PULUMI_ORG/PROJECT_SLUG-foundation outputs.

    Outputs:
      - url: public HTTP URL (via ALB DNS)
      - alb_dns: ALB DNS name
      - cluster_arn, service_arn
    """

    def __init__(
        self,
        name: str,
        image: pulumi.Input[str],
        port: int = 8000,
        env: Mapping[str, pulumi.Input[str]] | None = None,
        vpc_id: pulumi.Input[str] | None = None,
        subnet_ids: (
            Sequence[pulumi.Input[str]] | pulumi.Output[Sequence[str]] | None
        ) = None,
        with_sidecar_redis: bool = False,
        additional_containers: list[dict] | None = None,
        task_inline_policy_json: pulumi.Input[str] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("pkg:component:EcsHttpService", name, None, opts)

        project_slug = os.getenv("PROJECT_SLUG", "mono-template")
        org = os.getenv("PULUMI_ORG")
        if vpc_id is None or subnet_ids is None:
            # Try to read from foundation stack if present
            if org:
                stack = (
                    os.getenv("FOUNDATION_STACK") or f"{org}/{project_slug}-foundation"
                )
                ref = pulumi.StackReference(stack)
                vpc_id = vpc_id or ref.get_output("vpc_id")
                subnet_ids = subnet_ids or ref.get_output("public_subnet_ids")

        # If still missing, fail early with a clear message
        if vpc_id is None or subnet_ids is None:
            raise ValueError(
                "EcsHttpService requires VPC context via args or foundation stack outputs"
            )

        # Security groups
        lb_sg = aws.ec2.SecurityGroup(f"{name}-alb-sg", vpc_id=vpc_id)
        aws.ec2.SecurityGroupRule(
            f"{name}-alb-http",
            type="ingress",
            security_group_id=lb_sg.id,
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        )
        aws.ec2.SecurityGroupRule(
            f"{name}-alb-egress",
            type="egress",
            security_group_id=lb_sg.id,
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )

        svc_sg = aws.ec2.SecurityGroup(f"{name}-svc-sg", vpc_id=vpc_id)
        aws.ec2.SecurityGroupRule(
            f"{name}-svc-ingress",
            type="ingress",
            security_group_id=svc_sg.id,
            from_port=port,
            to_port=port,
            protocol="tcp",
            source_security_group_id=lb_sg.id,
        )
        aws.ec2.SecurityGroupRule(
            f"{name}-svc-egress",
            type="egress",
            security_group_id=svc_sg.id,
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )

        # Logs and roles
        log_group = aws.cloudwatch.LogGroup(f"{name}-logs", retention_in_days=14)
        exec_role = aws.iam.Role(
            f"{name}-exec-role",
            assume_role_policy='{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Effect":"Allow"}]}',
        )
        aws.iam.RolePolicyAttachment(
            f"{name}-exec-attach",
            role=exec_role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        )
        task_role = aws.iam.Role(
            f"{name}-task-role",
            assume_role_policy='{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Effect":"Allow"}]}',
        )
        if task_inline_policy_json is not None:
            aws.iam.RolePolicy(
                f"{name}-task-inline",
                role=task_role.id,
                policy=pulumi.Output.secret(task_inline_policy_json),
            )

        # Task definition
        env_list = []
        if env:
            for k, v in env.items():
                env_list.append({"name": k, "value": v})

        containers: list[dict] = [
            {
                "name": name,
                "image": image,
                "essential": True,
                "portMappings": [{"containerPort": port, "protocol": "tcp"}],
                "environment": env_list,
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": log_group.name,
                        "awslogs-region": os.getenv("AWS_REGION", "eu-west-2"),
                        "awslogs-stream-prefix": name,
                    },
                },
            }
        ]

        if with_sidecar_redis:
            containers.append(
                {
                    "name": f"{name}-redis",
                    "image": "redis:7-alpine",
                    "essential": True,
                    "portMappings": [{"containerPort": 6379, "protocol": "tcp"}],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": log_group.name,
                            "awslogs-region": os.getenv("AWS_REGION", "eu-west-2"),
                            "awslogs-stream-prefix": f"{name}-redis",
                        },
                    },
                }
            )

        if additional_containers:
            containers.extend(additional_containers)

        task_def = aws.ecs.TaskDefinition(
            f"{name}-task",
            family=f"{project_slug}-{name}",
            requires_compatibilities=["FARGATE"],
            cpu="256",
            memory="512",
            network_mode="awsvpc",
            execution_role_arn=exec_role.arn,
            task_role_arn=task_role.arn,
            container_definitions=pulumi.Output.secret(
                pulumi.Output.json_dumps(containers)
            ),
        )

        # ALB + target group + listener
        lb = aws.lb.LoadBalancer(
            f"{name}-lb", security_groups=[lb_sg.id], subnets=subnet_ids
        )
        tg = aws.lb.TargetGroup(
            f"{name}-tg",
            port=port,
            protocol="HTTP",
            target_type="ip",
            vpc_id=vpc_id,
            health_check=aws.lb.TargetGroupHealthCheckArgs(path="/healthz"),
        )
        aws.lb.Listener(
            f"{name}-listener",
            load_balancer_arn=lb.arn,
            port=80,
            default_actions=[
                aws.lb.ListenerDefaultActionArgs(
                    type="forward", target_group_arn=tg.arn
                )
            ],
        )

        # Cluster + service
        cluster = aws.ecs.Cluster(f"{name}-cluster")
        service = aws.ecs.Service(
            f"{name}-svc",
            cluster=cluster.arn,
            desired_count=1,
            launch_type="FARGATE",
            task_definition=task_def.arn,
            load_balancers=[
                aws.ecs.ServiceLoadBalancerArgs(
                    container_name=name, container_port=port, target_group_arn=tg.arn
                )
            ],
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                subnets=subnet_ids, assign_public_ip=True, security_groups=[svc_sg.id]
            ),
        )

        self.url = lb.dns_name.apply(lambda h: f"http://{h}")
        self.alb_dns = lb.dns_name
        self.cluster_arn = cluster.arn
        self.service_arn = service.arn

        self.register_outputs(
            {
                "url": self.url,
                "alb_dns": self.alb_dns,
                "cluster_arn": self.cluster_arn,
                "service_arn": self.service_arn,
            }
        )
