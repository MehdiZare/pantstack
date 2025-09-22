"""Pytest configuration and fixtures for CLI testing with automatic cleanup."""

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple
from unittest.mock import Mock

import pytest
from click.testing import CliRunner  # pants: no-infer-dep


class ResourceTracker:
    """Track all resources created during tests for cleanup."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services: List[str] = []
        self.stacks: List[Tuple[str, str]] = []  # (stack_name, env)
        self.docker_containers: List[str] = []
        self.temp_files: List[Path] = []
        self.processes: List[int] = []
        self.pulumi_stacks: List[str] = []

    def track_service(self, service_name: str) -> None:
        """Track a created service for cleanup."""
        if service_name and service_name not in self.services:
            self.services.append(service_name)

    def track_stack(self, stack_name: str, env: str) -> None:
        """Track a created Pulumi stack for cleanup."""
        if stack_name and (stack_name, env) not in self.stacks:
            self.stacks.append((stack_name, env))

    def track_container(self, container_name: str) -> None:
        """Track a Docker container for cleanup."""
        if container_name and container_name not in self.docker_containers:
            self.docker_containers.append(container_name)

    def track_temp_file(self, file_path: Path) -> None:
        """Track a temporary file for cleanup."""
        if file_path and file_path not in self.temp_files:
            self.temp_files.append(file_path)

    def track_process(self, pid: int) -> None:
        """Track a process for cleanup."""
        if pid and pid not in self.processes:
            self.processes.append(pid)

    def cleanup_services(self) -> int:
        """Clean up all tracked services."""
        cleaned = 0
        for service_name in self.services:
            service_path = self.project_root / "services" / service_name
            if service_path.exists():
                shutil.rmtree(service_path, ignore_errors=True)
                cleaned += 1
        self.services.clear()
        return cleaned

    def cleanup_stacks(self) -> int:
        """Clean up all tracked Pulumi stacks."""
        cleaned = 0
        for stack_name, env in self.stacks:
            try:
                # Try to remove stack
                result = subprocess.run(
                    [
                        "pulumi",
                        "stack",
                        "rm",
                        f"{stack_name}-{env}",
                        "--force",
                        "--yes",
                    ],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    cleaned += 1
            except (subprocess.TimeoutExpired, Exception):
                pass
        self.stacks.clear()
        return cleaned

    def cleanup_containers(self) -> int:
        """Clean up all tracked Docker containers."""
        cleaned = 0
        for container_name in self.docker_containers:
            try:
                # Stop container
                subprocess.run(
                    ["docker", "stop", container_name],
                    capture_output=True,
                    timeout=10,
                )
                # Remove container
                result = subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    cleaned += 1
            except (subprocess.TimeoutExpired, Exception):
                pass
        self.docker_containers.clear()
        return cleaned

    def cleanup_temp_files(self) -> int:
        """Clean up all tracked temporary files."""
        cleaned = 0
        for file_path in self.temp_files:
            if file_path.exists():
                if file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=True)
                else:
                    file_path.unlink(missing_ok=True)
                cleaned += 1
        self.temp_files.clear()
        return cleaned

    def cleanup_processes(self) -> int:
        """Kill all tracked processes."""
        cleaned = 0
        for pid in self.processes:
            try:
                os.kill(pid, 15)  # SIGTERM
                cleaned += 1
            except (ProcessLookupError, PermissionError):
                pass
        self.processes.clear()
        return cleaned

    def cleanup_all(self) -> Dict[str, int]:
        """Clean up all tracked resources."""
        results = {
            "processes": self.cleanup_processes(),
            "containers": self.cleanup_containers(),
            "stacks": self.cleanup_stacks(),
            "services": self.cleanup_services(),
            "temp_files": self.cleanup_temp_files(),
        }

        # Also clean up orphaned test resources
        self._cleanup_orphaned_resources()

        return results

    def _cleanup_orphaned_resources(self) -> None:
        """Clean up any orphaned test resources not tracked."""
        # Clean orphaned test services
        services_dir = self.project_root / "services"
        if services_dir.exists():
            for service_dir in services_dir.glob("test_*"):
                shutil.rmtree(service_dir, ignore_errors=True)
            for service_dir in services_dir.glob("temp_*"):
                shutil.rmtree(service_dir, ignore_errors=True)

        # Clean Pants cache if needed
        pants_path = self.project_root / "pants"
        if pants_path.exists():
            subprocess.run(
                ["./pants", "--no-watch-filesystem", "gc"],
                cwd=str(self.project_root),
                capture_output=True,
                timeout=30,
            )


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def resource_tracker(project_root) -> Generator[ResourceTracker, None, None]:
    """Provide resource tracker with automatic cleanup."""
    tracker = ResourceTracker(project_root)

    yield tracker

    # Cleanup all resources at end of session
    results = tracker.cleanup_all()
    total_cleaned = sum(results.values())
    if total_cleaned > 0:
        print(f"\n✨ Cleaned up {total_cleaned} test resources")
        for resource_type, count in results.items():
            if count > 0:
                print(f"  - {resource_type}: {count}")


@pytest.fixture
def isolated_project(tmp_path) -> Generator[Path, None, None]:
    """Create an isolated project copy for testing."""
    project_root = Path(__file__).parent.parent.parent
    isolated_path = tmp_path / "isolated_project"

    # Create minimal project structure
    isolated_path.mkdir()
    (isolated_path / "services").mkdir()
    (isolated_path / "scripts").mkdir()
    (isolated_path / "tests").mkdir()

    # Copy essential scripts
    scripts_to_copy = ["new_service.sh"]
    for script in scripts_to_copy:
        src = project_root / "scripts" / script
        if src.exists():
            dst = isolated_path / "scripts" / script
            shutil.copy2(src, dst)
            dst.chmod(0o755)

    # Copy Makefile
    makefile = project_root / "Makefile"
    if makefile.exists():
        shutil.copy2(makefile, isolated_path / "Makefile")

    # Initialize git repo (some commands may require it)
    subprocess.run(
        ["git", "init"],
        cwd=str(isolated_path),
        capture_output=True,
    )

    yield isolated_path

    # Cleanup is automatic when tmp_path is destroyed


@pytest.fixture
def cli_runner(resource_tracker) -> Generator[CliRunner, None, None]:
    """Enhanced CLI runner with automatic resource tracking."""
    runner = CliRunner(mix_stderr=False)

    # Add tracking method to runner
    def track_resource(resource_type: str, name: str):
        if resource_type == "service":
            resource_tracker.track_service(name)
        elif resource_type == "stack":
            resource_tracker.track_stack(name, "test")
        elif resource_type == "container":
            resource_tracker.track_container(name)
        elif resource_type == "temp_file":
            resource_tracker.track_temp_file(Path(name))
        elif resource_type == "process":
            resource_tracker.track_process(int(name))

    runner.track = track_resource  # type: ignore

    yield runner


@contextmanager
def test_service(
    project_root: Path, resource_tracker: ResourceTracker, name_suffix: str = "test"
) -> Generator[Tuple[str, Path], None, None]:
    """Context manager for test service creation and cleanup."""
    # Generate unique service name
    timestamp = str(int(time.time()))
    unique_id = uuid.uuid4().hex[:8]
    service_name = f"test_{name_suffix}_{timestamp}_{unique_id}"
    service_path = project_root / "services" / service_name

    # Track for cleanup
    resource_tracker.track_service(service_name)

    try:
        # Create service
        env = os.environ.copy()
        env["S"] = service_name

        result = subprocess.run(
            ["./scripts/new_service.sh"],
            env=env,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if service_path.exists():
            yield service_name, service_path
        else:
            pytest.fail(f"Failed to create service: {result.stderr}")

    finally:
        # Cleanup is handled by resource_tracker
        pass


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing without Docker."""
    mock = Mock()
    mock.containers.list.return_value = []
    mock.images.list.return_value = []
    return mock


