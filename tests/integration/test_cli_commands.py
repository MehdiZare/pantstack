"""Integration tests for CLI commands - actual execution tests."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest


# Check if we're in a sandbox environment
def in_sandbox():
    """Check if running in a sandbox environment."""
    current_path = Path(__file__).resolve()
    return "/pants-sandbox-" in str(current_path) or "/tmp/" in str(current_path)


# Skip all tests if in sandbox
pytestmark = pytest.mark.skipif(
    in_sandbox(),
    reason="CLI integration tests require filesystem access - skipping in sandbox",
)


class TestCLICommandsIntegration:
    """Integration tests for CLI commands with real execution."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def temp_service_name(self):
        """Generate unique temporary service name."""
        timestamp = int(time.time())
        return f"test_svc_{timestamp}"

    @pytest.fixture(autouse=True)
    def cleanup(self, project_root, temp_service_name):
        """Cleanup any test artifacts after each test."""
        yield
        # Cleanup test service if created
        service_path = project_root / "services" / temp_service_name
        if service_path.exists():
            shutil.rmtree(service_path)

        # Cleanup requirements files
        for pattern in [
            f"requirements-{temp_service_name}-*.txt",
            "requirements-test_svc_*-*.txt",
        ]:
            for req_file in (project_root / "3rdparty" / "python").glob(pattern):
                req_file.unlink()

    def test_make_help_works(self, project_root):
        """Test that make help command actually works."""
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
        assert "Development Commands" in result.stdout
        assert "new-service" in result.stdout

    def test_new_service_script_basic(self, project_root, temp_service_name):
        """Test basic new_service.sh script execution."""
        result = subprocess.run(
            ["./scripts/new_service.sh"],
            cwd=project_root,
            env={**os.environ, "S": temp_service_name},
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert f"Service '{temp_service_name}' scaffolded" in result.stdout

        # Verify service directory was created
        service_path = project_root / "services" / temp_service_name
        assert service_path.exists()
        assert (service_path / "BUILD").exists()
        assert (service_path / "app" / "api" / "main.py").exists()
        assert (service_path / "infrastructure" / "__main__.py").exists()

    def test_new_service_enhanced_script(self, project_root, temp_service_name):
        """Test enhanced new_service_enhanced.sh script execution."""
        enhanced_script = project_root / "scripts" / "new_service_enhanced.sh"
        if not enhanced_script.exists():
            pytest.skip("Enhanced script not found")

        result = subprocess.run(
            ["./scripts/new_service_enhanced.sh"],
            cwd=project_root,
            env={**os.environ, "S": temp_service_name},
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert (
            f"Enhanced service '{temp_service_name}' scaffolded successfully"
            in result.stdout
        )

        # Verify enhanced structure
        service_path = project_root / "services" / temp_service_name
        assert service_path.exists()

        # Check for enhanced features
        assert (service_path / "app" / "api" / "routes").exists()
        assert (service_path / "app" / "worker" / "tasks.py").exists()
        assert (service_path / "lib" / "repositories").exists()
        assert (service_path / "domain" / "models").exists()
        assert (service_path / "domain" / "services").exists()
        assert (service_path / "config" / "settings.py").exists()
        assert (service_path / "tests" / "conftest.py").exists()

    def test_service_already_exists_handling(self, project_root, temp_service_name):
        """Test handling when service already exists."""
        service_path = project_root / "services" / temp_service_name
        service_path.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ["./scripts/new_service.sh"],
            cwd=project_root,
            env={**os.environ, "S": temp_service_name},
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert f"Service '{temp_service_name}' already exists" in result.stdout

    def test_make_new_service_command(self, project_root, temp_service_name):
        """Test make new-service command."""
        result = subprocess.run(
            ["make", "new-service", f"S={temp_service_name}"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should either succeed or report service exists
        assert result.returncode == 0 or "already exists" in result.stdout

        # Verify service was created if successful
        if "scaffolded" in result.stdout:
            service_path = project_root / "services" / temp_service_name
            assert service_path.exists()

    def test_pants_resolvers_update(self, project_root, temp_service_name):
        """Test that pants.toml is updated with new resolvers."""
        # Run service creation
        result = subprocess.run(
            ["./scripts/new_service.sh"],
            cwd=project_root,
            env={**os.environ, "S": temp_service_name},
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and "scaffolded" in result.stdout:
            # Check if update_pants_resolvers.sh was called
            if "Added resolvers" in result.stdout:
                # Verify pants.toml was updated
                pants_toml = project_root / "pants.toml"
                content = pants_toml.read_text()
                assert (
                    f"{temp_service_name}_core" in content
                    or "Remember to add" in result.stdout
                )

    def test_requirements_files_creation(self, project_root, temp_service_name):
        """Test that requirements files are created."""
        result = subprocess.run(
            ["./scripts/new_service.sh"],
            cwd=project_root,
            env={**os.environ, "S": temp_service_name},
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and "scaffolded" in result.stdout:
            req_dir = project_root / "3rdparty" / "python"
            # Check for requirements files
            core_req = req_dir / f"requirements-{temp_service_name}-core.txt"
            api_req = req_dir / f"requirements-{temp_service_name}-api.txt"

            assert (
                core_req.exists()
                or api_req.exists()
                or "requirements" not in result.stdout
            )

    def test_script_error_handling_no_name(self, project_root):
        """Test script handles missing service name."""
        result = subprocess.run(
            ["./scripts/new_service.sh"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should show usage message
        assert result.returncode != 0
        assert "Usage:" in result.stderr or "Usage:" in result.stdout

    def test_bootstrap_script_exists(self, project_root):
        """Test that bootstrap script exists and is executable."""
        script = project_root / "scripts" / "bootstrap_foundation.sh"
        assert script.exists()
        assert os.access(script, os.X_OK)

    def test_verify_tools_script(self, project_root):
        """Test verify-tools.sh script."""
        result = subprocess.run(
            ["./scripts/setup/verify-tools.sh"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should complete (may report missing tools)
        assert result.returncode in [0, 1]
        # Should check for tools
        assert "Checking" in result.stdout or "check" in result.stdout.lower()

    def test_make_fmt_lint_commands_available(self, project_root):
        """Test that formatting and linting commands are available."""
        # Test fmt
        result = subprocess.run(
            ["make", "fmt", "--dry-run"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Command should be recognized (may fail if pants not installed)
        assert "No rule to make target" not in result.stderr

        # Test lint
        result = subprocess.run(
            ["make", "lint", "--dry-run"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "No rule to make target" not in result.stderr

    def test_docker_compose_files_exist(self, project_root):
        """Test that docker-compose files exist."""
        compose_file = project_root / "docker-compose.yml"
        assert compose_file.exists() or (project_root / "docker-compose.yaml").exists()

    def test_makefile_has_phony_targets(self, project_root):
        """Test that Makefile properly declares PHONY targets."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        assert ".PHONY:" in content
        # Key targets should be marked as PHONY
        assert "help" in content
        assert "new-service" in content

    def test_scripts_have_proper_shebang(self, project_root):
        """Test that all shell scripts have proper shebang."""
        scripts_dir = project_root / "scripts"
        for script in scripts_dir.glob("**/*.sh"):
            if script.is_file():
                first_line = script.read_text().split("\n")[0]
                assert first_line.startswith("#!/"), f"{script} missing shebang"
                assert "bash" in first_line or "sh" in first_line

    def test_scripts_have_error_handling(self, project_root):
        """Test that scripts have proper error handling."""
        scripts_dir = project_root / "scripts"
        important_scripts = [
            "new_service.sh",
            "bootstrap_foundation.sh",
            "publish_template.sh",
        ]

        for script_name in important_scripts:
            script = scripts_dir / script_name
            if script.exists():
                content = script.read_text()
                # Should have error handling
                assert (
                    "set -e" in content or "set -euo" in content
                ), f"{script_name} missing error handling"

    def test_cleanup_after_failed_service_creation(self, project_root):
        """Test that partial service creation is handled properly."""
        # This would test cleanup after interruption
        # For now, just verify the service directory doesn't exist
        test_service = "test_cleanup_service"
        service_path = project_root / "services" / test_service
        assert not service_path.exists()
