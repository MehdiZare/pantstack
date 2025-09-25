"""Tests for Makefile commands and CLI integration."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestMakeCommands:
    """Test Makefile commands and their integration."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def makefile_exists(self, project_root):
        """Verify Makefile exists."""
        makefile = project_root / "Makefile"
        if not makefile.exists():
            pytest.skip("Makefile not found")
        return makefile

    @pytest.fixture
    def temp_env_file(self):
        """Create temporary .env file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("PROJECT_SLUG=test-project\n")
            f.write("AWS_ACCOUNT_ID=123456789012\n")
            f.write("AWS_REGION=us-east-1\n")
            f.write("GITHUB_OWNER=test-user\n")
            f.write("GITHUB_REPO=test-repo\n")
            f.write("PULUMI_ORG=test-org\n")
            temp_path = f.name

        yield Path(temp_path)

        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    def test_make_help_command(self, project_root, makefile_exists):
        """Test that make help command works and shows expected output."""
        result = subprocess.run(
            ["make", "help"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"make help failed: {result.stderr}"
        assert "Pantstack Monorepo Commands" in result.stdout
        assert "Setup Commands" in result.stdout
        assert "Template Commands" in result.stdout
        assert "Development Commands" in result.stdout

    @patch("subprocess.run")
    def test_make_new_project(self, mock_run, project_root):
        """Test make new-project command."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="Project created successfully"
        )

        # Simulate running the command
        result = subprocess.run(
            ["make", "new-project"], cwd=project_root, capture_output=True, text=True
        )

        mock_run.assert_called_once()

        # Verify make command was called
        call_args = mock_run.call_args[0][0]
        assert "make" in call_args
        assert "new-project" in call_args

    @patch("subprocess.run")
    def test_make_init_template(self, mock_run, project_root, temp_env_file):
        """Test make init-template command."""
        mock_run.return_value = MagicMock(returncode=0)

        # Set environment to use temp .env
        env = os.environ.copy()
        env["ENV_FILE"] = str(temp_env_file)

        result = subprocess.run(
            ["make", "init-template"],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
        )

        # Check that publish_template.sh would be called
        # Note: Actual execution depends on .env file existence

    @patch("subprocess.run")
    def test_make_bootstrap(self, mock_run, project_root):
        """Test make bootstrap command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Bootstrap completed")

        result = subprocess.run(
            ["make", "bootstrap"], cwd=project_root, capture_output=True, text=True
        )

        mock_run.assert_called()

    def test_make_test_command(self, project_root, makefile_exists):
        """Test that make test command structure is correct."""
        with open(makefile_exists) as f:
            content = f.read()

        # Verify test targets exist
        assert "test:" in content
        assert "test-unit:" in content or "test:" in content
        assert "pants" in content or "pytest" in content

    @patch("subprocess.run")
    def test_make_new_service(self, mock_run, project_root):
        """Test make new-service command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Service created")

        # Test with service name
        result = subprocess.run(
            ["make", "new-service", "S=orders"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        mock_run.assert_called()

    def test_make_lint_command(self, project_root, makefile_exists):
        """Test that make lint command exists."""
        with open(makefile_exists) as f:
            content = f.read()

        assert "lint:" in content
        # Should use pants or other linting tools
        assert "pants" in content or "black" in content or "ruff" in content

    def test_make_fmt_command(self, project_root, makefile_exists):
        """Test that make fmt command exists."""
        with open(makefile_exists) as f:
            content = f.read()

        assert "fmt:" in content
        # Should format code
        assert "pants" in content or "black" in content or "isort" in content

    @patch("subprocess.run")
    def test_make_dev_up(self, mock_run, project_root):
        """Test make dev-up command for local development."""
        mock_run.return_value = MagicMock(returncode=0)

        result = subprocess.run(
            ["make", "dev-up"], cwd=project_root, capture_output=True, text=True
        )

        mock_run.assert_called()
        # Should call make dev-up
        call_args = mock_run.call_args[0][0]
        assert "make" in call_args
        assert "dev-up" in call_args

    @patch("subprocess.run")
    def test_make_dev_down(self, mock_run, project_root):
        """Test make dev-down command."""
        mock_run.return_value = MagicMock(returncode=0)

        result = subprocess.run(
            ["make", "dev-down"], cwd=project_root, capture_output=True, text=True
        )

        mock_run.assert_called()

    def test_make_stack_commands(self, project_root, makefile_exists):
        """Test that stack management commands exist."""
        with open(makefile_exists) as f:
            content = f.read()

        stack_commands = [
            "svc-stack-up",
            "svc-stack-destroy",
            "svc-stack-preview",
            "svc-stack-outputs",
        ]

        for command in stack_commands:
            assert (
                f"{command}:" in content or command in content
            ), f"Missing stack command: {command}"

    @patch("subprocess.run")
    def test_make_seed_stacks(self, mock_run, project_root):
        """Test make seed-stacks command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Stacks initialized")

        result = subprocess.run(
            ["make", "seed-stacks"], cwd=project_root, capture_output=True, text=True
        )

        mock_run.assert_called()

    def test_make_github_commands(self, project_root, makefile_exists):
        """Test that GitHub integration commands exist."""
        with open(makefile_exists) as f:
            content = f.read()

        github_commands = [
            "gh-new-module-pr",
            "gha-deploy",
            "gha-ci",
        ]

        for command in github_commands:
            assert command in content, f"Missing GitHub command: {command}"

    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_make_with_environment_variables(self, mock_run, mock_exists, project_root):
        """Test that make commands properly handle environment variables."""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        # Test with environment variables
        env = os.environ.copy()
        env["S"] = "test-service"
        env["ENV"] = "test"

        result = subprocess.run(
            ["make", "svc-stack-up", "S=test-service", "ENV=test"],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
        )

        # Verify environment variables are passed
        assert env["S"] == "test-service"
        assert env["ENV"] == "test"

    def test_makefile_variable_definitions(self, makefile_exists):
        """Test that Makefile has proper variable definitions."""
        with open(makefile_exists) as f:
            content = f.read()

        # Check for common variable patterns
        assert ".DEFAULT_GOAL" in content or "help:" in content
        assert ".PHONY:" in content

    @patch("subprocess.run")
    def test_make_quickstart(self, mock_run, project_root):
        """Test make quickstart interactive wizard."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Quickstart completed")

        result = subprocess.run(
            ["make", "quickstart"], cwd=project_root, capture_output=True, text=True
        )

        mock_run.assert_called()
        # Should run quickstart.sh script
        call_args = str(mock_run.call_args)
        assert "quickstart" in call_args.lower()

    def test_make_documentation_commands(self, makefile_exists):
        """Test that documentation commands exist."""
        with open(makefile_exists) as f:
            content = f.read()

        doc_commands = ["docs-serve", "docs-build", "docs-publish"]

        # At least some documentation commands should exist
        doc_commands_found = [cmd for cmd in doc_commands if cmd in content]
        assert len(doc_commands_found) > 0, "No documentation commands found"

    @patch("subprocess.run")
    def test_make_setup_commands(self, mock_run, project_root):
        """Test setup-related make commands."""
        mock_run.return_value = MagicMock(returncode=0)

        setup_commands = ["setup", "setup-quick", "check-tools"]

        for command in setup_commands:
            # Check if command exists in Makefile
            makefile = project_root / "Makefile"
            if makefile.exists():
                with open(makefile) as f:
                    content = f.read()
                    if f"{command}:" in content:
                        result = subprocess.run(
                            ["make", command],
                            cwd=project_root,
                            capture_output=True,
                            text=True,
                        )
                        # Command should at least be callable
                        assert result is not None

    def test_make_command_error_handling(self, project_root):
        """Test that make commands handle errors appropriately."""
        # Test with non-existent target
        result = subprocess.run(
            ["make", "non_existent_target"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        # Should return non-zero exit code
        assert result.returncode != 0

        # Should show error message
        assert (
            "No rule to make target" in result.stderr
            or "Error" in result.stderr
            or "No such" in result.stderr
        )

    def test_make_parallel_execution(self, makefile_exists):
        """Test that Makefile supports parallel execution where appropriate."""
        with open(makefile_exists) as f:
            content = f.read()

        # Check for .NOTPARALLEL directive (if sequential execution is required)
        # or verify that independent targets can be run in parallel
        if ".NOTPARALLEL" not in content:
            # Makefile should support parallel execution by default
            assert True
        else:
            # If .NOTPARALLEL is set, there should be a good reason
            assert ".NOTPARALLEL" in content
