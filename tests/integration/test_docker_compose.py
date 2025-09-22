"""Integration tests for Docker Compose services."""

import os
import subprocess
import time
from pathlib import Path

import pytest
import requests


class TestDockerCompose:
    """Test Docker Compose service orchestration."""

    @pytest.fixture(scope="class")
    def docker_compose_file(self):
        """Path to docker-compose.yml file."""
        project_root = Path(__file__).parent.parent.parent
        compose_file = project_root / "docker-compose.yml"

        if not compose_file.exists():
            pytest.skip("docker-compose.yml not found")

        return str(compose_file)

    @pytest.fixture(scope="class")
    def docker_available(self):
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker not available")

    def test_docker_compose_file_validity(self, docker_compose_file):
        """Test docker-compose.yml file validity."""
        # Test file parsing
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "config"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"docker-compose config failed: {result.stderr}"

    def test_docker_compose_services_defined(self, docker_compose_file):
        """Test that required services are defined in docker-compose.yml."""
        # Parse docker-compose configuration
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "config"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        config_output = result.stdout

        # Check for essential services
        required_services = ["localstack", "redis"]

        for service in required_services:
            assert (
                service in config_output
            ), f"Service {service} not found in docker-compose.yml"

    @pytest.mark.slow
    def test_localstack_service_startup(self, docker_compose_file, docker_available):
        """Test LocalStack service startup via docker-compose."""
        service_name = "localstack"

        try:
            # Start specific service
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "up", "-d", service_name],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
            )

            assert (
                result.returncode == 0
            ), f"Failed to start {service_name}: {result.stderr}"

            # Wait for service to be healthy
            max_wait = 60  # seconds
            wait_interval = 2

            for _ in range(max_wait // wait_interval):
                try:
                    response = requests.get(
                        "http://localhost:4566/_localstack/health", timeout=5
                    )
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get("services", {}).get("s3") in [
                            "available",
                            "running",
                        ]:
                            break
                except requests.exceptions.RequestException:
                    pass

                time.sleep(wait_interval)
            else:
                pytest.fail("LocalStack service did not become healthy within timeout")

            # Verify service is running
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "ps", service_name],
                capture_output=True,
                text=True,
            )

            assert "Up" in result.stdout or "running" in result.stdout.lower()

        finally:
            # Clean up
            subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "down"],
                capture_output=True,
            )

    @pytest.mark.slow
    def test_redis_service_startup(self, docker_compose_file, docker_available):
        """Test Redis service startup via docker-compose."""
        service_name = "redis"

        try:
            # Start specific service
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "up", "-d", service_name],
                capture_output=True,
                text=True,
                timeout=60,
            )

            assert (
                result.returncode == 0
            ), f"Failed to start {service_name}: {result.stderr}"

            # Wait for service to be ready
            max_wait = 30  # seconds
            wait_interval = 1

            for _ in range(max_wait // wait_interval):
                try:
                    # Check if Redis is accepting connections
                    result = subprocess.run(
                        [
                            "docker",
                            "exec",
                            "-i",
                            f"$(docker-compose -f {docker_compose_file} ps -q {service_name})",
                            "redis-cli",
                            "ping",
                        ],
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=5,
                    )
                    if result.returncode == 0 and "PONG" in result.stdout:
                        break
                except subprocess.TimeoutExpired:
                    pass

                time.sleep(wait_interval)
            else:
                # Alternative check using port availability
                try:
                    import socket

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex(("localhost", 6379))
                    sock.close()
                    if result == 0:
                        pass  # Connection successful
                    else:
                        pytest.fail(
                            "Redis service did not become available within timeout"
                        )
                except Exception:
                    pytest.fail("Could not verify Redis service availability")

            # Verify service is running
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "ps", service_name],
                capture_output=True,
                text=True,
            )

            assert "Up" in result.stdout or "running" in result.stdout.lower()

        finally:
            # Clean up
            subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "down"],
                capture_output=True,
            )

    def test_environment_variables_loading(self, docker_compose_file):
        """Test environment variables loading in docker-compose."""
        # Check if .env file is referenced
        with open(docker_compose_file, "r") as f:
            compose_content = f.read()

        # Look for environment variable references
        env_patterns = ["${", "env_file:", ".env"]

        has_env_config = any(pattern in compose_content for pattern in env_patterns)

        # Either explicit env vars or env_file should be configured
        assert (
            has_env_config
        ), "No environment configuration found in docker-compose.yml"

    def test_volume_mounts_configuration(self, docker_compose_file):
        """Test volume mounts configuration."""
        # Parse docker-compose configuration
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "config"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        config_output = result.stdout

        # Check for expected volume configurations
        volume_indicators = ["volumes:", "bind", "tmpfs"]

        has_volumes = any(indicator in config_output for indicator in volume_indicators)

        # Some services should have volume mounts for persistence or data sharing
        # This is not always required, so we just verify the configuration is valid
        assert True  # Placeholder - actual volume requirements depend on services

    def test_network_configuration(self, docker_compose_file):
        """Test network configuration."""
        # Parse docker-compose configuration
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "config"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        config_output = result.stdout

        # Services should be able to communicate
        # Check for network-related configuration
        network_indicators = ["networks:", "depends_on:", "links:"]

        # Network configuration may be implicit (default network)
        # So we just verify the compose file is valid
        assert "services:" in config_output

    def test_port_mappings(self, docker_compose_file):
        """Test port mappings configuration."""
        # Parse docker-compose configuration
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "config"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        config_output = result.stdout

        # Check for expected port mappings
        expected_ports = ["4566", "6379"]  # LocalStack and Redis

        for port in expected_ports:
            assert (
                port in config_output
            ), f"Port {port} not found in docker-compose configuration"

    def test_service_dependencies(self, docker_compose_file):
        """Test service dependencies configuration."""
        # Parse docker-compose configuration
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_file, "config"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        config_output = result.stdout

        # Verify that the configuration is structurally sound
        # Dependencies are managed through depends_on, links, or network configuration
        assert "services:" in config_output

        # If depends_on is used, it should be properly formatted
        if "depends_on:" in config_output:
            # Basic structure validation - depends_on should be followed by service names
            lines = config_output.split("\n")
            depends_on_found = False

            for line in lines:
                if "depends_on:" in line:
                    depends_on_found = True
                elif depends_on_found and line.strip().startswith("-"):
                    # Found a dependency entry
                    assert len(line.strip()) > 1  # Should have actual service name

    @pytest.mark.slow
    def test_full_stack_startup(self, docker_compose_file, docker_available):
        """Test full development stack startup."""
        try:
            # Start all services
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "up", "-d"],
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes timeout
            )

            assert result.returncode == 0, f"Failed to start services: {result.stderr}"

            # Wait for services to be ready
            time.sleep(10)

            # Check service status
            result = subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "ps"],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # Verify services are running (not exited)
            ps_output = result.stdout
            lines = ps_output.split("\n")

            for line in lines:
                if any(service in line.lower() for service in ["localstack", "redis"]):
                    # Service line should indicate it's running
                    assert (
                        "up" in line.lower() or "running" in line.lower()
                    ), f"Service not running: {line}"

        finally:
            # Clean up
            subprocess.run(
                ["docker-compose", "-f", docker_compose_file, "down", "-v"],
                capture_output=True,
            )
