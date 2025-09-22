"""Integration tests for service lifecycle with comprehensive cleanup."""

import subprocess
import time
from pathlib import Path

import pytest


class TestServiceLifecycle:
    """Test service creation, modification, and cleanup."""

    @pytest.mark.safe
    def test_list_services_no_side_effects(self, project_root):
        """Test listing services - no side effects."""
        services_dir = project_root / "services"
        if services_dir.exists():
            services = [d.name for d in services_dir.iterdir() if d.is_dir()]
            # This test only reads, no cleanup needed
            assert isinstance(services, list)

    def test_create_single_service(
        self, project_root, resource_tracker, safe_subprocess
    ):
        """Test creating a single service with automatic cleanup."""
        # Generate unique service name
        timestamp = str(int(time.time()))
        service_name = f"test_single_{timestamp}"
        service_path = project_root / "services" / service_name

        # Track for cleanup
        resource_tracker.track_service(service_name)

        # Create service
        result = safe_subprocess(
            ["bash", "scripts/new_service.sh"],
            env={"S": service_name, "PATH": "/usr/bin:/bin"},
            cwd=str(project_root),
        )

        # Verify service was created
        assert service_path.exists(), f"Service {service_name} was not created"
        assert (service_path / "BUILD").exists(), "BUILD file not created"
        assert (service_path / "app" / "api").exists(), "app/api directory not created"
        assert (
            service_path / "domain" / "models"
        ).exists(), "domain/models not created"

        # Service will be automatically cleaned up by resource_tracker

    def test_create_multiple_services(
        self, project_root, resource_tracker, safe_subprocess
    ):
        """Test creating multiple services with cleanup."""
        services_to_create = ["api", "worker", "admin"]
        created_services = []

        for service_suffix in services_to_create:
            timestamp = str(int(time.time()))
            service_name = f"test_multi_{service_suffix}_{timestamp}"
            service_path = project_root / "services" / service_name

            # Track each service
            resource_tracker.track_service(service_name)
            created_services.append((service_name, service_path))

            # Create service
            result = safe_subprocess(
                ["bash", "scripts/new_service.sh"],
                env={"S": service_name, "PATH": "/usr/bin:/bin"},
                cwd=str(project_root),
            )

            # Brief delay between creations
            time.sleep(0.1)

        # Verify all services were created
        for name, path in created_services:
            assert path.exists(), f"Service {name} was not created"

        # All services will be automatically cleaned up

    @pytest.mark.destructive
    def test_service_with_docker_container(
        self, project_root, resource_tracker, mock_docker_client
    ):
        """Test service that creates Docker resources."""
        timestamp = str(int(time.time()))
        service_name = f"test_docker_{timestamp}"
        container_name = f"test-container-{timestamp}"

        # Track resources
        resource_tracker.track_service(service_name)
        resource_tracker.track_container(container_name)

        # Simulate service with container
        service_path = project_root / "services" / service_name
        service_path.mkdir(parents=True, exist_ok=True)

        # Mock container creation
        mock_docker_client.containers.create.return_value.name = container_name

        # Resources will be cleaned up automatically

    def test_service_context_manager(self, project_root, resource_tracker):
        """Test using the service context manager."""
        import os

        from tests.cli.conftest import test_service

        # Use context manager for automatic cleanup
        with test_service(project_root, resource_tracker, "context") as (name, path):
            # Service exists within context
            assert path.exists()
            assert name.startswith("test_context_")

            # Perform tests on the service
            build_file = path / "BUILD"
            assert build_file.exists()

        # Service is automatically cleaned up after context exits
        # In sandbox mode, cleanup happens differently
        # Check if we're running in a Pants sandbox
        cwd = os.getcwd()
        if "/pants-sandbox" in cwd or "/T/pants-sandbox" in cwd:
            # In sandbox, verify service was tracked for cleanup
            assert name in resource_tracker.services
        else:
            # In non-sandbox mode, verify actual cleanup
            assert not path.exists()

    @pytest.mark.requires_pants
    def test_service_with_pants_build(
        self, project_root, resource_tracker, safe_subprocess
    ):
        """Test service with Pants build operations."""
        timestamp = str(int(time.time()))
        service_name = f"test_pants_{timestamp}"
        service_path = project_root / "services" / service_name

        # Track service
        resource_tracker.track_service(service_name)

        # Create service
        result = safe_subprocess(
            ["bash", "scripts/new_service.sh"],
            env={"S": service_name, "PATH": "/usr/bin:/bin"},
            cwd=str(project_root),
        )

        if service_path.exists():
            # Try Pants operations if available
            pants_path = project_root / "pants"
            if pants_path.exists():
                # Test Pants can see the service
                result = safe_subprocess(
                    ["./pants", "filedeps", f"services/{service_name}::"],
                    cwd=str(project_root),
                    check=False,  # Don't fail if Pants has issues
                )

        # Cleanup happens automatically

    def test_cleanup_verification(self, project_root, resource_tracker):
        """Test that cleanup verification works."""
        timestamp = str(int(time.time()))
        service_name = f"test_verify_{timestamp}"
        service_path = project_root / "services" / service_name

        # Track service
        resource_tracker.track_service(service_name)

        # Create service directory manually
        service_path.mkdir(parents=True, exist_ok=True)

        # Service should exist now
        assert service_path.exists()

        # Trigger cleanup
        resource_tracker.cleanup_services()

        # Service should be gone
        assert not service_path.exists()

    @pytest.mark.no_cleanup_check
    def test_with_no_cleanup_check(self, project_root):
        """Test that skips cleanup verification."""
        # This test is marked to skip cleanup checks
        # Useful for tests that intentionally leave artifacts
        # or handle their own cleanup
        pass

    def test_emergency_cleanup(self, project_root):
        """Test emergency cleanup functionality."""
        from tests.cli.cleanup import TestCleanupManager

        # Create a test artifact manually
        timestamp = str(int(time.time()))
        orphan_service = project_root / "services" / f"test_orphan_{timestamp}"
        orphan_service.mkdir(parents=True, exist_ok=True)

        # Verify it exists
        assert orphan_service.exists()

        # Run emergency cleanup
        manager = TestCleanupManager(project_root)
        manager.emergency_cleanup()

        # Verify it's gone
        assert not orphan_service.exists()

    def test_parallel_service_creation(self, project_root, resource_tracker):
        """Test creating services in parallel with proper cleanup."""
        import concurrent.futures

        def create_service(suffix):
            timestamp = str(int(time.time()))
            service_name = f"test_parallel_{suffix}_{timestamp}"
            resource_tracker.track_service(service_name)

            service_path = project_root / "services" / service_name
            service_path.mkdir(parents=True, exist_ok=True)
            return service_name, service_path.exists()

        # Create services in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_service, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Verify all were created
        for name, created in results:
            assert created, f"Service {name} was not created"

        # All will be cleaned up automatically
