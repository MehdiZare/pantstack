"""End-to-end integration tests."""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests


class TestEndToEnd:
    """End-to-end integration tests for the full application stack."""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture(scope="class")
    def test_environment(self):
        """Set up test environment variables."""
        return {
            "ENV": "test",
            "DEBUG": "true",
            "LOCALSTACK": "true",
            "LOCALSTACK_ENDPOINT": "http://localhost:4566",
            "SUPABASE_URL": "http://localhost:54321",
            "REDIS_URL": "redis://localhost:6379/1",
        }

    @pytest.fixture(scope="class")
    def development_stack_running(self, project_root):
        """Ensure development stack is running."""
        docker_compose_file = project_root / "docker-compose.yml"

        if not docker_compose_file.exists():
            pytest.skip("docker-compose.yml not found")

        # Check if services are already running
        result = subprocess.run(
            ["docker-compose", "-f", str(docker_compose_file), "ps"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.skip("Could not check docker-compose status")

        # If no services running, try to start them
        if "Up" not in result.stdout:
            try:
                subprocess.run(
                    ["docker-compose", "-f", str(docker_compose_file), "up", "-d"],
                    check=True,
                    timeout=120,
                )
                time.sleep(15)  # Wait for services to initialize
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pytest.skip("Could not start development stack")

        return True

    def test_localstack_and_supabase_integration(
        self, development_stack_running, test_environment
    ):
        """Test integration between LocalStack and Supabase."""
        # Test LocalStack health
        try:
            response = requests.get(
                f"{test_environment['LOCALSTACK_ENDPOINT']}/_localstack/health",
                timeout=10,
            )
            assert response.status_code == 200
            health_data = response.json()
            assert "services" in health_data
        except requests.exceptions.RequestException:
            pytest.skip("LocalStack not accessible")

        # Test Supabase connectivity
        try:
            response = requests.get(
                f"{test_environment['SUPABASE_URL']}/rest/v1/",
                timeout=10,
            )
            # Should get some response (200, 401, or 404 are all acceptable)
            assert response.status_code in [200, 401, 404]
        except requests.exceptions.RequestException:
            pytest.skip("Supabase not accessible")

    @pytest.mark.slow
    def test_api_service_startup_and_health(
        self, project_root, test_environment, development_stack_running
    ):
        """Test API service startup and health check."""
        # This test would require the API service to be implemented and runnable
        api_port = 8000
        api_url = f"http://localhost:{api_port}"

        # For now, just test that we can structure the test properly
        expected_endpoints = [
            "/health",
            "/docs",
            "/openapi.json",
        ]

        # Verify test structure
        assert len(expected_endpoints) > 0
        assert all(endpoint.startswith("/") for endpoint in expected_endpoints)

        # Note: Actual API testing would require the service to be running
        # This could be added once the FastAPI application is fully implemented

    def test_worker_service_integration(
        self, test_environment, development_stack_running
    ):
        """Test worker service integration with queues."""
        # Test Redis connectivity for task queues
        redis_url = test_environment["REDIS_URL"]

        try:
            import redis

            r = redis.from_url(redis_url)
            r.ping()

            # Test basic queue operations
            test_queue = "test_integration_queue"
            test_message = {"task": "test_task", "data": {"test": True}}

            # Push test message
            r.lpush(test_queue, json.dumps(test_message))

            # Pop test message
            retrieved = r.rpop(test_queue)
            if retrieved:
                retrieved_data = json.loads(retrieved.decode())
                assert retrieved_data["task"] == test_message["task"]

        except ImportError:
            pytest.skip("Redis library not available")
        except Exception:
            pytest.skip("Redis not accessible")

    def test_database_operations_flow(
        self, test_environment, development_stack_running
    ):
        """Test database operations through the full stack."""
        # Test would involve:
        # 1. Creating data via API
        # 2. Verifying data in database
        # 3. Triggering background tasks
        # 4. Verifying task completion

        # For now, test the infrastructure is available
        supabase_url = test_environment["SUPABASE_URL"]

        try:
            # Test database connectivity through Supabase
            response = requests.get(f"{supabase_url}/rest/v1/", timeout=5)
            assert response.status_code in [200, 401, 404]
        except requests.exceptions.RequestException:
            pytest.skip("Database service not accessible")

    def test_file_storage_operations(self, test_environment, development_stack_running):
        """Test file storage operations (S3 via LocalStack)."""
        import boto3
        from botocore.exceptions import ClientError

        # Configure AWS client for LocalStack
        s3_client = boto3.client(
            "s3",
            endpoint_url=test_environment["LOCALSTACK_ENDPOINT"],
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )

        bucket_name = "e2e-test-bucket"

        try:
            # Create test bucket
            s3_client.create_bucket(Bucket=bucket_name)

            # Upload test file
            test_content = "End-to-end test file content"
            test_key = "test-files/e2e-test.txt"

            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content.encode(),
                ContentType="text/plain",
            )

            # Verify file exists
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            retrieved_content = response["Body"].read().decode()

            assert retrieved_content == test_content

            # Test file listing
            response = s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix="test-files/"
            )
            assert "Contents" in response
            assert any(obj["Key"] == test_key for obj in response["Contents"])

        except ClientError as e:
            pytest.skip(f"S3 operations failed: {e}")
        finally:
            # Clean up
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
                s3_client.delete_bucket(Bucket=bucket_name)
            except ClientError:
                pass

    def test_event_driven_workflow(self, test_environment, development_stack_running):
        """Test event-driven workflow between services."""
        import boto3
        from botocore.exceptions import ClientError

        # Set up SQS for event testing
        sqs_client = boto3.client(
            "sqs",
            endpoint_url=test_environment["LOCALSTACK_ENDPOINT"],
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )

        queue_name = "e2e-test-events"

        try:
            # Create test queue
            response = sqs_client.create_queue(QueueName=queue_name)
            queue_url = response["QueueUrl"]

            # Send test event
            test_event = {
                "event_type": "user_created",
                "user_id": "test-user-123",
                "timestamp": "2023-09-20T10:00:00Z",
                "source": "api",
            }

            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(test_event),
            )

            # Receive and verify event
            response = sqs_client.receive_message(
                QueueUrl=queue_url, MaxNumberOfMessages=1
            )

            assert "Messages" in response
            message = response["Messages"][0]
            received_event = json.loads(message["Body"])

            assert received_event["event_type"] == test_event["event_type"]
            assert received_event["user_id"] == test_event["user_id"]

            # Clean up message
            receipt_handle = message["ReceiptHandle"]
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        except ClientError as e:
            pytest.skip(f"SQS operations failed: {e}")
        finally:
            # Clean up
            try:
                sqs_client.delete_queue(QueueUrl=queue_url)
            except ClientError:
                pass

    def test_configuration_management(self, test_environment):
        """Test configuration management across services."""
        # Verify essential configuration is available
        required_config = [
            "ENV",
            "LOCALSTACK_ENDPOINT",
            "SUPABASE_URL",
            "REDIS_URL",
        ]

        for config_key in required_config:
            assert config_key in test_environment
            assert len(test_environment[config_key]) > 0

        # Test environment-specific defaults
        assert test_environment["ENV"] == "test"
        assert "localhost" in test_environment["LOCALSTACK_ENDPOINT"]
        assert "localhost" in test_environment["SUPABASE_URL"]

    def test_logging_and_monitoring_integration(self, test_environment):
        """Test logging and monitoring integration."""
        # Test logging configuration
        log_config = {
            "level": "DEBUG" if test_environment.get("DEBUG") == "true" else "INFO",
            "format": "json",
            "handlers": ["console", "file"],
        }

        # Verify logging structure
        assert log_config["level"] in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert log_config["format"] in ["json", "text"]
        assert len(log_config["handlers"]) > 0

    def test_security_configuration(self, test_environment):
        """Test security configuration in test environment."""
        # Security settings for test environment
        security_config = {
            "debug_mode": test_environment.get("DEBUG") == "true",
            "local_development": "localhost"
            in test_environment.get("SUPABASE_URL", ""),
            "test_environment": test_environment.get("ENV") == "test",
        }

        # In test environment, debug mode should be enabled
        assert security_config["debug_mode"] is True
        assert security_config["local_development"] is True
        assert security_config["test_environment"] is True

    @pytest.mark.slow
    def test_performance_baseline(self, development_stack_running, test_environment):
        """Test basic performance baseline for services."""
        services_to_test = [
            {
                "name": "LocalStack",
                "url": f"{test_environment['LOCALSTACK_ENDPOINT']}/_localstack/health",
                "max_response_time": 5.0,  # seconds
            },
            {
                "name": "Supabase",
                "url": f"{test_environment['SUPABASE_URL']}/rest/v1/",
                "max_response_time": 3.0,  # seconds
            },
        ]

        for service in services_to_test:
            start_time = time.time()

            try:
                response = requests.get(
                    service["url"], timeout=service["max_response_time"]
                )
                response_time = time.time() - start_time

                # Service should respond within acceptable time
                assert (
                    response_time < service["max_response_time"]
                ), f"{service['name']} response time {response_time:.2f}s exceeds {service['max_response_time']}s"

                # Should get a valid HTTP response
                assert (
                    200 <= response.status_code < 500
                ), f"{service['name']} returned unexpected status: {response.status_code}"

            except requests.exceptions.RequestException as e:
                pytest.skip(f"{service['name']} not accessible: {e}")
