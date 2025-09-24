# CI/CD Workflow Consolidation Plan

**Last Updated:** September 23, 2024
**Status:** 🟡 Partially Complete (Architecture improvements done, CI/CD pending)

## Current State
18 workflow files with 2000+ lines of YAML, significant duplication and overlap.

## Problem Analysis

### Duplication Issues
1. **Testing Workflows (3 files)**
   - `ci.yml` - Basic CI pipeline (84 lines)
   - `ci-enhanced.yml` - Enhanced CI with more features (270 lines)
   - `test.yml` - Separate test workflow (280 lines)
   → All three run similar lint/test/build steps

2. **Deployment Workflows (4 files)**
   - `deploy.yml` - Manual deployment (62 lines)
   - `auto-deploy-dev.yml` - Auto-deploy dev branch (145 lines)
   - `auto-deploy-main.yml` - Auto-deploy main branch (123 lines)
   - `deploy-lambda.yml` - Lambda deployment (158 lines)
   → Similar deployment logic repeated

3. **PR Workflows (4 files)**
   - `pr-preview.yml` - PR preview stacks (219 lines)
   - `cleanup-pr-stacks.yml` - Cleanup PR resources (46 lines)
   - `semantic-pr.yml` - PR title validation (63 lines)
   - `enforce-version-label.yml` - Version label check (38 lines)
   → Could be combined into single PR lifecycle workflow

4. **Maintenance Workflows (4 files)**
   - `labels-seed.yml` - Label management (32 lines)
   - `config-check.yml` - Configuration validation (32 lines)
   - `main-branch-protection.yml` - Branch protection (62 lines)
   - `test-template.yml` - Template testing (239 lines)
   → All are maintenance/utility tasks

## Recommended Consolidation

### Target: 6 Core Workflows

#### 1. **ci.yml** - Unified CI Pipeline
Consolidates: ci.yml, ci-enhanced.yml, test.yml

**Key Features:**
```yaml
name: CI
on:
  push: [main, dev]
  pull_request:

jobs:
  lint:
    # All linting checks
  test:
    strategy:
      matrix:
        python: [3.11, 3.12]
        test-type: [unit, integration]
    # Parallel test execution
  build:
    # Build and package
  security:
    # Security scanning
```

**Benefits:**
- Single source of truth for CI
- Matrix strategy for version testing
- Conditional steps based on triggers
- ~400 lines instead of 634

#### 2. **deploy.yml** - Universal Deployment
Consolidates: deploy.yml, auto-deploy-*.yml, deploy-lambda.yml

**Key Features:**
```yaml
name: Deploy
on:
  workflow_dispatch:
    inputs:
      service: # Service to deploy
      environment: # test/staging/prod
      type: # ecs/lambda/both
  push:
    branches: [main, dev]
  workflow_call: # Reusable

jobs:
  deploy:
    # Single parameterized job
    # Auto-detect changed services
    # Support all deployment types
```

**Benefits:**
- One workflow for all deployments
- Reusable from other workflows
- Auto-deployment based on branch
- ~250 lines instead of 488

#### 3. **pr.yml** - PR Lifecycle Management
Consolidates: pr-preview.yml, cleanup-pr-stacks.yml, semantic-pr.yml, enforce-version-label.yml

**Key Features:**
```yaml
name: PR
on:
  pull_request:
  pull_request_target:

jobs:
  validate:
    # Semantic title, version label
  preview:
    # Deploy preview stack
  cleanup:
    if: github.event.action == 'closed'
    # Clean up resources
```

**Benefits:**
- Complete PR lifecycle in one workflow
- Automatic preview and cleanup
- All validations in one place
- ~200 lines instead of 366

#### 4. **release.yml** - Release Management
Based on: template-release.yml

**Key Features:**
```yaml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    # Semantic versioning
    # Changelog generation
    # Multi-registry publishing
    # Production deployment
```

**Benefits:**
- Automated release process
- Version management
- Deployment coordination

