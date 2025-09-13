import os
import pulumi
import pulumi_aws as aws
import pulumi_github as github


# Inputs from env (surfaced via Pulumi config or .env when running bootstrap)
PROJECT_SLUG = os.getenv("PROJECT_SLUG", "mono-template")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO", PROJECT_SLUG)
GITHUB_VISIBILITY = os.getenv("GITHUB_VISIBILITY", "private")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
PULUMI_ACCESS_TOKEN = os.getenv("PULUMI_ACCESS_TOKEN")


# Configure providers from environment
aws_provider = aws.Provider(
    "aws",
    region=AWS_REGION,
)

# If a PAT is present in env, the GitHub provider picks it up automatically
# via GITHUB_TOKEN. Owner can be set per-resource.
github_provider = github.Provider("github")


# 1) GitHub repository (default branch will be switched to 'dev')
repo = github.Repository(
    "project-repo",
    name=GITHUB_REPO,
    visibility=GITHUB_VISIBILITY,
    description=f"Infrastructure + code for {PROJECT_SLUG}",
    auto_init=True,  # create initial commit on default branch (main)
    has_issues=True,
    has_wiki=False,
    allow_auto_merge=True,
    delete_branch_on_merge=True,
    vulnerability_alerts=True,
    pages=None,
    archive_on_destroy=False,
    # Explicitly associate with owner if provided
    opts=pulumi.ResourceOptions(provider=github_provider),
)

# Create 'dev' branch from the default branch so we can set it as default
dev_branch = github.Branch(
    "dev-branch",
    repository=repo.name,
    branch="dev",
    source_branch="main",
    opts=pulumi.ResourceOptions(provider=github_provider, depends_on=[repo]),
)

default_branch = github.BranchDefault(
    "default-dev",
    repository=repo.name,
    branch=dev_branch.branch,
    opts=pulumi.ResourceOptions(provider=github_provider, depends_on=[dev_branch]),
)


# 2) ECR repository (single per project). Image tags encode module and branch.
ecr_repo = aws.ecr.Repository(
    "project-ecr",
    name=PROJECT_SLUG,
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(scan_on_push=True),
    force_delete=True,
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

ecr_lifecycle = aws.ecr.LifecyclePolicy(
    "ecr-lifecycle",
    repository=ecr_repo.name,
    policy_text=pulumi.Output.secret(
        '{"rules": [{"rulePriority": 1, "description": "Keep last 50 images", "selection": {"tagStatus": "any", "countType": "imageCountMoreThan", "countNumber": 50}, "action": {"type": "expire"}}]}'
    ),
    opts=pulumi.ResourceOptions(provider=aws_provider),
)


# 3) IAM user for CI/CD (GitHub Free; no OIDC). Minimal ECR push/pull policy now.
ci_user = aws.iam.User(
    "ci-user",
    name=f"{PROJECT_SLUG}-ci",
    force_destroy=True,
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

ci_access_key = aws.iam.AccessKey(
    "ci-user-access-key",
    user=ci_user.name,
    opts=pulumi.ResourceOptions(provider=aws_provider),
)

# Broad access for project bootstrap and CI/CD (simplest path)
admin_attach = aws.iam.UserPolicyAttachment(
    "ci-admin-attach",
    user=ci_user.name,
    policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",
    opts=pulumi.ResourceOptions(provider=aws_provider),
)


# 4) Set GitHub secrets and variables on the new repo
def repo_secret(name: str, value: pulumi.Input[str]):
    return github.ActionsSecret(
        f"secret-{name.lower()}",
        repository=repo.name,
        secret_name=name,
        plaintext_value=value,
        opts=pulumi.ResourceOptions(provider=github_provider),
    )


def repo_var(name: str, value: pulumi.Input[str]):
    return github.ActionsVariable(
        f"var-{name.lower()}",
        repository=repo.name,
        variable_name=name,
        value=value,
        opts=pulumi.ResourceOptions(provider=github_provider),
    )


_ = repo_secret("PULUMI_ACCESS_TOKEN", pulumi.Output.secret(PULUMI_ACCESS_TOKEN or ""))
_ = repo_secret("AWS_ACCESS_KEY_ID", pulumi.Output.secret(ci_access_key.id))
_ = repo_secret("AWS_SECRET_ACCESS_KEY", pulumi.Output.secret(ci_access_key.secret))
_ = repo_var("AWS_REGION", AWS_REGION)
_ = repo_var("AWS_ACCOUNT_ID", AWS_ACCOUNT_ID or "")
_ = repo_var("PROJECT_SLUG", PROJECT_SLUG)
_ = repo_var("ECR_REPOSITORY", ecr_repo.name)
_ = repo_var("PULUMI_ORG", os.getenv("PULUMI_ORG", ""))


# Useful outputs
pulumi.export("github_repo", repo.full_name)
pulumi.export("github_default_branch", default_branch.branch)
pulumi.export("ecr_repository_url", ecr_repo.repository_url)
pulumi.export("ci_user_arn", ci_user.arn)
