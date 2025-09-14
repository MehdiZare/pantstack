# Infrastructure Architecture

Pantstack uses Pulumi for Infrastructure as Code, deploying to AWS with a modular, scalable architecture.

## Infrastructure Layers

### Foundation Layer
Located in `stack/infra/foundation/`, provides shared resources:
- ECR repository for all service images
- GitHub OIDC provider for secure CI/CD
- CI/CD IAM roles and policies
- Optional shared networking components

### Service Infrastructure
Each service has its own infrastructure in `modules/{service}/infrastructure/`:
- ECS Fargate services
- Application Load Balancers
- SQS queues for async processing
- S3 buckets for storage
- Service-specific IAM roles

## AWS Services Architecture

### Container Orchestration
```
┌─────────────────────────────────────┐
│         Application Load             │
│            Balancer                  │
└──────────────┬──────────────────────┘
               │
       ┌───────▼──────────┐
       │   Target Group   │
       └───────┬──────────┘
               │
       ┌───────▼──────────┐
       │  ECS Service     │
       │  (Fargate)       │
       └───────┬──────────┘
               │
       ┌───────▼──────────┐
       │  Task Definition │
       │  (Docker Image)  │
       └──────────────────┘
```

### Typical Service Stack
- **ALB**: Public-facing load balancer
- **ECS Cluster**: Container orchestration
- **Fargate Service**: Serverless container execution
- **SQS Queues**: Async message processing
- **S3 Buckets**: Object storage
- **CloudWatch**: Logs and metrics
- **IAM Roles**: Fine-grained permissions

## Pulumi Configuration

### Project Structure
```yaml
# Pulumi.yaml
name: pantstack-api
runtime: python
description: API service infrastructure
```

### Stack Configuration
```yaml
# Pulumi.test.yaml
config:
  aws:region: us-east-1
  pantstack:environment: test
  pantstack:minCapacity: 1
  pantstack:maxCapacity: 3
```

### Environment Strategy
- **test**: Development environment (from dev branch)
- **prod**: Production environment (from main branch)
- **preview-{pr}**: PR preview stacks (auto-created)

## Deployment Patterns

### Blue-Green Deployments
ECS services use rolling updates with:
- Health checks for zero-downtime
- Automatic rollback on failures
- Connection draining for graceful shutdown

### Auto-Scaling
```python
# Fargate auto-scaling configuration
scaling_target = appautoscaling.Target(
    "scaling-target",
    service_namespace="ecs",
    resource_id=f"service/{cluster_name}/{service_name}",
    scalable_dimension="ecs:service:DesiredCount",
    min_capacity=1,
    max_capacity=10,
)

scaling_policy = appautoscaling.Policy(
    "scaling-policy",
    policy_type="TargetTrackingScaling",
    resource_id=scaling_target.resource_id,
    target_tracking_scaling_policy_configuration={
        "targetValue": 70.0,
        "predefinedMetricSpecification": {
            "predefinedMetricType": "ECSServiceAverageCPUUtilization",
        },
    },
)
```

## Security Architecture

### Network Security
- Private subnets for compute resources
- Public subnets only for load balancers
- Security groups with least privilege
- VPC flow logs for audit

### IAM Security
- Service-specific IAM roles
- Task execution roles for ECS
- Cross-service permissions via resource policies
- GitHub OIDC for CI/CD (no long-lived credentials)

### Secrets Management
- AWS Systems Manager Parameter Store
- Encrypted at rest with KMS
- Rotation policies for sensitive data
- Environment-specific secrets

## Image Management

### ECR Repository Structure
Single repository with tagged images:
```
pantstack/
├── api-dev-abc123       # Dev branch build
├── api-v1.2.3          # Release version
├── api-main-def456     # Main branch build
├── admin-dev-ghi789    # Another service
└── worker-api-dev-jkl  # Worker variant
```

### Image Tagging Strategy
- `{service}-{branch}-{sha}`: Branch builds
- `{service}-v{version}`: Release versions
- `{service}-worker-{branch}-{sha}`: Worker images

## Cost Optimization

### Fargate Spot
Use Spot instances for non-critical workloads:
```python
capacity_providers=["FARGATE_SPOT", "FARGATE"],
default_capacity_provider_strategy=[
    {"capacityProvider": "FARGATE_SPOT", "weight": 4},
    {"capacityProvider": "FARGATE", "weight": 1},
],
```

### Resource Right-Sizing
- Start with minimal resources
- Monitor CloudWatch metrics
- Adjust based on actual usage
- Use auto-scaling for variable loads

## Monitoring & Observability

### CloudWatch Integration
- Container logs automatically shipped
- Custom metrics for business KPIs
- Alarms for critical thresholds
- Dashboards for service health

### Distributed Tracing
- AWS X-Ray for request tracing
- Service mesh with App Mesh (optional)
- Correlation IDs across services

## Disaster Recovery

### Backup Strategy
- S3 versioning for object storage
- RDS automated backups (if used)
- Cross-region replication for critical data
- Infrastructure as code for quick rebuild

### Recovery Procedures
1. **Service Failure**: ECS auto-restarts failed tasks
2. **AZ Failure**: Multi-AZ deployment handles automatically
3. **Region Failure**: Deploy to alternate region using Pulumi
4. **Data Loss**: Restore from S3 versioning or backups
