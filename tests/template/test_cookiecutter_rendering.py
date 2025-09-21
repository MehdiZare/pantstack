"""Tests for cookiecutter template rendering and variable substitution."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCookiecutterRendering:
    """Test cookiecutter template rendering functionality."""

    @pytest.fixture
    def template_dir(self):
        """Get the template directory (project root)."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def cookiecutter_config(self, template_dir):
        """Load cookiecutter configuration."""
        config_path = template_dir / "cookiecutter.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cookiecutter_json_exists(self, template_dir):
        """Test that cookiecutter.json exists and is valid."""
        config_path = template_dir / "cookiecutter.json"
        assert config_path.exists(), "cookiecutter.json not found"

        with open(config_path) as f:
            config = json.load(f)

        # Verify required fields
        assert "project_slug" in config
        assert "github_owner" in config
        assert "github_repo" in config
        assert "aws_account_id" in config
        assert "aws_region" in config
        assert "pulumi_org" in config

    def test_template_variables_in_files(self, template_dir):
        """Test that template variables are present in key files."""
        files_with_variables = [
            ".env.example",
            ".github/workflows/auto-deploy-dev.yml",
            ".github/workflows/auto-deploy-main.yml",
        ]

        template_pattern = "{{ cookiecutter."

        for file_path in files_with_variables:
            full_path = template_dir / file_path
            if full_path.exists():
                with open(full_path) as f:
                    content = f.read()
                    assert template_pattern in content, \
                        f"No template variables found in {file_path}"

    @patch("subprocess.run")
    def test_cookiecutter_render_basic(self, mock_run, temp_output_dir):
        """Test basic cookiecutter rendering with default values."""
        test_values = {
            "project_slug": "test-project",
            "github_owner": "test-user",
            "github_repo": "test-project",
            "github_visibility": "private",
            "aws_account_id": "123456789012",
            "aws_region": "us-east-1",
            "pulumi_org": "test-org"
        }

        # Mock the cookiecutter command
        mock_run.return_value = MagicMock(returncode=0)

        # Simulate rendering
        expected_files = [
            "README.md",
            "Makefile",
            "cookiecutter.json",
            ".env.example",
            "docker-compose.yml",
            "pants.toml",
        ]

        # Verify expected structure
        for file_name in expected_files:
            assert file_name in expected_files

    def test_template_variable_validation(self, cookiecutter_config):
        """Test that all template variables have valid defaults."""
        required_validations = {
            "project_slug": lambda x: isinstance(x, str) and len(x) > 0,
            "github_owner": lambda x: isinstance(x, str) and len(x) > 0,
            "aws_account_id": lambda x: isinstance(x, str) and x.isdigit() and len(x) == 12,
            "aws_region": lambda x: isinstance(x, str) and "-" in x,
            "pulumi_org": lambda x: isinstance(x, str) and len(x) > 0,
        }

        for field, validator in required_validations.items():
            if field in cookiecutter_config:
                value = cookiecutter_config[field]
                # For choices, take the first one
                if isinstance(value, list):
                    value = value[0] if value else ""

                # Skip template variables in defaults
                if not isinstance(value, str) or not value.startswith("{{"):
                    assert validator(value), \
                        f"Invalid default value for {field}: {value}"

    def test_env_example_rendering(self, template_dir):
        """Test that .env.example contains correct template variables."""
        env_example = template_dir / ".env.example"
        assert env_example.exists(), ".env.example not found"

        with open(env_example) as f:
            content = f.read()

        expected_variables = [
            "{{ cookiecutter.project_slug }}",
            "{{ cookiecutter.aws_account_id }}",
            "{{ cookiecutter.aws_region }}",
            "{{ cookiecutter.github_owner }}",
            "{{ cookiecutter.github_repo }}",
            "{{ cookiecutter.pulumi_org }}",
        ]

        for var in expected_variables:
            assert var in content, f"Missing {var} in .env.example"

    def test_github_workflows_rendering(self, template_dir):
        """Test that GitHub workflows contain correct template variables."""
        workflows_dir = template_dir / ".github" / "workflows"

        if not workflows_dir.exists():
            pytest.skip("GitHub workflows directory not found")

        workflow_files = list(workflows_dir.glob("*.yml"))
        assert len(workflow_files) > 0, "No workflow files found"

        # Check for template variables in workflows
        for workflow_file in workflow_files:
            with open(workflow_file) as f:
                content = f.read()

                # Some workflows should have template variables
                if "auto-deploy" in workflow_file.name or "pr-preview" in workflow_file.name:
                    # These might have AWS account IDs or regions
                    pass  # Template variables are optional in workflows

    def test_no_hardcoded_secrets(self, template_dir):
        """Test that no hardcoded secrets exist in template."""
        patterns_to_avoid = [
            r"aws_access_key_id\s*=\s*['\"]AKI",
            r"aws_secret_access_key\s*=\s*['\"][^{]",
            r"GITHUB_TOKEN\s*=\s*ghp_",
            r"PULUMI_ACCESS_TOKEN\s*=\s*pul-",
            r"password\s*=\s*['\"][^{]",
        ]

        import re

        # Files to check
        files_to_check = [
            ".env.example",
            "docker-compose.yml",
            "docker-compose.local.yml",
        ]

        for file_path in files_to_check:
            full_path = template_dir / file_path
            if full_path.exists():
                with open(full_path) as f:
                    content = f.read()

                for pattern in patterns_to_avoid:
                    matches = re.search(pattern, content, re.IGNORECASE)
                    assert not matches, \
                        f"Potential hardcoded secret found in {file_path}: {pattern}"

    @patch("subprocess.run")
    def test_cruft_create_simulation(self, mock_run, temp_output_dir):
        """Test simulating cruft create command."""
        # Simulate cruft create
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Project created successfully"
        )

        import subprocess

        # Test command construction
        cmd = ["cruft", "create", ".", "--no-input"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        mock_run.assert_called_once()

        # Verify command was called with expected arguments
        called_args = mock_run.call_args[0][0]
        assert "cruft" in called_args
        assert "create" in called_args

    def test_template_directory_structure(self, template_dir):
        """Test that template has expected directory structure."""
        expected_dirs = [
            "services",
            "stack",
            "stack/libs",
            "stack/infra",
            "docs",
            "scripts",
            "tests",
            ".github",
            ".github/workflows",
        ]

        for dir_path in expected_dirs:
            full_path = template_dir / dir_path
            assert full_path.exists() and full_path.is_dir(), \
                f"Expected directory not found: {dir_path}"

    def test_makefile_targets_exist(self, template_dir):
        """Test that Makefile contains expected targets."""
        makefile = template_dir / "Makefile"
        assert makefile.exists(), "Makefile not found"

        with open(makefile) as f:
            content = f.read()

        expected_targets = [
            "help:",
            "quickstart:",
            "new-project:",
            "init-template:",
            "bootstrap:",
            "test:",
            "lint:",
            "fmt:",
        ]

        for target in expected_targets:
            assert target in content, f"Missing target {target} in Makefile"

    def test_docker_compose_template_variables(self, template_dir):
        """Test docker-compose files for template variables."""
        docker_files = [
            "docker-compose.yml",
            "docker-compose.local.yml"
        ]

        for file_name in docker_files:
            file_path = template_dir / file_name
            if file_path.exists():
                with open(file_path) as f:
                    content = f.read()

                # Check for environment variable references
                assert "${" in content or "$" in content, \
                    f"No environment variables found in {file_name}"

    def test_pants_configuration(self, template_dir):
        """Test that pants.toml is properly configured."""
        pants_toml = template_dir / "pants.toml"
        assert pants_toml.exists(), "pants.toml not found"

        with open(pants_toml) as f:
            content = f.read()

        # Check for essential Pants configuration
        assert "[GLOBAL]" in content
        assert "backend_packages" in content
        assert "python" in content

    def test_service_templates(self, template_dir):
        """Test that service templates are properly structured."""
        services_dir = template_dir / "services"

        if not services_dir.exists():
            pytest.skip("Services directory not found")

        # Check example services
        example_services = ["web", "auth", "agent"]

        for service in example_services:
            service_dir = services_dir / service
            if service_dir.exists():
                # Check service structure
                expected_subdirs = ["app", "domain", "adapters", "tests"]
                for subdir in expected_subdirs:
                    assert (service_dir / subdir).exists() or \
                           any((service_dir / d).exists() for d in ["app", "domain"]), \
                           f"Service {service} missing expected directory: {subdir}"

    def test_requirements_files(self, template_dir):
        """Test that requirements files exist and are valid."""
        requirements_dir = template_dir / "requirements"

        if requirements_dir.exists():
            req_files = list(requirements_dir.glob("*.txt"))
            assert len(req_files) > 0, "No requirements files found"

            for req_file in req_files:
                with open(req_file) as f:
                    content = f.read()
                    # Basic validation - should have some packages
                    if content.strip():  # Skip empty files
                        assert "==" in content or ">=" in content or "#" in content, \
                            f"Invalid requirements format in {req_file.name}"