# Publishing the Template

This guide explains how to publish and maintain Pantstack as a reusable template for other projects.

## Initial Template Setup

### Prerequisites

1. **GitHub CLI Authentication**
   ```bash
   # Install GitHub CLI
   brew install gh  # macOS
   # or visit: https://cli.github.com/

   # Authenticate
   gh auth login

   # Add workflow scope for pushing workflows
   gh auth refresh -s workflow
   ```

2. **Environment Configuration**
   ```bash
   # Copy and configure environment
   cp .env.example .env

   # Edit .env and replace placeholders:
   # GITHUB_OWNER=YourGitHubUsername
   # GITHUB_REPO=your-template-name
   # Leave GITHUB_TOKEN empty to use gh CLI
   ```

## Publishing Process

### First-Time Publishing

```bash
# Initialize and publish template
make init-template
```

This command will:
1. Create/update the GitHub repository
2. Configure repository settings (template flag, topics, description)
3. Push code to both `dev` and `main` branches
4. Set up branch protection rules
5. Mark repository as a GitHub template

### What Gets Published

The template includes:
- Complete monorepo structure
- Pants build configuration
- Pulumi infrastructure templates
- GitHub Actions workflows (configured to skip in template)
- Documentation and examples
- Cookiecutter configuration for variable substitution

## Template Configuration

### Cookiecutter Variables

Variables defined in `cookiecutter.json`:
```json
{
  "project_slug": "pantstack",
  "project_name": "Pantstack",
  "project_description": "Batteries-included monorepo",
  "github_owner": "MehdiZare",
  "github_repo": "{{ cookiecutter.project_slug }}",
  "aws_account_id": "123456789012",
  "aws_region": "us-east-1",
  "pulumi_org": "your-org",
  "python_version": "3.12"
}
```

### Variable Placeholders

Throughout the template, variables use Jinja2 syntax:
```yaml
# Example from .github/workflows/ci.yml
env:
  AWS_ACCOUNT_ID: {{ cookiecutter.aws_account_id }}
  AWS_REGION: {{ cookiecutter.aws_region }}
```

### Files Excluded from Template

Configure in `.cookiecutter-ignore`:
```
.git/
.env
*.pyc
__pycache__/
.coverage
htmlcov/
.pytest_cache/
.pants.d/
dist/
```

## Workflow Configuration

### Template Repository Workflows

Workflows in the template repository are configured to skip execution:
```yaml
# .github/workflows/ci.yml
on:
  push:
    branches: [dev, main]
  pull_request:
    branches: [dev, main]

jobs:
  check-template:
    runs-on: ubuntu-latest
    outputs:
      is_template: ${{ steps.check.outputs.is_template }}
    steps:
      - id: check
        run: |
          # Skip if this is the template repository
          if [[ "${{ github.repository }}" == "MehdiZare/pantstack" ]]; then
            echo "is_template=true" >> $GITHUB_OUTPUT
          else
            echo "is_template=false" >> $GITHUB_OUTPUT
          fi

  ci:
    needs: check-template
    if: needs.check-template.outputs.is_template == 'false'
    # ... rest of workflow
```

### User Repository Activation

When users create projects from the template, workflows automatically activate because the repository name changes.

## Version Management

### Semantic Versioning

The template follows semantic versioning:
- **Major**: Breaking changes to template structure
- **Minor**: New features or modules added
- **Patch**: Bug fixes and minor improvements

### Creating Releases

1. **Development on dev branch**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "feat: add new module template"
   git push origin feature/new-feature
   gh pr create --base dev
   ```

2. **Release to main**
   ```bash
   # Create release PR with version label
   gh pr create \
     --base main \
     --head dev \
     --title "Release v1.2.0" \
     --body "New features and improvements" \
     --label "release:minor"
   ```

3. **Automatic Release Creation**
   On merge to main, GitHub Actions will:
   - Create a new version tag
   - Generate changelog
   - Create GitHub release
   - Update template documentation

## Template Metadata

### Repository Topics

Configure helpful topics for discovery:
```bash
gh repo edit \
  --add-topic "template" \
  --add-topic "monorepo" \
  --add-topic "pants" \
  --add-topic "pulumi" \
  --add-topic "fastapi" \
  --add-topic "aws"
