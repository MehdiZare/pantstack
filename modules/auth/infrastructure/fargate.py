import pulumi


class ApiService(pulumi.ComponentResource):
    """ECS Fargate API + ALB placeholder component.

    Example:
        >>> # instantiate in __main__.py with base stack refs
    """

    def __init__(self, name: str, image: str | None = None, env: dict[str, str] | None = None, opts=None):
        super().__init__("pkg:svc:ApiService", name, None, opts)
        # Placeholder: in real impl, create SG, ALB, TG, Listener, Cluster, TaskDef, Service
        self.url = pulumi.Output.from_input("https://example.invalid/")
        self.register_outputs({"url": self.url})