@pytest.fixture
def test_env_vars():
    """Set test environment variables."""
    original_env = os.environ.copy()

    # Set test environment
    test_vars = {
        "ENVIRONMENT": "test",
        "TEST_MODE": "true",
        "AWS_DEFAULT_REGION": "us-east-1",
        "LOCALSTACK_ENDPOINT": "http://localhost:4566",
    }

    for key, value in test_vars.items():
        os.environ[key] = value

    yield test_vars

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def cleanup_verification(resource_tracker, request):
    """Verify cleanup after each test."""
    yield

    # Skip verification for tests marked with no_cleanup_check
    if "no_cleanup_check" in request.keywords:
        return

    # Check for orphaned resources after test
    project_root = resource_tracker.project_root
    services_dir = project_root / "services"

    if services_dir.exists():
        orphaned = list(services_dir.glob("test_*")) + list(services_dir.glob("temp_*"))
        if orphaned:
            # Clean them up
            for orphan in orphaned:
                shutil.rmtree(orphan, ignore_errors=True)

            # Report the issue
            orphan_names = [p.name for p in orphaned]
            import warnings

            warnings.warn(f"Found orphaned test resources: {orphan_names}", UserWarning)


@pytest.fixture
def safe_subprocess():
    """Provide safe subprocess execution with timeout and cleanup."""
    processes = []

    def run_command(cmd, **kwargs):
        """Run command with safety features."""
        defaults = {
            "capture_output": True,
            "text": True,
            "timeout": 30,
        }
        defaults.update(kwargs)

        try:
            proc = subprocess.run(cmd, **defaults)
            if proc.returncode != 0 and not kwargs.get("check", True):
                pass  # Don't raise if check=False
            return proc
        except subprocess.TimeoutExpired as e:
            # Kill the process
            if hasattr(e, "process") and e.process:
                e.process.kill()
            raise
        finally:
            # Track for cleanup
            if "proc" in locals() and hasattr(proc, "pid"):
                processes.append(proc.pid)

    yield run_command

    # Cleanup any lingering processes
    for pid in processes:
        try:
            os.kill(pid, 15)  # SIGTERM
        except (ProcessLookupError, PermissionError):
            pass


# Pytest markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "no_cleanup_check: Skip cleanup verification for this test"
    )
    config.addinivalue_line("markers", "destructive: Test that modifies the system")
    config.addinivalue_line("markers", "safe: Test with no side effects")
    config.addinivalue_line(
        "markers", "requires_docker: Test requires Docker to be running"
    )
    config.addinivalue_line(
        "markers", "requires_pants: Test requires Pants build system"
    )
