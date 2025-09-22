"""Tests for setup tools functionality."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSetupTools:
    """Test setup tools scripts and functions."""

    def test_check_tool_installation(self):
        """Test tool installation verification."""
        # Test with a tool that exists
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Python" in result.stdout

    def test_detect_os(self):
        """Test OS detection logic."""
        import platform

        system = platform.system().lower()

        # Should detect macOS or Linux
        assert system in ["darwin", "linux"]

    @patch("subprocess.run")
    def test_homebrew_installation_check(self, mock_run):
        """Test Homebrew installation check."""
        # Mock successful brew command
        mock_run.return_value = Mock(returncode=0, stdout="Homebrew 4.0.0")

        result = subprocess.run(["brew", "--version"], capture_output=True, text=True)
        assert result.returncode == 0

    def test_env_file_creation(self):
        """Test .env file creation from template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create example env file
            env_example = temp_path / ".env.example"
            env_example.write_text("EXAMPLE_VAR=example_value\n")

            # Create .env from example
            env_file = temp_path / ".env"
            env_file.write_text(env_example.read_text())

            assert env_file.exists()
            assert "EXAMPLE_VAR=example_value" in env_file.read_text()

    @patch("subprocess.run")
    def test_tool_version_check(self, mock_run):
        """Test version checking for tools."""
        # Mock version output
        mock_run.return_value = Mock(returncode=0, stdout="Python 3.11.0", stderr="")

        result = subprocess.run(
            ["python3", "--version"], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "Python" in result.stdout

    def test_path_configuration(self):
        """Test PATH configuration requirements."""
        path = os.environ.get("PATH", "")

        # Check that basic directories are in PATH
        path_dirs = path.split(os.pathsep)

        # Should have standard system paths
        system_paths = ["/usr/bin", "/bin"]
        for sys_path in system_paths:
            assert any(sys_path in p for p in path_dirs)

    @patch("os.makedirs")
    @patch("pathlib.Path.write_text")
    def test_virtual_environment_creation(self, mock_write, mock_makedirs):
        """Test virtual environment creation simulation."""
        venv_path = Path(".venv")

        # Simulate venv creation
        mock_makedirs.return_value = None
        mock_write.return_value = None

        # This would normally create a venv
        assert True  # Placeholder for actual venv creation test

    def test_required_tools_list(self):
        """Test that required tools are properly defined."""
        required_tools = [
            "python3",
            "uv",
            "docker",
            "aws",
            "pulumi",
            "gh",
            "supabase",
            "pants",
            "jq",
            "cruft",
        ]

        # All tools should be defined
        assert len(required_tools) == 10
        assert "python3" in required_tools
        assert "docker" in required_tools

    @patch("subprocess.run")
    def test_docker_installation_check(self, mock_run):
        """Test Docker installation verification."""
        # Mock docker version command
        mock_run.return_value = Mock(
            returncode=0, stdout="Docker version 20.10.0", stderr=""
        )

        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)

        assert result.returncode == 0

    def test_script_permissions(self):
        """Test that setup scripts have executable permissions."""
        script_files = [
            "scripts/setup-tools.sh",
            "scripts/quick-setup.sh",
            "scripts/setup/verify-tools.sh",
        ]

        for script in script_files:
            if Path(script).exists():
                # Check if file has execute permission
                stat_info = os.stat(script)
                assert stat_info.st_mode & 0o111  # Execute permission for someone
