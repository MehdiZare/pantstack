import json
import os
from typing import Mapping, Sequence

import pulumi_aws as aws

import pulumi


class EcsWorkerService(pulumi.ComponentResource):
    """Minimal ECS Fargate worker service.

    Creates a Fargate service running a single container with environment variables.
    Networking expects a VPC/subnets (public is fine for simple demos).
    """

    def __init__(
        self,
        name: str,
        image: pulumi.Input[str],
        env: Mapping[str, pulumi.Input[str]] | None = None,
        vpc_id: pulumi.Input[str] | None = None,
        subnet_ids: (
            Sequence[pulumi.Input[str]] | pulumi.Output[Sequence[str]] | None
        ) = None,
        with_sidecar_redis: bool = False,
        additional_containers: list[dict] | None = None,
        command: list[str] | None = None,
        task_inline_policy_json: pulumi.Input[str] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__("pkg:component:EcsWorkerService", name, None, opts)

        project_slug = os.getenv("PROJECT_SLUG", "mono-template")
        org = os.getenv("PULUMI_ORG")
        if vpc_id is None or subnet_ids is None:
            if org:
                stack = (
                    os.getenv("FOUNDATION_STACK") or f"{org}/{project_slug}-foundation"
                )
                ref = pulumi.StackReference(stack)
                vpc_id = vpc_id or ref.get_output("vpc_id")
                subnet_ids = subnet_ids or ref.get_output("public_subnet_ids")

        if vpc_id is None or subnet_ids is None:
            raise ValueError(
                "EcsWorkerService requires VPC context via args or foundation stack outputs"
            )

        # Security group (egress only)
        sg = aws.ec2.SecurityGroup(f"{name}-sg", vpc_id=vpc_id)
        aws.ec2.SecurityGroupRule(
            f"{name}-egress",
            type="egress",
            security_group_id=sg.id,
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )

        # Logs and roles
        log_group = aws.cloudwatch.LogGroup(f"{name}-logs", retention_in_days=14)

        def _assume_role_policy_json() -> str:
            return json.dumps(
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
            )

        exec_role = aws.iam.Role(
            f"{name}-exec-role",
            assume_role_policy=_assume_role_policy_json(),
        )
        aws.iam.RolePolicyAttachment(
            f"{name}-exec-attach",
            role=exec_role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        )
        task_role = aws.iam.Role(
            f"{name}-task-role",
            assume_role_policy=_assume_role_policy_json(),
        )
        if task_inline_policy_json is not None:
            aws.iam.RolePolicy(
                f"{name}-task-inline",
                role=task_role.id,
                policy=pulumi.Output.secret(task_inline_policy_json),
            )

        env_list = []
        if env:
            for k, v in env.items():
                env_list.append({"name": k, "value": v})

        containers: list[dict] = [
            {
                "name": name,
                "image": image,
                "essential": True,
                "environment": env_list,
                **({"command": command} if command else {}),
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

        cluster = aws.ecs.Cluster(f"{name}-cluster")
        service = aws.ecs.Service(
            f"{name}-svc",
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

        self.cluster_arn = cluster.arn
        self.service_arn = service.arn
        self.register_outputs(
            {"cluster_arn": self.cluster_arn, "service_arn": self.service_arn}
        )
