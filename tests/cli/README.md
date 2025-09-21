# CLI Testing Guide

## Overview

This directory contains comprehensive testing infrastructure for CLI commands with automatic cleanup mechanisms to ensure no side effects remain after test execution.

## Key Features

✅ **Automatic Resource Tracking** - All created resources are tracked for cleanup
✅ **Multi-layer Cleanup** - Fixture, test, session, and emergency cleanup levels
✅ **Resource Isolation** - Tests run in isolated environments
✅ **Cleanup Verification** - Automatic verification that no artifacts remain
✅ **Safe Test Commands** - Pre-configured commands with guaranteed cleanup

## Test Infrastructure

### Core Components

1. **`conftest.py`** - Pytest configuration with shared fixtures
   - Resource tracker with automatic cleanup
   - Isolated project fixture for safe testing
   - Enhanced CLI runner with resource tracking
   - Cleanup verification after each test

2. **`cleanup.py`** - Cleanup utilities
   - `TestCleanupManager` - Comprehensive cleanup manager
   - Resource discovery functions
   - Emergency cleanup capabilities
   - Cleanup verification

3. **`verify_cleanup.sh`** - Bash script for cleanup verification
   - Checks for test services, containers, stacks
   - Reports any remaining artifacts
   - Exit code indicates cleanup status

## Running Tests Safely

### Recommended Commands

Always use these cleanup-enabled commands:

```bash
# Run tests with automatic cleanup
make test-cli-safe

# Run tests with cleanup verification
make test-cli-verify

# Check for test artifacts
make check-test-artifacts

# Clean test artifacts
make clean-test-artifacts

# Emergency cleanup (if needed)
make clean-all-test-artifacts
```

### Manual Test Execution

If running tests manually with pytest:

```bash
# Run all CLI tests
pytest tests/cli

# Run specific test file
pytest tests/cli/test_service_commands.py

# Run non-destructive tests only
pytest tests/cli -m "not destructive"

# Run with verbose output
pytest tests/cli -v

# Always clean up after manual runs
make clean-test-artifacts
```

## Writing New Tests

### Test Structure

```python
import pytest
from pathlib import Path

class TestMyCommands:
    """Test suite for my commands."""

    def test_safe_command(self):
        """Test that doesn't create resources."""
        # No cleanup needed for read-only operations
        assert True

    def test_with_service_creation(self, project_root, resource_tracker):
        """Test that creates a service."""
        # Service will be automatically cleaned up
        service_name = "test_myservice_12345"
        resource_tracker.track_service(service_name)

        # Create service
        # ... test logic ...

        # Cleanup happens automatically

    @pytest.mark.destructive
    def test_destructive_operation(self, isolated_project):
        """Test that modifies the system."""
        # Use isolated project for safety
        # ... test logic ...
        # Isolated project is destroyed after test
```

### Using Fixtures

#### Resource Tracker
```python
def test_with_tracking(resource_tracker):
    """Test with resource tracking."""
    # Track any created resources
    resource_tracker.track_service("test_service")
    resource_tracker.track_container("test_container")
    resource_tracker.track_stack("test_stack", "dev")

    # Resources are automatically cleaned up
```

#### Isolated Project
```python
def test_in_isolation(isolated_project):
    """Test in isolated project copy."""
    # isolated_project is a temporary copy
    service_path = isolated_project / "services" / "test"
    service_path.mkdir(parents=True)

    # Entire isolated project is deleted after test
```

#### Test Service Context Manager
```python
def test_service_lifecycle(project_root, resource_tracker):
    """Test with service context manager."""
    from tests.cli.conftest import test_service

    with test_service(project_root, resource_tracker, "mytest") as (name, path):
        # Service exists here
        assert path.exists()
        # ... test logic ...

    # Service is cleaned up after context exits
```

## Resource Naming Conventions

All test resources **MUST** use these prefixes to enable pattern-based cleanup:

- **Services**: `test_<name>_<timestamp>` or `temp_<name>_<uuid>`
- **Containers**: `test-<name>-<uuid>` or `temp-<name>-<id>`
- **Stacks**: `test-<name>-<env>` or `temp-<name>-<env>`
- **Temp Files**: `tmp_test_<name>_<pid>`

Examples:
```
test_auth_1234567890
temp_service_abc123
test-api-container-xyz789
test-stack-dev
tmp_test_config_12345
```

## Test Categories

### Markers

Tests are categorized with pytest markers:

```python
@pytest.mark.safe           # No side effects
@pytest.mark.destructive    # Modifies the system
@pytest.mark.requires_docker # Needs Docker
@pytest.mark.requires_pants  # Needs Pants build system
@pytest.mark.no_cleanup_check # Skip cleanup verification
```

### Test Types

1. **Unit Tests** - No side effects
   - Test command parsing
   - Test utility functions
   - No cleanup needed

2. **Integration Tests** - Local side effects
   - Create test services
   - Modify local files
   - Automatic cleanup via fixtures

3. **System Tests** - External dependencies
   - Docker operations
   - Pulumi stacks
   - Network operations
   - Comprehensive cleanup required

