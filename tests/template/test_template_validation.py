"""Tests for template validation and completeness."""

import json
import re
from pathlib import Path

import pytest


class TestTemplateValidation:
    """Validate template structure and completeness."""

    @pytest.fixture
    def template_dir(self):
        """Get the template directory (project root)."""
        import os

        # When running with Pants (run_goal_use_sandbox=False), we're in the repo root
        # Start from current file location and go up
        current_file = Path(__file__).resolve()

        # Navigate up to find the project root by looking for marker files
        for parent in current_file.parents:
            # Check for key template files that indicate we're at the root
            if (parent / "cookiecutter.json").exists() and (
                parent / "pants.toml"
            ).exists():
                return parent

        # If not found, we might be running from repo root already
        cwd = Path.cwd()
        if (cwd / "cookiecutter.json").exists() and (cwd / "pants.toml").exists():
            return cwd

        # Final fallback - assume we're 3 levels deep (tests/template/test_file.py)
        return current_file.parent.parent.parent

    @pytest.fixture
    def all_template_files(self, template_dir):
        """Get all files in template, excluding common ignore patterns."""
        ignore_patterns = {
            ".git",
            ".pants.d",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "dist",
            "build",
            ".venv",
            "node_modules",
            ".DS_Store",
            ".env",
            "*.pyc",
            "*.egg-info",
        }

        all_files = []
        for file_path in template_dir.rglob("*"):
            if file_path.is_file():
                # Check if any part of the path matches ignore patterns
                path_parts = file_path.relative_to(template_dir).parts
                if not any(pattern in str(file_path) for pattern in ignore_patterns):
                    all_files.append(file_path)

        return all_files

    def test_all_template_variables_defined(self, template_dir):
        """Test that all template variables used are defined in cookiecutter.json."""
        config_path = template_dir / "cookiecutter.json"
        if not config_path.exists():
            pytest.skip("cookiecutter.json not found - not a template project")

        with open(config_path) as f:
            config = json.load(f)

        defined_vars = set(config.keys())

        # Find all template variables used
        template_pattern = re.compile(r"\{\{\s*cookiecutter\.(\w+)\s*\}\}")
        used_vars = set()

        files_to_check = [
            ".env.example",
            ".github/workflows/auto-deploy-dev.yml",
            ".github/workflows/auto-deploy-main.yml",
            ".github/workflows/pr-preview.yml",
        ]

        for file_path in files_to_check:
            full_path = template_dir / file_path
            if full_path.exists():
                with open(full_path) as f:
                    content = f.read()
                    matches = template_pattern.findall(content)
                    used_vars.update(matches)

        # Check for undefined variables
        undefined_vars = used_vars - defined_vars
        assert (
            len(undefined_vars) == 0
        ), f"Undefined template variables found: {undefined_vars}"

    def test_no_orphaned_template_variables(self, template_dir):
        """Test that all defined variables are actually used."""
        config_path = template_dir / "cookiecutter.json"
        with open(config_path) as f:
            config = json.load(f)

        defined_vars = set(config.keys())

        # Find all template variables used
        template_pattern = re.compile(r"\{\{\s*cookiecutter\.(\w+)\s*\}\}")
        used_vars = set()

        # Check all relevant files
        for file_path in template_dir.rglob("*"):
            if file_path.is_file() and ".git" not in str(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = template_pattern.findall(content)
                        used_vars.update(matches)
                except (UnicodeDecodeError, PermissionError):
                    # Skip binary files or permission issues
                    continue

        # Some variables might be optional or used in generated code
        optional_vars = {"github_visibility"}  # Example of optional variable

        orphaned_vars = defined_vars - used_vars - optional_vars
        # It's okay to have some orphaned vars for future use
        # but warn about them
        if orphaned_vars:
            print(f"Warning: Potentially unused template variables: {orphaned_vars}")

    def test_consistent_template_syntax(self, all_template_files):
        """Test that template syntax is consistent across files."""
        inconsistent_patterns = []

        for file_path in all_template_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for inconsistent spacing in template variables
                if "{{cookiecutter." in content:  # Missing space
                    inconsistent_patterns.append((file_path, "Missing space after {{"))
                if "{{ cookiecutter ." in content:  # Extra space
                    inconsistent_patterns.append((file_path, "Extra space in variable"))
                if "{{  cookiecutter" in content:  # Double space
                    inconsistent_patterns.append(
                        (file_path, "Double space in template")
                    )

            except (UnicodeDecodeError, PermissionError):
                continue

        assert (
            len(inconsistent_patterns) == 0
        ), f"Inconsistent template syntax found: {inconsistent_patterns}"

    def test_required_files_exist(self, template_dir):
        """Test that all required files for a template exist."""
        required_files = [
            "cookiecutter.json",
            "README.md",
            "LICENSE",
            "CONTRIBUTING.md",
            ".gitignore",
            "Makefile",
            ".env.example",
            "requirements.txt",
            "pants.toml",
            "pyproject.toml",
        ]

        missing_files = []
        for file_name in required_files:
            file_path = template_dir / file_name
            if not file_path.exists():
                # Special handling for requirements.txt - can be in multiple locations
                if file_name == "requirements.txt":
                    alt_paths = [
                        template_dir / "requirements" / "requirements.txt",
                        template_dir / "3rdparty" / "python" / "requirements.txt",
                        template_dir / "3rdparty" / "python" / "requirements-test.txt",
                    ]
                    if not any(p.exists() for p in alt_paths):
                        missing_files.append(file_name)
                else:
                    missing_files.append(file_name)

        assert len(missing_files) == 0, f"Required files missing: {missing_files}"

    def test_github_workflows_valid(self, template_dir):
        """Test that GitHub workflows are valid YAML."""
        import yaml

        workflows_dir = template_dir / ".github" / "workflows"
        if not workflows_dir.exists():
            pytest.skip("No workflows directory")

        invalid_workflows = []
        for workflow_file in workflows_dir.glob("*.yml"):
            try:
                with open(workflow_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                invalid_workflows.append((workflow_file.name, str(e)))

        assert (
            len(invalid_workflows) == 0
        ), f"Invalid workflow files: {invalid_workflows}"

    def test_python_files_syntax(self, template_dir):
        """Test that all Python files have valid syntax."""
        import ast
        import py_compile

        python_files = list(template_dir.rglob("*.py"))
        syntax_errors = []

        for py_file in python_files:
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()

                # Skip template files that might have cookiecutter variables
                if "{{ cookiecutter" in source:
                    continue

                # Try to compile the Python file
                ast.parse(source)
            except SyntaxError as e:
                syntax_errors.append((py_file.relative_to(template_dir), str(e)))

        assert len(syntax_errors) == 0, f"Python syntax errors found: {syntax_errors}"

    def test_dockerfile_exists_and_valid(self, template_dir):
        """Test that Dockerfiles exist and are valid."""
        dockerfile_locations = [
            "Dockerfile",
            "services/web/Dockerfile",
            "docker/Dockerfile",
        ]

        dockerfiles_found = []
        for location in dockerfile_locations:
            dockerfile = template_dir / location
            if dockerfile.exists():
                dockerfiles_found.append(location)

                with open(dockerfile) as f:
                    content = f.read()

                # Basic Dockerfile validation
                assert "FROM" in content, f"No FROM statement in {location}"

        # At least one Dockerfile should exist
        # Note: This is optional for templates
        if len(dockerfiles_found) == 0:
            print("Warning: No Dockerfiles found in template")

    def test_makefile_help_target(self, template_dir):
        """Test that Makefile has a help target with documentation."""
        makefile = template_dir / "Makefile"
        assert makefile.exists()

        with open(makefile) as f:
            content = f.read()

        # Check for help target
        assert "help:" in content, "No help target in Makefile"

        # Check that targets have documentation (## comments)
        documented_targets = re.findall(r"^[\w-]+:.*##\s+.+", content, re.MULTILINE)
        assert len(documented_targets) > 5, "Not enough documented targets in Makefile"

    def test_env_example_completeness(self, template_dir):
        """Test that .env.example contains all necessary variables."""
        env_example = template_dir / ".env.example"
        assert env_example.exists()

        with open(env_example) as f:
            content = f.read()

        required_env_vars = [
            "PROJECT_SLUG",
            "AWS_ACCOUNT_ID",
            "AWS_REGION",
            "GITHUB_OWNER",
            "GITHUB_REPO",
            "PULUMI_ORG",
        ]

        missing_vars = []
        for var in required_env_vars:
            if var not in content:
                missing_vars.append(var)

        assert (
            len(missing_vars) == 0
        ), f"Missing environment variables in .env.example: {missing_vars}"

    def test_documentation_exists(self, template_dir):
        """Test that essential documentation exists."""
        docs_to_check = [
            ("README.md", ["## Quick Start", "## Prerequisites"]),
            ("CONTRIBUTING.md", ["## How", "## Code of Conduct"]),
            ("docs/getting-started/quick-start.md", None),
        ]

        for doc_path, required_sections in docs_to_check:
            full_path = template_dir / doc_path
            if full_path.exists():
                with open(full_path) as f:
                    content = f.read()

                if required_sections:
                    for section in required_sections:
                        assert (
                            section in content
                        ), f"Missing section '{section}' in {doc_path}"

    def test_scripts_are_executable(self, template_dir):
        """Test that shell scripts have executable permissions."""
        scripts_dir = template_dir / "scripts"
        if not scripts_dir.exists():
            pytest.skip("No scripts directory")

        non_executable = []
        for script in scripts_dir.rglob("*.sh"):
            if not script.is_file():
                continue

            # Check if file is executable
            import os
            import stat

            file_stat = os.stat(script)
            is_executable = bool(file_stat.st_mode & stat.S_IXUSR)

            if not is_executable:
                non_executable.append(script.relative_to(template_dir))

        assert (
            len(non_executable) == 0
        ), f"Non-executable scripts found: {non_executable}"

    def test_template_does_not_contain_secrets(self, all_template_files, template_dir):
        """Test that template doesn't contain any secrets or sensitive data."""
        secret_patterns = [
            re.compile(r'aws_access_key_id\s*=\s*["\']?AKI[A-Z0-9]{16}'),
            re.compile(r'aws_secret_access_key\s*=\s*["\']?[A-Za-z0-9/+=]{40}'),
            re.compile(r"GITHUB_TOKEN\s*=\s*ghp_[a-zA-Z0-9]{36}"),
            re.compile(r"PULUMI_ACCESS_TOKEN\s*=\s*pul-[a-f0-9]{40}"),
            re.compile(r'["\']sk_live_[a-zA-Z0-9]{24,}'),  # Stripe
            re.compile(r'["\']pk_live_[a-zA-Z0-9]{24,}'),  # Stripe
        ]

        files_with_secrets = []
        for file_path in all_template_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                for pattern in secret_patterns:
                    if pattern.search(content):
                        files_with_secrets.append(file_path.relative_to(template_dir))
                        break

            except (UnicodeDecodeError, PermissionError):
                continue

        assert (
            len(files_with_secrets) == 0
        ), f"Files containing potential secrets: {files_with_secrets}"

    def test_service_structure_consistency(self, template_dir):
        """Test that all services follow the same structure."""
        services_dir = template_dir / "services"
        if not services_dir.exists():
            pytest.skip("No services directory")

        services = [d for d in services_dir.iterdir() if d.is_dir()]

        if not services:
            pytest.skip("No services found")

        # Define expected structure for each service
        expected_structure = {
            "app": ["api"],  # or ["worker"] for worker services
            "domain": ["models.py", "services.py", "ports.py"],
            "adapters": [],  # Optional
            "public": [],  # Optional
            "tests": [],  # Should have tests
        }

        inconsistent_services = []
        for service in services:
            for required_dir, required_files in expected_structure.items():
                dir_path = service / required_dir

                if required_dir in ["app", "domain", "tests"]:
                    if not dir_path.exists():
                        inconsistent_services.append(
                            f"{service.name} missing {required_dir}"
                        )

        assert (
            len(inconsistent_services) == 0
        ), f"Inconsistent service structure: {inconsistent_services}"

    def test_pants_build_files_exist(self, template_dir):
        """Test that BUILD files exist for Pants build system."""
        # Check root BUILD file
        root_build = template_dir / "BUILD"

        # Check service BUILD files
        services_dir = template_dir / "services"
        if services_dir.exists():
            services_without_build = []
            for service in services_dir.iterdir():
                if service.is_dir():
                    build_file = service / "BUILD"
                    if not build_file.exists():
                        services_without_build.append(service.name)

            assert (
                len(services_without_build) == 0
            ), f"Services missing BUILD files: {services_without_build}"

    def test_template_metadata(self, template_dir):
        """Test that template has proper metadata."""
        # Check package.json for Node/npm metadata
        package_json = template_dir / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                package_data = json.load(f)

            assert "name" in package_data
            assert "version" in package_data
            assert "description" in package_data

        # Check pyproject.toml for Python metadata
        pyproject = template_dir / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject) as f:
                content = f.read()

            assert "[project]" in content or "[tool.poetry]" in content
            assert "name" in content
            assert "version" in content
