"""Cleanup utilities for CLI testing."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

import docker


class TestCleanupManager:
    """Comprehensive cleanup manager for test artifacts."""

    # Prefixes that identify test resources
    TEST_PREFIXES = ["test_", "temp_", "tmp_test_"]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docker_client = None
        self._init_docker()

    def _init_docker(self):
        """Initialize Docker client if available."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
        except Exception:
            self.docker_client = None

    def find_test_services(self) -> List[Path]:
        """Find all test services in the services directory."""
        services_dir = self.project_root / "services"
        if not services_dir.exists():
            return []

        test_services = []
        for prefix in self.TEST_PREFIXES:
            test_services.extend(services_dir.glob(f"{prefix}*"))

        return test_services

    def clean_test_services(self) -> int:
        """Remove all test services."""
        test_services = self.find_test_services()
        removed = 0

        for service_path in test_services:
            try:
                shutil.rmtree(service_path)
                removed += 1
                print(f"  ✓ Removed service: {service_path.name}")
            except Exception as e:
                print(f"  ✗ Failed to remove {service_path.name}: {e}")

        return removed

    def find_test_containers(self) -> List[str]:
        """Find all test Docker containers."""
        if not self.docker_client:
            return []

        test_containers = []
        try:
            all_containers = self.docker_client.containers.list(all=True)
            for container in all_containers:
                for prefix in self.TEST_PREFIXES:
                    if container.name.startswith(prefix):
                        test_containers.append(container.name)
                        break
        except Exception:
            pass

        return test_containers

    def clean_test_containers(self) -> int:
        """Remove all test Docker containers."""
        if not self.docker_client:
            return 0

        test_containers = self.find_test_containers()
        removed = 0

        for container_name in test_containers:
            try:
                container = self.docker_client.containers.get(container_name)
                container.stop(timeout=5)
                container.remove(force=True)
                removed += 1
                print(f"  ✓ Removed container: {container_name}")
            except Exception as e:
                print(f"  ✗ Failed to remove {container_name}: {e}")

        return removed

    def find_test_stacks(self) -> List[str]:
        """Find all test Pulumi stacks."""
        test_stacks = []

        try:
            result = subprocess.run(
                ["pulumi", "stack", "ls", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                import json

                stacks = json.loads(result.stdout)
                for stack in stacks:
                    stack_name = stack.get("name", "")
                    for prefix in self.TEST_PREFIXES:
                        if prefix in stack_name:
                            test_stacks.append(stack_name)
                            break
        except Exception:
            pass

        return test_stacks

    def clean_test_stacks(self) -> int:
        """Remove all test Pulumi stacks."""
        test_stacks = self.find_test_stacks()
        removed = 0

        for stack_name in test_stacks:
            try:
                result = subprocess.run(
                    ["pulumi", "stack", "rm", stack_name, "--force", "--yes"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    removed += 1
                    print(f"  ✓ Removed stack: {stack_name}")
                else:
                    print(f"  ✗ Failed to remove {stack_name}: {result.stderr}")
            except Exception as e:
                print(f"  ✗ Failed to remove {stack_name}: {e}")

        return removed

    def clean_pants_cache(self) -> bool:
        """Clean Pants build cache."""
        pants_path = self.project_root / "pants"
        if not pants_path.exists():
            return False

        try:
            result = subprocess.run(
                ["./pants", "--no-watch-filesystem", "gc"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                print("  ✓ Cleaned Pants cache")
                return True
        except Exception as e:
            print(f"  ✗ Failed to clean Pants cache: {e}")

        return False

    def find_test_processes(self) -> List[int]:
        """Find test-related processes."""
        test_processes = []

        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
            )

            for line in result.stdout.split("\n"):
                # Look for test-related processes
                if any(prefix in line for prefix in self.TEST_PREFIXES):
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            test_processes.append(pid)
                        except ValueError:
                            pass
        except Exception:
            pass

        return test_processes

    def clean_test_processes(self) -> int:
        """Kill test-related processes."""
        test_processes = self.find_test_processes()
        killed = 0

        for pid in test_processes:
            try:
                os.kill(pid, 15)  # SIGTERM
                killed += 1
                print(f"  ✓ Killed process: {pid}")
            except (ProcessLookupError, PermissionError) as e:
                print(f"  ✗ Failed to kill {pid}: {e}")

        return killed

    def verify_cleanup(self) -> Dict[str, List]:
        """Verify that all test artifacts have been cleaned."""
        remaining = {
            "services": self.find_test_services(),
            "containers": self.find_test_containers(),
            "stacks": self.find_test_stacks(),
            "processes": self.find_test_processes(),
        }

        # Filter out empty lists
        remaining = {k: v for k, v in remaining.items() if v}

        return remaining

    def clean_all(self) -> Dict[str, int]:
        """Clean all test artifacts."""
        print("🧹 Cleaning all test artifacts...")

        results = {
            "services": self.clean_test_services(),
            "containers": self.clean_test_containers(),
            "stacks": self.clean_test_stacks(),
            "processes": self.clean_test_processes(),
        }

        # Clean Pants cache
        if self.clean_pants_cache():
            results["pants_cache"] = 1

        return results

    def emergency_cleanup(self) -> None:
        """Emergency cleanup - more aggressive."""
        print("🚨 Emergency cleanup - removing all test artifacts...")

        # Services - force remove
        services_dir = self.project_root / "services"
        if services_dir.exists():
            for prefix in self.TEST_PREFIXES:
                subprocess.run(
                    [
                        "find",
                        str(services_dir),
                        "-name",
                        f"{prefix}*",
                        "-type",
                        "d",
                        "-exec",
                        "rm",
                        "-rf",
                        "{}",
                        "+",
                    ],
                    capture_output=True,
                )

        # Docker - force remove
        if self.docker_client:
            try:
                for prefix in self.TEST_PREFIXES:
                    subprocess.run(
                        ["docker", "ps", "-a", "--filter", f"name={prefix}", "-q"],
                        capture_output=True,
                    )
                    subprocess.run(
                        [
                            "docker",
                            "rm",
                            "-f",
                            f"$(docker ps -a --filter name={prefix} -q)",
                        ],
                        shell=True,
                        capture_output=True,
                    )
            except Exception:
                pass

        # Pulumi stacks - force remove
        try:
            for prefix in self.TEST_PREFIXES:
                subprocess.run(
                    f"pulumi stack ls --json | jq -r '.[] | select(.name | contains(\"{prefix}\")) | .name' | xargs -I {{}} pulumi stack rm {{}} --force --yes",
                    shell=True,
                    capture_output=True,
                )
        except Exception:
            pass


def cleanup_after_test(project_root: Path, resources: Dict[str, List]) -> None:
    """Clean up specific resources after a test."""
    manager = TestCleanupManager(project_root)

    for resource_type, items in resources.items():
        if resource_type == "services":
            for service_name in items:
                service_path = project_root / "services" / service_name
                if service_path.exists():
                    shutil.rmtree(service_path, ignore_errors=True)

        elif resource_type == "containers":
            if manager.docker_client:
                for container_name in items:
                    try:
                        container = manager.docker_client.containers.get(container_name)
                        container.stop(timeout=5)
                        container.remove(force=True)
                    except Exception:
                        pass

        elif resource_type == "stacks":
            for stack_name in items:
                subprocess.run(
                    ["pulumi", "stack", "rm", stack_name, "--force", "--yes"],
                    capture_output=True,
                    timeout=30,
                )


def assert_no_test_artifacts(project_root: Path) -> None:
    """Assert that no test artifacts remain."""
    manager = TestCleanupManager(project_root)
    remaining = manager.verify_cleanup()

    if remaining:
        artifact_list = []
        for resource_type, items in remaining.items():
            if items:
                if isinstance(items[0], Path):
                    items = [str(item) for item in items]
                artifact_list.append(f"{resource_type}: {items}")

        raise AssertionError(
            "Test artifacts found after cleanup:\n" + "\n".join(artifact_list)
        )