## Cleanup Mechanisms

### 1. Fixture-Level Cleanup

```python
@pytest.fixture
def my_resource():
    resource = create_resource()
    yield resource
    cleanup_resource(resource)  # Always runs
```

### 2. Test-Level Cleanup

```python
def test_something():
    try:
        resource = create_resource()
        # Test logic
    finally:
        cleanup_resource(resource)  # Always runs
```

### 3. Session-Level Cleanup

The `resource_tracker` fixture automatically cleans up all tracked resources at the end of the test session.

### 4. Emergency Cleanup

If tests fail catastrophically:

```bash
# Emergency cleanup command
make clean-all-test-artifacts

# Or run the Python cleanup
python -c "
from tests.cli.cleanup import TestCleanupManager
from pathlib import Path
manager = TestCleanupManager(Path('.'))
manager.emergency_cleanup()
"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run CLI tests
  run: |
    make test-cli-safe

- name: Verify cleanup
  if: always()
  run: |
    make check-test-artifacts || (
      echo "Test artifacts found! Running emergency cleanup..."
      make clean-all-test-artifacts
      exit 1
    )
```

## Troubleshooting

### Common Issues

1. **Tests leave artifacts**
   - Run `make clean-test-artifacts`
   - Check that tests use proper naming conventions
   - Ensure resource tracker is used

2. **Cleanup fails**
   - Run `make clean-all-test-artifacts` for emergency cleanup
   - Check permissions for removing resources
   - Ensure Docker/Pulumi commands are available

3. **Tests fail with "resource exists"**
   - Previous test didn't clean up properly
   - Run `make check-test-artifacts` to identify artifacts
   - Clean and retry

### Debugging Cleanup

```python
# Check what would be cleaned
from tests.cli.cleanup import TestCleanupManager
from pathlib import Path

manager = TestCleanupManager(Path('.'))
remaining = manager.verify_cleanup()
print(f"Would clean: {remaining}")

# Perform cleanup
results = manager.clean_all()
print(f"Cleaned: {results}")
```

## Best Practices

1. **Always use resource tracking**
   ```python
   def test_creates_service(resource_tracker):
       resource_tracker.track_service("test_service")
       # Create service
   ```

2. **Use proper naming conventions**
   ```python
   service_name = f"test_feature_{timestamp}_{uuid}"
   ```

3. **Prefer context managers**
   ```python
   with test_service(...) as (name, path):
       # Service exists only in this block
   ```

4. **Mark destructive tests**
   ```python
   @pytest.mark.destructive
   def test_modifies_system():
       pass
   ```

5. **Use isolated projects for risky tests**
   ```python
   def test_risky(isolated_project):
       # Work in isolation
   ```

## Quick Reference

### Commands
- `make test-cli-safe` - Run tests with cleanup
- `make test-cli-verify` - Run with verification
- `make check-test-artifacts` - Check for artifacts
- `make clean-test-artifacts` - Clean artifacts
- `make clean-all-test-artifacts` - Emergency cleanup

### Fixtures
- `resource_tracker` - Track resources for cleanup
- `isolated_project` - Isolated project copy
- `cli_runner` - Enhanced CLI runner
- `test_env_vars` - Test environment variables
- `safe_subprocess` - Safe command execution

### Cleanup Functions
- `TestCleanupManager.clean_all()` - Clean everything
- `TestCleanupManager.verify_cleanup()` - Check for artifacts
- `TestCleanupManager.emergency_cleanup()` - Force cleanup

## Workspace Environment for Integration Tests

Integration tests that need filesystem access run in a workspace environment instead of the default sandbox. This allows tests to:
- Access scripts in the repository (e.g., `scripts/new_service.sh`)
- Create and modify files in the actual filesystem
- Test real file operations and service creation

### Configuration
- Workspace environment defined in root `/BUILD` file
- Configured in `pants.toml` under `[environments-preview.names]`
- Tests use `environment="workspace"` in their BUILD targets

### Running Tests with Workspace Environment

```bash
# Run integration tests in workspace
make test-cli-integration-workspace

# Run all tests (unit in sandbox, integration in workspace)
make test-cli-all-workspace

# Verify cleanup after workspace tests
make verify-cleanup
```

### Important Notes
- Workspace tests bypass Pants' caching for reproducibility
- Always ensure proper cleanup after workspace tests
- Use workspace environment only for tests that truly need filesystem access
- Unit tests continue to run in sandbox for speed and isolation

## Contributing

When adding new test commands:

1. Create tests in `tests/cli/test_<feature>.py`
2. Use resource tracking fixtures
3. Follow naming conventions
4. Add appropriate markers
5. For integration tests needing filesystem access:
   - Set `environment="workspace"` in BUILD file
   - Add script dependencies if needed
6. Document any special cleanup needs
7. Run `make test-cli-verify` to ensure cleanup works

## Support

For issues with testing or cleanup:

1. Check this documentation
2. Run `make check-test-artifacts` to diagnose
3. Use `make clean-all-test-artifacts` if stuck
4. Report persistent issues with full error output