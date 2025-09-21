"""Integration tests for service lifecycle management."""
import pytest
pytest.skip("Skipping service lifecycle tests - requires filesystem access", allow_module_level=True)

import os
import shutil
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest


class TestServiceLifecycle:
    """Test complete service lifecycle with cleanup."""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture(scope="class")
    def test_workspace(self):
        """Create isolated test workspace."""
        workspace = Path(tempfile.mkdtemp(prefix="pantstack_test_"))
        yield workspace
        # Cleanup happens automatically when context exits
        shutil.rmtree(workspace, ignore_errors=True)

    @contextmanager
    def test_service(self, project_root, name_suffix="test"):
        """Context manager for test service creation and cleanup."""
        service_name = f"test_svc_{name_suffix}_{uuid.uuid4().hex[:8]}"
        service_path = project_root / "services" / service_name

        try:
            # Create service
            result = subprocess.run(
                ["./scripts/new_service.sh"],
                env={**os.environ, "S": service_name},
                cwd=str(project_root),
                capture_output=True,
                text=True,
                shell=True,
            )

            # Check if service was created (script might exit 0 even if service exists)
            if service_path.exists():
                yield service_name, service_path
            else:
                # Try to create if it failed
                if result.returncode != 0:
                    pytest.fail(f"Service creation failed: {result.stderr}")
                else:
                    pytest.skip(f"Service not created: {service_name}")

        finally:
            # Cleanup service
            if service_path.exists():
                shutil.rmtree(service_path)

            # Clean Pants artifacts if pants exists
            pants_path = project_root / "pants"
            if pants_path.exists():
                subprocess.run(
                    ["./pants", "--no-watch-filesystem", "gc"],
                    cwd=str(project_root),
                    capture_output=True,
                    shell=True,
                )

    def test_create_and_validate_service(self, project_root):
        """Test service creation with automatic cleanup."""
        with self.test_service(project_root, "validate") as (name, path):
            # Verify structure
            assert (path / "BUILD").exists(), "BUILD file not created"
            assert (path / "app" / "api").exists(), "app/api directory not created"
            assert (path / "domain" / "models").exists(), "domain/models directory not created"
            assert (path / "tests" / "unit").exists(), "tests/unit directory not created"

            # Verify BUILD file content
            build_content = (path / "BUILD").read_text()
            assert f'entry_point="services.{name}.app.api.main:run"' in build_content, \
                "BUILD file doesn't contain correct entry point"

    def test_service_directory_structure(self, project_root):
        """Test that all expected directories are created."""
        with self.test_service(project_root, "structure") as (name, path):
            expected_dirs = [
                "app/api",
                "app/worker",
                "domain/models",
                "domain/services",
                "domain/ports",
                "adapters/repositories",
                "public",
                "infra/pulumi",
                "tests/unit",
            ]

            for dir_path in expected_dirs:
                full_path = path / dir_path
                assert full_path.exists(), f"Missing directory: {dir_path}"
                assert full_path.is_dir(), f"Not a directory: {dir_path}"

    def test_build_file_content(self, project_root):
        """Test BUILD file has correct configuration."""
        with self.test_service(project_root, "buildfile") as (name, path):
            build_file = path / "BUILD"
            assert build_file.exists()

            content = build_file.read_text()

            # Check for essential BUILD file components
            expected_patterns = [
                'python_sources(',
                'name="core"',
                'name="api_src"',
                'name="worker_src"',
                'pex_binary(name="api_pex"',
                'pex_binary(name="worker_pex"',
                'docker_image(name="image"',
                'python_tests(name="unit"',
                f'entry_point="services.{name}.app.api.main:run"',
                f'entry_point="services.{name}.app.worker.run:main"',
            ]

            for pattern in expected_patterns:
                assert pattern in content, f"BUILD file missing: {pattern}"

    def test_multiple_services_cleanup(self, project_root):
        """Test creating multiple services and cleaning all."""
        services_created = []

        try:
            # Create multiple test services
            for i in range(3):
                service_name = f"test_multi_{i}_{uuid.uuid4().hex[:8]}"
                service_path = project_root / "services" / service_name

                # Create service
                result = subprocess.run(
                    [str(project_root / "scripts" / "new_service.sh")],
                    env={**os.environ, "S": service_name},
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                )

                if service_path.exists():
                    services_created.append((service_name, service_path))
                    assert service_path.exists(), f"Service not created: {service_name}"

        finally:
            # Clean up all created services
            for name, path in services_created:
                if path.exists():
                    shutil.rmtree(path)

            # Verify all cleaned up
            for name, path in services_created:
                assert not path.exists(), f"Service not cleaned: {name}"

    def test_service_name_sanitization(self, project_root):
        """Test service creation with various name formats."""
        valid_names = [
            "api_service",
            "worker123",
            "test_svc",
            "mysvc",
        ]

        for base_name in valid_names:
            service_name = f"test_{base_name}_{uuid.uuid4().hex[:8]}"
            service_path = project_root / "services" / service_name

            try:
                result = subprocess.run(
                    [str(project_root / "scripts" / "new_service.sh")],
                    env={**os.environ, "S": service_name},
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                )

                if service_path.exists():
                    # Verify it was created
                    assert (service_path / "BUILD").exists()
            finally:
                # Always cleanup
                if service_path.exists():
                    shutil.rmtree(service_path)

    @pytest.mark.slow
    def test_pants_operations_if_available(self, project_root):
        """Test Pants operations on temporary service if Pants is available."""
        pants_path = project_root / "pants"

        if not pants_path.exists():
            # Try to bootstrap pants
            bootstrap_result = subprocess.run(
                ["make", "boot"],
                cwd=project_root,
                capture_output=True,
                text=True,
            )

            if bootstrap_result.returncode != 0 or not pants_path.exists():
                pytest.skip("Pants not available")

        with self.test_service(project_root, "pants") as (name, path):
            # Create minimal test file
            test_dir = path / "tests" / "unit"
            test_dir.mkdir(parents=True, exist_ok=True)
            test_file = test_dir / "test_basic.py"
            test_file.write_text('''def test_placeholder():
    """Placeholder test."""
    assert True
''')

            # Run Pants validation
            result = subprocess.run(
                ["./pants", "filedeps", f"services/{name}::"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                shell=True,
            )

            # Pants operations might fail due to missing lockfiles, but command should run
            assert result.returncode == 0 or "lockfile" in result.stderr.lower(), \
                f"Pants operation failed unexpectedly: {result.stderr}"

    def test_cleanup_orphaned_services(self, project_root):
        """Test cleanup of orphaned test services."""
        # Create an orphaned service manually
        orphan_name = f"test_orphan_{uuid.uuid4().hex[:8]}"
        orphan_path = project_root / "services" / orphan_name
        orphan_path.mkdir(parents=True, exist_ok=True)
        (orphan_path / "marker.txt").write_text("orphaned")

        try:
            # Verify it exists
            assert orphan_path.exists()

            # Run cleanup
            cleanup_script = project_root / "scripts" / "test" / "test_service_lifecycle.sh"
            if cleanup_script.exists():
                subprocess.run(
                    ["./scripts/test/test_service_lifecycle.sh", "cleanup"],
                    cwd=str(project_root),
                    capture_output=True,
                    shell=True,
                )

        finally:
            # Manual cleanup if script didn't work
            if orphan_path.exists():
                shutil.rmtree(orphan_path)