# Updating Projects from Template

This guide explains how to update existing projects that were created from the Pantstack template.

## Update Methods

### Method 1: Using Cruft (Recommended)

Cruft maintains a link between your project and the template, making updates easier.

#### Initial Setup with Cruft

If you created your project with Cruft:
```bash
# Check current template version
cruft check

# View changes between your project and template
cruft diff

# Update to latest template version
cruft update

# Update to specific version
cruft update --checkout v1.2.3
```

#### Converting Existing Project to Cruft

If you didn't use Cruft initially:
```bash
# Link your project to the template
cruft link https://github.com/MehdiZare/pantstack

# Now you can use cruft update
cruft update
```

### Method 2: Manual Git Integration

For projects created without Cruft, use Git to pull template updates.

#### Setup Template Remote

```bash
# Add template as remote
git remote add template https://github.com/MehdiZare/pantstack.git
git fetch template

# Create update branch
git checkout -b update-from-template

# Merge template changes
git merge template/main --allow-unrelated-histories
```

#### Resolve Conflicts

Common conflict areas:
- `.env` files (keep your values)
- `pants.toml` (merge carefully)
- GitHub workflows (review changes)
- Module-specific code (keep your changes)

### Method 3: Cherry-Pick Updates

For selective updates:
```bash
# Fetch template
git fetch template

# View template commits
git log template/main --oneline

# Cherry-pick specific commits
git cherry-pick <commit-hash>
```

## Update Strategy

### Before Updating

1. **Check Release Notes**
   ```bash
   # View latest releases
   gh release list --repo MehdiZare/pantstack

   # View specific release
   gh release view v1.2.3 --repo MehdiZare/pantstack
   ```

2. **Backup Your Project**
   ```bash
   # Create backup branch
   git checkout -b backup-before-update
   git push origin backup-before-update
   ```

3. **Review Changes**
   ```bash
   # If using Cruft
   cruft diff

   # If using Git
   git diff HEAD template/main
   ```

### During Update

1. **Handle Conflicts Carefully**
   - Keep your business logic
   - Accept infrastructure improvements
   - Merge configuration changes thoughtfully

2. **Update Dependencies**
   ```bash
   # Regenerate lockfiles after update
   make locks

   # Update Pants if needed
   make boot
   ```

3. **Test Thoroughly**
   ```bash
   # Run all tests
   make test

   # Test builds
   make build

   # Test local deployment
   make up
   ```

### After Update

1. **Update Documentation**
   - Review new documentation from template
   - Update your project-specific docs
   - Document any customizations

2. **Verify CI/CD**
   ```bash
   # Create test PR to verify workflows
   git checkout -b test-ci-after-update
   git push origin test-ci-after-update
   gh pr create --title "Test CI after template update"
   ```

## Version Compatibility

### Breaking Changes

Major version updates may include breaking changes:

#### v1.x to v2.x
- Python version changes
- Pants configuration restructuring
- Module organization changes
- Infrastructure pattern updates

#### Migration Guides

Check `MIGRATION.md` in the template repository for specific version migrations:
```bash
# View migration guide
curl https://raw.githubusercontent.com/MehdiZare/pantstack/main/MIGRATION.md
```

### Compatibility Matrix

| Template Version | Python | Pants | Pulumi | AWS Provider |
|-----------------|--------|-------|---------|--------------|
| v1.0.x | 3.11 | 2.16 | 3.x | 5.x |
| v1.1.x | 3.11 | 2.18 | 3.x | 5.x |
| v1.2.x | 3.12 | 2.22 | 3.x | 6.x |
| v2.0.x | 3.12 | 2.28 | 3.x | 6.x |

## Selective Updates

### Update Specific Components

#### GitHub Actions Only
```bash
# Copy workflow files
cp -r template/.github/workflows/* .github/workflows/

# Review and commit
git add .github/workflows
git commit -m "chore: update GitHub Actions from template"
```

