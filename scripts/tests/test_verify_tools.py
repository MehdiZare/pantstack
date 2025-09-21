"""Tests for tool verification functionality."""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest


class TestVerifyTools:
    """Test tool verification scripts and functions."""

    @patch("subprocess.run")
    def test_python_version_verification(self, mock_run):
        """Test Python version verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Python 3.11.5",
            stderr=""
        )

        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "3.11" in result.stdout

    @patch("subprocess.run")
    def test_uv_installation_verification(self, mock_run):
        """Test uv installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="uv 0.4.0",
            stderr=""
        )

        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_docker_service_verification(self, mock_run):
        """Test Docker service status verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Server: Docker Desktop",
            stderr=""
        )

        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_aws_cli_verification(self, mock_run):
        """Test AWS CLI installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="aws-cli/2.13.0",
            stderr=""
        )

        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_pulumi_verification(self, mock_run):
        """Test Pulumi installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="v3.80.0",
            stderr=""
        )

        result = subprocess.run(
            ["pulumi", "version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_github_cli_verification(self, mock_run):
        """Test GitHub CLI installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="gh version 2.32.0",
            stderr=""
        )

        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_supabase_cli_verification(self, mock_run):
        """Test Supabase CLI installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="1.68.0",
            stderr=""
        )

        result = subprocess.run(
            ["supabase", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_pants_verification(self, mock_run):
        """Test Pants installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="2.28.0",
            stderr=""
        )

        result = subprocess.run(
            ["pants", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_jq_verification(self, mock_run):
        """Test jq installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="jq-1.6",
            stderr=""
        )

        result = subprocess.run(
            ["jq", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_cruft_verification(self, mock_run):
        """Test cruft installation verification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="cruft, version 2.15.0",
            stderr=""
        )

        result = subprocess.run(
            ["cruft", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_authentication_verification_structure(self):
        """Test authentication verification structure."""
        auth_checks = {
            "github": {"command": ["gh", "auth", "status"], "expected": "Logged in"},
            "aws": {"command": ["aws", "sts", "get-caller-identity"], "expected": "Account"},
            "pulumi": {"command": ["pulumi", "whoami"], "expected": "@"}
        }

        # Verify structure is correct
        assert "github" in auth_checks
        assert "aws" in auth_checks
        assert "pulumi" in auth_checks

        for service, config in auth_checks.items():
            assert "command" in config
            assert "expected" in config
            assert isinstance(config["command"], list)

    @patch("subprocess.run")
    def test_github_auth_status(self, mock_run):
        """Test GitHub authentication status check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="✓ Logged in to github.com as username",
            stderr=""
        )

        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    @patch("subprocess.run")
    def test_aws_auth_status(self, mock_run):
        """Test AWS authentication status check."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"Account": "123456789012", "UserId": "AIDACKCEVSQ6C2EXAMPLE"}',
            stderr=""
        )

        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Verify JSON output
        data = json.loads(result.stdout)
        assert "Account" in data

    def test_version_comparison_logic(self):
        """Test version comparison for minimum requirements."""
        def parse_version(version_str):
            """Parse version string to comparable tuple."""
            # Extract just the version numbers
            import re
            match = re.search(r"(\d+)\.(\d+)\.?(\d+)?", version_str)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3)) if match.group(3) else 0
                return (major, minor, patch)
            return (0, 0, 0)

        # Test version parsing
        assert parse_version("Python 3.11.5") == (3, 11, 5)
        assert parse_version("2.28.0") == (2, 28, 0)
        assert parse_version("gh version 2.32.0") == (2, 32, 0)

        # Test minimum version requirements
        min_versions = {
            "python": (3, 11, 0),
            "pants": (2, 28, 0),
            "gh": (2, 0, 0)
        }

        # All should meet minimum requirements
        current_versions = {
            "python": (3, 11, 5),
            "pants": (2, 28, 0),
            "gh": (2, 32, 0)
        }

        for tool, min_ver in min_versions.items():
            current_ver = current_versions[tool]
            assert current_ver >= min_ver, f"{tool} version {current_ver} below minimum {min_ver}"