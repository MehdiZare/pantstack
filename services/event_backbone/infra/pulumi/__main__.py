import pulumi_aws as aws

import pulumi

project = pulumi.get_project()

bus = aws.cloudwatch.EventBus("events-bus", name=f"{project}-bus")
dlq = aws.sqs.Queue("events-dlq", message_retention_seconds=1209600)

pulumi.export("bus_arn", bus.arn)
pulumi.export("bus_name", bus.name)
pulumi.export("dlq_url", dlq.url)
