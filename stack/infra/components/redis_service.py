import json
from typing import Sequence

import pulumi_aws as aws

import pulumi


class RedisService(pulumi.ComponentResource):
    """Run a minimal Redis server on ECS Fargate behind an internal NLB.

    This is convenient for demos and small projects. For production,
    consider ElastiCache for Redis for durability and HA.
    """

    def __init__(
        self,
        name: str,
        *,
        vpc_id: pulumi.Input[str],
        subnet_ids: Sequence[pulumi.Input[str]] | pulumi.Output[Sequence[str]],
        allow_cidr: pulumi.Input[str] | None = None,
        port: int = 6379,
        cpu: str = "256",
        memory: str = "512",
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("pkg:component:RedisService", name, None, opts)

        # Security group permitting Redis traffic from the specified CIDR (or anywhere if None)
        sg = aws.ec2.SecurityGroup(f"{name}-sg", vpc_id=vpc_id)
        aws.ec2.SecurityGroupRule(
            f"{name}-ingress",
            type="ingress",
            security_group_id=sg.id,
            from_port=port,
            to_port=port,
            protocol="tcp",
            cidr_blocks=[allow_cidr or "0.0.0.0/0"],
        )
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
        log_group = aws.cloudwatch.LogGroup(f"{name}-logs", retention_in_days=7)

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

        # Task definition running Redis
        task_def = aws.ecs.TaskDefinition(
            f"{name}-task",
            family=name,
            requires_compatibilities=["FARGATE"],
            cpu=cpu,
            memory=memory,
            network_mode="awsvpc",
            execution_role_arn=exec_role.arn,
            container_definitions=pulumi.Output.json_dumps(
                [
                    {
                        "name": "redis",
                        "image": "redis:7-alpine",
                        "essential": True,
                        "portMappings": [{"containerPort": port, "protocol": "tcp"}],
                        "logConfiguration": {
                            "logDriver": "awslogs",
                            "options": {
                                "awslogs-group": log_group.name,
                                "awslogs-region": aws.get_region().name,
                                "awslogs-stream-prefix": name,
                            },
                        },
                    }
                ]
            ),
        )

        # Internal Network Load Balancer for stable endpoint
        nlb = aws.lb.LoadBalancer(
            f"{name}-nlb",
            internal=True,
            load_balancer_type="network",
            subnets=subnet_ids,
        )
        tg = aws.lb.TargetGroup(
            f"{name}-tg",
            port=port,
            protocol="TCP",
            target_type="ip",
            vpc_id=vpc_id,
        )
        aws.lb.Listener(
            f"{name}-listener",
            load_balancer_arn=nlb.arn,
            port=port,
            default_actions=[
                aws.lb.ListenerDefaultActionArgs(
                    type="forward", target_group_arn=tg.arn
                )
            ],
        )

        cluster = aws.ecs.Cluster(f"{name}-cluster")
        svc = aws.ecs.Service(
            f"{name}-svc",
            cluster=cluster.arn,
            desired_count=1,
            launch_type="FARGATE",
            task_definition=task_def.arn,
            load_balancers=[
                aws.ecs.ServiceLoadBalancerArgs(
                    container_name="redis", container_port=port, target_group_arn=tg.arn
                )
            ],
            network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
                subnets=subnet_ids,
                assign_public_ip=False,
                security_groups=[sg.id],
            ),
        )

        self.endpoint = nlb.dns_name.apply(lambda h: f"{h}" + ":" + str(port))
        self.nlb_dns = nlb.dns_name
        self.security_group_id = sg.id
        self.cluster_arn = cluster.arn
        self.service_arn = svc.arn

        self.register_outputs(
            {
                "endpoint": self.endpoint,
                "nlb_dns": self.nlb_dns,
                "security_group_id": self.security_group_id,
                "cluster_arn": self.cluster_arn,
                "service_arn": self.service_arn,
            }
        )