```

### Repository Description

```bash
gh repo edit \
  --description "🚀 Batteries-included monorepo template with Pants, Pulumi, FastAPI, and GitHub Actions"
```

### Template Settings

```bash
# Mark as template
gh api -X PATCH /repos/{owner}/{repo} \
  -f is_template=true

# Configure default branch
gh repo edit --default-branch main
```

## Documentation

### README for Template Users

The main `README.md` should include:
1. Quick start instructions
2. Prerequisites and requirements
3. Both Cookiecutter and GitHub template usage
4. Links to detailed documentation
5. Examples and use cases

### Template-Specific Documentation

Create `TEMPLATE.md` with:
- Template architecture decisions
- Customization points
- Common modifications
- Troubleshooting guide
- Contributing guidelines

## Testing the Template

### Local Testing

1. **Test Cookiecutter Generation**
   ```bash
   # Create test project
   cookiecutter . --output-dir /tmp/test

   # Verify structure
   cd /tmp/test/your-project
   make boot
   make test
   ```

2. **Test GitHub Template**
   ```bash
   # Create from GitHub
   gh repo create test-from-template \
     --template MehdiZare/pantstack \
     --private

   # Clone and test
   gh repo clone test-from-template
   cd test-from-template
   make bootstrap
   ```

### Automated Testing

Create workflow to test template:
```yaml
# .github/workflows/test-template.yml
name: Test Template

on:
  pull_request:
    paths:
      - 'cookiecutter.json'
      - '{{ cookiecutter.project_slug }}/**'

jobs:
  test-generation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Cookiecutter
        run: pip install cookiecutter

      - name: Generate Project
        run: |
          cookiecutter . --no-input \
            project_slug=test-project \
            github_owner=test-owner

      - name: Test Generated Project
        run: |
          cd test-project
          make boot
          make lint
          make test
```

## Distribution Channels

### GitHub Template

Users can create new repositories directly:
1. Visit https://github.com/MehdiZare/pantstack
2. Click "Use this template"
3. Fill in repository details
4. Clone and customize

### Cookiecutter/Cruft

Users can generate projects with variable substitution:
```bash
# Using Cookiecutter
cookiecutter gh:MehdiZare/pantstack

# Using Cruft (with update capability)
cruft create gh:MehdiZare/pantstack

# Specific version
cruft create gh:MehdiZare/pantstack --checkout v1.2.3
```

### Direct Clone

For maximum control:
```bash
git clone https://github.com/MehdiZare/pantstack.git my-project
cd my-project
rm -rf .git
git init
# Customize and commit
```

## Maintenance

### Keeping Template Updated

1. **Monitor Dependencies**
   ```bash
   # Check for outdated dependencies
   pip list --outdated

   # Update requirements files
   pip-compile --upgrade
   ```

2. **Update GitHub Actions**
   ```bash
   # Check for action updates
   gh api /repos/MehdiZare/pantstack/actions/workflows
   ```

3. **Track AWS Best Practices**
   - Monitor AWS service updates
   - Update Pulumi providers
   - Adjust infrastructure patterns

### User Communication

1. **Changelog**: Maintain detailed CHANGELOG.md
2. **Release Notes**: Comprehensive GitHub release descriptions
3. **Migration Guides**: Document breaking changes
4. **Support Channel**: GitHub Discussions or Issues

## Best Practices

1. **Backward Compatibility**: Minimize breaking changes
2. **Clear Documentation**: Explain all template features
3. **Working Examples**: Include sample modules
4. **CI/CD Testing**: Ensure workflows work for users
5. **Version Tags**: Use semantic versioning consistently
6. **Variable Defaults**: Provide sensible defaults
7. **Escape Hatches**: Allow users to customize everything
8. **Security Updates**: Promptly address vulnerabilities
9. **Community Feedback**: Incorporate user suggestions
10. **Template Testing**: Test generation regularly