#### Infrastructure Patterns
```bash
# Update Pulumi patterns
cp -r template/stack/infra/foundation/* stack/infra/foundation/

# Review changes
git diff stack/infra/foundation
```

#### Build Configuration
```bash
# Update Pants configuration
cp template/pants.toml pants.toml
cp -r template/build-support/* build-support/

# Merge your customizations back
git add -p  # Interactive staging
```

## Handling Customizations

### Preserving Local Changes

1. **Document Customizations**
   ```markdown
   # LOCAL_CUSTOMIZATIONS.md

   ## Modified Files
   - `pants.toml`: Added custom resolve for ML module
   - `.github/workflows/ci.yml`: Added security scanning
   - `Makefile`: Added deployment shortcuts

   ## Why These Changes
   - ML module requires specific TensorFlow version
   - Security compliance requirements
   - Team prefers make commands
   ```

2. **Use Git Attributes**
   ```bash
   # .gitattributes
   # Preserve local versions during merge
   .env merge=ours
   LOCAL_CUSTOMIZATIONS.md merge=ours
   modules/custom-module/** merge=ours
   ```

3. **Create Patches**
   ```bash
   # Save your customizations as patches
   git diff template/main > customizations.patch

   # Apply after update
   git apply customizations.patch
   ```

### Merge Strategies

#### Conservative (Safest)
```bash
# Only take bug fixes and security updates
git cherry-pick <security-fix-commit>
```

#### Balanced (Recommended)
```bash
# Take all updates but preserve your code
cruft update --strategy=ours
```

#### Aggressive (Latest Features)
```bash
# Take all template changes, reapply customizations
cruft update --strategy=theirs
# Then manually reapply your changes
```

## Automation

### Automated Update Checks

Create GitHub Action to check for updates:
```yaml
# .github/workflows/check-template-updates.yml
name: Check Template Updates

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  check-updates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Cruft
        run: pip install cruft

      - name: Check for Updates
        id: check
        run: |
          if cruft check; then
            echo "up_to_date=true" >> $GITHUB_OUTPUT
          else
            echo "up_to_date=false" >> $GITHUB_OUTPUT
          fi

      - name: Create Issue if Outdated
        if: steps.check.outputs.up_to_date == 'false'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Template Update Available',
              body: 'A new version of the Pantstack template is available.',
              labels: ['maintenance', 'template-update']
            })
```

### Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Check for GitHub Action updates
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  # Check for Python updates
  - package-ecosystem: "pip"
    directory: "/3rdparty/python"
    schedule:
      interval: "weekly"
```

## Troubleshooting

### Common Issues

#### Merge Conflicts in Generated Files
```bash
# For lockfiles, regenerate instead of merging
rm lockfiles/*.lock
make locks
```

#### Incompatible Python Version
```bash
# Update Python version in pants.toml
sed -i 's/CPython==3.11/CPython==3.12/' pants.toml

# Update in CI workflows
find .github -name "*.yml" -exec sed -i 's/python-version: 3.11/python-version: 3.12/' {} \;
```

#### Broken CI After Update
```bash
# Revert workflow files
git checkout HEAD~1 -- .github/workflows/

# Apply updates incrementally
git show template/main:.github/workflows/ci.yml > .github/workflows/ci.yml
# Test and fix issues
```

## Best Practices

1. **Update Regularly**: Small, frequent updates are easier than large ones
2. **Test in Branch**: Always update in a feature branch first
3. **Review Carefully**: Understand what changes you're accepting
4. **Keep Notes**: Document why you accepted or rejected changes
5. **Automate Checks**: Use CI to verify updates don't break anything
6. **Communicate**: Inform team about template updates
7. **Contribute Back**: Submit improvements to the template
8. **Version Lock**: Pin to specific template version in production
9. **Staged Rollout**: Update dev environment first, then staging, then production
10. **Backup Always**: Keep backups before major updates