#### 5. **maintenance.yml** - Repository Maintenance
Consolidates: labels-seed.yml, config-check.yml, main-branch-protection.yml, test-template.yml

**Key Features:**
```yaml
name: Maintenance
on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  cleanup:
    # Clean old artifacts
  security:
    # Vulnerability scanning
  config:
    # Validate configurations
  labels:
    # Sync labels
```

**Benefits:**
- All maintenance in one place
- Scheduled and manual triggers
- ~150 lines instead of 365

#### 6. **security.yml** - Security Scanning
Keep: codeql.yml (specialized)

**Benefits:**
- Deep code analysis
- Keep separate for security team access

## ✅ Completed Architecture Improvements (September 23, 2024)

Before addressing CI/CD consolidation, the following architectural improvements were completed:

### 1. **Documentation Enhancement**
- ✅ Updated README.md with comprehensive architecture overview
- ✅ Added Architecture Principles and multi-module service pattern explanation
- ✅ Transformed CLAUDE.md into practical developer guide
- ✅ Created detailed project structure documentation

### 2. **Module System Implementation**
- ✅ Created module generator script (`scripts/new_module.sh`)
- ✅ Implemented module discovery system (`shared/core/module_discovery.py`)
- ✅ Added selective module loading for different entry points
- ✅ Created comprehensive module testing framework
- ✅ Added `make new-module S=<service> M=<module>` command

### 3. **Structural Improvements**
- ✅ Standardized on `infrastructure/` directory naming
- ✅ Removed duplicate `platform/` directory
- ✅ Fixed directory structure inconsistencies

### 4. **Testing Framework**
- ✅ Created base test classes for modules (`shared/tests/test_module_base.py`)
- ✅ Added module-specific testing patterns
- ✅ Created example test implementations

## ⏳ Pending: CI/CD Consolidation

## Implementation Strategy

### Phase 1: Preparation (Week 1)
1. Document current workflow dependencies
2. Identify shared components
3. Create test plan for validation
4. Set up feature branch for testing

### Phase 2: Implementation (Week 2)
1. Create reusable workflow components
2. Implement consolidated workflows one by one
3. Test in parallel with existing workflows
4. Validate all scenarios work

### Phase 3: Migration (Week 3)
1. Switch one workflow at a time
2. Monitor for issues
3. Archive old workflows
4. Update documentation

### Phase 4: Cleanup (Week 4)
1. Remove archived workflows
2. Optimize consolidated workflows
3. Create runbooks
4. Train team on new structure

## Expected Benefits

### Quantitative
- **66% reduction** in workflow files (18 → 6)
- **60% reduction** in lines of code (~2000 → ~800)
- **50% faster** CI/CD maintenance
- **30% reduction** in GitHub Actions minutes

### Qualitative
- Easier to understand and maintain
- Less duplication means fewer bugs
- Clearer ownership and responsibility
- Better reusability and modularity
- Improved developer experience

## Risk Mitigation

### Risks
1. **Breaking existing pipelines**
   - Mitigation: Run in parallel first

2. **Missing edge cases**
   - Mitigation: Comprehensive testing

3. **Team resistance**
   - Mitigation: Clear documentation and training

4. **Rollback complexity**
   - Mitigation: Keep archives for 30 days

## Success Metrics

- All deployments work without manual intervention
- No increase in failed workflow runs
- Reduced time to fix workflow issues
- Positive developer feedback
- Decreased GitHub Actions usage costs

## Next Steps

1. **Get approval** for consolidation plan
2. **Create feature branch** for testing
3. **Implement Phase 1** preparation
4. **Begin incremental implementation**

## Alternative Approach

If full consolidation is too risky, consider:
1. Start with just CI workflows (3 → 1)
2. If successful, consolidate deployment workflows
3. Then consolidate PR workflows
4. Finally, maintenance workflows

This incremental approach reduces risk while still achieving benefits.
