# Contributing to Pantstack Template

Thank you for your interest in contributing to Pantstack! This guide will help you contribute effectively.

## Ways to Contribute

### Reporting Issues

1. **Bug Reports**
   - Use the bug report template
   - Include reproduction steps
   - Specify your environment (OS, Python version, etc.)
   - Attach relevant logs or error messages

2. **Feature Requests**
   - Use the feature request template
   - Explain the use case
   - Provide examples if possible
   - Consider backward compatibility

### Code Contributions

1. **Bug Fixes**
   - Reference the issue number
   - Include tests for the fix
   - Update documentation if needed

2. **New Features**
   - Discuss in an issue first
   - Follow existing patterns
   - Add comprehensive tests
   - Document the feature

3. **Documentation**
   - Fix typos and clarify unclear sections
   - Add examples and use cases
   - Improve getting started guides
   - Translate documentation

## Development Setup

### Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/pantstack.git
cd pantstack

# Add upstream remote
git remote add upstream https://github.com/MehdiZare/pantstack.git

# Keep fork updated
git fetch upstream
git checkout main
git merge upstream/main
```

### Environment Setup

```bash
# Install development dependencies
make boot
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Copy and configure environment
cp .env.example .env
# Edit .env with test values
```

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test
make fmt     # Format code
make lint    # Run linters
make test    # Run tests

# Commit with conventional commits
git commit -m "feat: add new module template"

# Push to your fork
git push origin feature/your-feature-name
```

## Contribution Guidelines

### Code Style

#### Python Code
- Follow PEP 8
- Use Black for formatting
- Type hints for all functions
- Docstrings for public APIs

```python
from typing import Optional, List

def process_data(
    items: List[str],
    filter_empty: bool = True
) -> Optional[List[str]]:
    """Process a list of data items.

    Args:
        items: List of strings to process
        filter_empty: Whether to filter empty strings

    Returns:
        Processed list or None if input is empty
    """
    if not items:
        return None

    if filter_empty:
        items = [item for item in items if item]

    return items
```

#### Shell Scripts
- Use shellcheck for validation
- Add error handling
- Document complex commands

```bash
#!/usr/bin/env bash
set -euo pipefail

# Description of what this script does
main() {
    local module_name="${1:?Module name required}"

    echo "Creating module: ${module_name}"

    # Complex command with explanation
    # This finds all BUILD files and updates them
    find . -name "BUILD" -type f -exec \
        sed -i "s/old_pattern/new_pattern/g" {} \;
}

main "$@"
```

#### YAML Files
- Use yamllint for validation
- Consistent indentation (2 spaces)
- Comments for complex sections

```yaml
# GitHub Actions workflow
name: CI Pipeline

on:
  push:
    branches: [main, dev]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      # Cache dependencies for faster builds
      - uses: actions/cache@v3
        with:
          path: ~/.cache/pants
          key: ${{ runner.os }}-pants-${{ hashFiles('pants.toml') }}
```

### Commit Messages

Follow Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or changes
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

Examples:
```bash
# Feature
git commit -m "feat(modules): add GraphQL module template"

# Bug fix
git commit -m "fix(ci): correct Python version in test matrix"

# Breaking change
git commit -m "feat!: restructure module layout

BREAKING CHANGE: Modules now use src/ layout instead of flat structure"

# With scope and body
git commit -m "docs(api): improve FastAPI examples

- Add authentication example
- Include error handling patterns
- Update dependency injection docs"
```

### Testing Requirements

#### Unit Tests
```python
# modules/api/backend/tests/test_example.py
import pytest
from ..service.example import ExampleService

class TestExampleService:
    """Test suite for ExampleService."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ExampleService()

    def test_basic_functionality(self, service):
        """Test basic service functionality."""
        result = service.process("input")
        assert result == "expected_output"

    @pytest.mark.parametrize("input,expected", [
        ("test1", "output1"),
        ("test2", "output2"),
        ("", None),
    ])
    def test_various_inputs(self, service, input, expected):
        """Test service with various inputs."""
        assert service.process(input) == expected
```

#### Integration Tests
```python
# Test template generation
def test_template_generation():
    """Test that template generates valid project."""
    from cookiecutter.main import cookiecutter

    # Generate project
    project_dir = cookiecutter(
        ".",
        no_input=True,
        extra_context={
            "project_slug": "test-project",
            "github_owner": "test-owner",
        }
    )

    # Verify structure
    assert Path(project_dir / "modules").exists()
    assert Path(project_dir / "pants.toml").exists()

    # Test generated project
    subprocess.run(["make", "test"], cwd=project_dir, check=True)
```

### Documentation Standards

#### Module Documentation
```markdown
# Module Name

Brief description of what this module does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

\```bash
make new-module M=module-name
\```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API key for service | None |
| `TIMEOUT` | Request timeout | 30s |

## Usage

### Basic Example

\```python
from module_name import Client

client = Client(api_key="your-key")
result = client.process(data)
\```

## API Reference

### `Client`

Main client class for interacting with the service.

#### `process(data: Dict) -> Result`

Process the provided data.

**Parameters:**
- `data`: Dictionary containing input data

**Returns:**
- `Result` object with processed data

**Raises:**
- `ValueError`: If data is invalid
- `ConnectionError`: If service is unavailable
```

## Pull Request Process

### Before Submitting

1. **Test Your Changes**
   ```bash
   # Run full test suite
   make test

   # Test template generation
   cookiecutter . --no-input

   # Test specific modules
   pants test modules/api::
   ```

2. **Update Documentation**
   - Add/update relevant documentation
   - Update README if needed
   - Add migration notes for breaking changes

3. **Check Code Quality**
   ```bash
   # Format code
   make fmt

   # Run linters
   make lint

   # Type checking
   make typecheck
   ```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Conventional commit messages
- [ ] No merge conflicts

## Testing
How to test these changes

## Screenshots (if applicable)
Add screenshots for UI changes
```

### Review Process

1. **Automated Checks**
   - CI must pass
   - Code coverage maintained
   - No security vulnerabilities

2. **Code Review**
   - At least one approval required
   - Address all feedback
   - Keep discussions professional

3. **Merge Requirements**
   - Squash commits if needed
   - Update from main if outdated
   - Delete branch after merge

## Release Process

### Version Bumping

Versions are automatically determined by commit messages:
- `feat:` → Minor version bump
- `fix:` → Patch version bump
- `feat!:` or `BREAKING CHANGE:` → Major version bump

### Release Workflow

1. **Development**
   - Work happens on feature branches
   - PRs to `dev` branch
   - Automatic prerelease versions

2. **Release Preparation**
   ```bash
   # Create release PR
   gh pr create \
     --base main \
     --head dev \
     --title "Release v1.2.0" \
     --label "release:minor"
   ```

3. **Release Creation**
   - Merge to main triggers release
   - Automatic changelog generation
   - GitHub release creation
   - Template repository update

## Community

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Stack Overflow**: Tag with `pantstack`

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards others

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes
- Project documentation

## Legal

### License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT).

### Developer Certificate of Origin

By making a contribution, you certify that:
1. The contribution is your original work
2. You have the right to submit it
3. You understand it will be public
4. You grant license to the project

## Resources

### Helpful Links

- [Pants Documentation](https://www.pantsbuild.org/docs)
- [Pulumi Documentation](https://www.pulumi.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Development Tools

- [Black](https://black.readthedocs.io/): Python formatter
- [mypy](http://mypy-lang.org/): Static type checker
- [pytest](https://docs.pytest.org/): Testing framework
- [pre-commit](https://pre-commit.com/): Git hooks framework

Thank you for contributing to Pantstack! 🚀
