import pulumi

from .fargate import ApiService

svc = ApiService("auth-api", image=None, env={})
pulumi.export("url", svc.url)
