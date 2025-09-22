# Technical Debt - Code Quality Issues

## Overview
During the pre-commit integration, we discovered several code quality issues. Most critical issues have been fixed, but some remain and are temporarily suppressed in `.flake8`.

## ✅ Issues Fixed

### 1. YAML Syntax Errors in GitHub Workflows
- **Fixed**: `.github/workflows/test-template.yml` - Converted multiline Python to single line
- **No actual errors found in**: `ci-enhanced.yml` and `test.yml`

### 2. Critical Flake8 Violations Fixed
- **F821** (2): Fixed undefined names - Added missing imports
- **F541** (5): Fixed f-string placeholders - Removed unnecessary 'f' prefixes
- **E203** (2): Fixed whitespace issues - Removed spaces before colons
- **E722** (7): Fixed bare except clauses - Added specific exception types
- **E713** (1): Fixed membership test - Changed to proper syntax

## ⚠️ Remaining Issues

### Flake8 Violations (~60 remaining)

#### Unused Imports (F401) - ~30 remaining
- Mostly in test files where imports may be used by fixtures
- Files: `cli/tests/*.py`, `services/auth/lib/**/*.py`, `entry_points/**/*.py`
- **Priority**: LOW - Not critical for functionality

#### Unused Variables (F841) - ~25 remaining
- Common in test files where variables are created for side effects
- Often legitimate in test setup/teardown
- **Priority**: LOW - May be intentional in tests

## Temporary Exclusions Remaining

### .flake8
```ini
per-file-ignores =
    # Test files with unused imports/variables
    cli/tests/*.py: F401,F841
    tests/**/*.py: F401,F841
    scripts/tests/*.py: F401,F841
    shared/tests/*.py: F401,F841
    # Service files with remaining unused imports
    services/auth/lib/**/*.py: F401
    services/auth/tests/**/*.py: F401
    entry_points/**/*.py: F401,F841
    shared/core/*.py: F401,F841
    stack/infra/**/*.py: F401
```

### .pre-commit-config.yaml
✅ All YAML checking re-enabled

## Action Items

1. ✅ **YAML workflows** - COMPLETED
   - Fixed multiline Python strings in test-template.yml
   - All workflows now pass YAML validation

2. ✅ **Critical code issues** - COMPLETED
   - Fixed all undefined names (F821)
   - Fixed all f-string placeholders (F541)
   - Fixed all whitespace issues (E203)
   - Fixed all bare except clauses (E722)

3. **Clean up test imports** (Priority: LOW)
   - Review unused imports in test files
   - Some may be legitimate (fixtures, side effects)
   - Use `autoflake` cautiously on test files

4. **Remove remaining exclusions** (Priority: LOW)
   - Gradually clean up F401 and F841 violations
   - Focus on non-test files first

## Commands to Help Fix

```bash
# Find all unused imports
flake8 . --select=F401

# Auto-remove unused imports (use carefully)
autoflake --in-place --remove-unused-variables --remove-all-unused-imports <file>

# Find bare excepts
grep -r "except:" --include="*.py"

# Check YAML syntax
python -m yaml < .github/workflows/test.yml
```

## References
- [Flake8 Error Codes](https://flake8.pycqa.org/en/latest/user/error-codes.html)
- [Pre-commit Hooks](https://pre-commit.com/hooks.html)
