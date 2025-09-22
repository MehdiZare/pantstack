"""Helper utilities for e2e testing."""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class DockerComposeManager:
    """Manage Docker Compose stack for testing."""

    def __init__(self, project_root: Path = None):
        """Initialize Docker Compose manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.compose_file = self.project_root / "docker-compose.yml"

    def is_running(self) -> bool:
        """Check if Docker Compose stack is running.

        Returns:
            True if stack is running, False otherwise
        """
        result = subprocess.run(
            ["docker-compose", "ps"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        return "api" in result.stdout and "Up" in result.stdout

    def start(self, timeout: int = 180) -> bool:
        """Start Docker Compose stack.

        Args:
            timeout: Maximum time to wait for startup

        Returns:
            True if started successfully, False otherwise
        """
        if not self.compose_file.exists():
            print(f"Docker Compose file not found: {self.compose_file}")
            return False

        if self.is_running():
            print("Docker Compose stack is already running")
            return True

        print("Starting Docker Compose stack...")
        try:
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=self.project_root,
                check=True,
                timeout=timeout,
            )
            print("Docker Compose stack started, waiting for services...")
            time.sleep(30)  # Wait for services to initialize
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to start Docker Compose stack: {e}")
            return False

    def stop(self) -> bool:
        """Stop Docker Compose stack.

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            subprocess.run(
                ["docker-compose", "down"],
                cwd=self.project_root,
                check=True,
                timeout=60,
            )
            print("Docker Compose stack stopped")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to stop Docker Compose stack: {e}")
            return False

    def restart_service(self, service: str) -> bool:
        """Restart a specific service.

        Args:
            service: Service name to restart

        Returns:
            True if restarted successfully, False otherwise
        """
        try:
            subprocess.run(
                ["docker-compose", "restart", service],
                cwd=self.project_root,
                check=True,
                timeout=60,
            )
            print(f"Service {service} restarted")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to restart service {service}: {e}")
            return False

    def get_logs(self, service: str = None, lines: int = 100) -> str:
        """Get logs from Docker Compose services.

        Args:
            service: Specific service to get logs from (None for all)
            lines: Number of lines to retrieve

        Returns:
            Log output
        """
        cmd = ["docker-compose", "logs", f"--tail={lines}"]
        if service:
            cmd.append(service)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return ""


class ServiceHealthChecker:
    """Check health of various services."""

    def __init__(self, timeout: int = 5):
        """Initialize health checker.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    def check_api(self, url: str = "http://localhost:8000") -> bool:
        """Check API service health.

        Args:
            url: API base URL

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{url}/health", timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def check_celery_flower(self, url: str = "http://localhost:5555") -> bool:
        """Check Celery Flower health.

        Args:
            url: Flower base URL

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{url}/api/workers", timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def check_localstack(self, url: str = "http://localhost:4566") -> bool:
        """Check LocalStack health.

        Args:
            url: LocalStack base URL

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{url}/_localstack/health", timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def check_supabase(self, url: str = "http://localhost:54321") -> bool:
        """Check Supabase health.

        Args:
            url: Supabase base URL

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{url}/rest/v1/", timeout=self.timeout)
            return response.status_code in [200, 401, 404]
        except requests.exceptions.RequestException:
            return False

    def check_redis(self) -> bool:
        """Check Redis health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            import redis

            r = redis.from_url("redis://localhost:6379")
            return r.ping()
        except:
            return False

    def wait_for_services(
        self,
        services: List[str] = None,
        max_retries: int = 60,
        retry_delay: int = 2,
    ) -> Dict[str, bool]:
        """Wait for services to be ready.

        Args:
            services: List of services to check (None for all)
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds

        Returns:
            Dictionary of service health status
        """
        if services is None:
            services = ["api", "localstack", "supabase", "redis"]

        service_checkers = {
            "api": self.check_api,
            "celery": self.check_celery_flower,
            "localstack": self.check_localstack,
            "supabase": self.check_supabase,
            "redis": self.check_redis,
        }

        results = {}

        for service in services:
            if service not in service_checkers:
                continue

            checker = service_checkers[service]
            for attempt in range(max_retries):
                if checker():
                    results[service] = True
                    print(f"✅ {service.capitalize()} is ready")
                    break

                if attempt == max_retries - 1:
                    results[service] = False
                    print(
                        f"❌ {service.capitalize()} not ready after {max_retries * retry_delay} seconds"
                    )
                else:
                    time.sleep(retry_delay)

        return results


class SupabaseTestHelper:
    """Helper for Supabase testing operations."""

    def __init__(
        self,
        url: str = "http://localhost:54321",
        anon_key: str = None,
        service_key: str = None,
    ):
        """Initialize Supabase helper.

        Args:
            url: Supabase URL
            anon_key: Anonymous key for Supabase
            service_key: Service role key for Supabase
        """
        self.url = url
        self.anon_key = anon_key or os.getenv(
            "SUPABASE_ANON_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        )
        self.service_key = service_key or os.getenv(
            "SUPABASE_SERVICE_KEY", self.anon_key
        )

    def get_headers(self, use_service_key: bool = False) -> Dict[str, str]:
        """Get headers for Supabase requests.

        Args:
            use_service_key: Use service key instead of anon key

        Returns:
            Headers dictionary
        """
        key = self.service_key if use_service_key else self.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def create_table_data(
        self, table: str, data: Dict[str, Any], use_service_key: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Create data in Supabase table.

        Args:
            table: Table name
            data: Data to insert
            use_service_key: Use service key for authentication

        Returns:
            Created record or None if failed
        """
        try:
            response = requests.post(
                f"{self.url}/rest/v1/{table}",
                json=data,
                headers=self.get_headers(use_service_key),
            )
            if response.status_code in [200, 201]:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to create data in {table}: {e}")
        return None

    def get_table_data(
        self, table: str, filters: Dict[str, Any] = None, use_service_key: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """Get data from Supabase table.

        Args:
            table: Table name
            filters: Query filters
            use_service_key: Use service key for authentication

        Returns:
            List of records or None if failed
        """
        try:
            url = f"{self.url}/rest/v1/{table}"
            if filters:
                query_params = "&".join([f"{k}=eq.{v}" for k, v in filters.items()])
                url = f"{url}?{query_params}"

            response = requests.get(url, headers=self.get_headers(use_service_key))
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get data from {table}: {e}")
        return None

    def delete_table_data(
        self, table: str, filters: Dict[str, Any], use_service_key: bool = True
    ) -> bool:
        """Delete data from Supabase table.

        Args:
            table: Table name
            filters: Query filters for deletion
            use_service_key: Use service key for authentication

        Returns:
            True if successful, False otherwise
        """
        try:
            query_params = "&".join([f"{k}=eq.{v}" for k, v in filters.items()])
            url = f"{self.url}/rest/v1/{table}?{query_params}"

            response = requests.delete(url, headers=self.get_headers(use_service_key))
            return response.status_code in [200, 204]
        except requests.exceptions.RequestException as e:
            print(f"Failed to delete data from {table}: {e}")
        return False

    def run_migration(self, migration_file: Path) -> bool:
        """Run SQL migration file.

        Args:
            migration_file: Path to migration SQL file

        Returns:
            True if successful, False otherwise
        """
        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return False

        try:
            with open(migration_file, "r") as f:
                sql = f.read()

            # Note: This would typically use Supabase CLI or direct database connection
            # For now, we'll just validate the file exists
            print(f"Migration file ready: {migration_file}")
            return True
        except Exception as e:
            print(f"Failed to prepare migration: {e}")
            return False


class LocalStackTestHelper:
    """Helper for LocalStack testing operations."""

    def __init__(self, endpoint_url: str = "http://localhost:4566"):
        """Initialize LocalStack helper.

        Args:
            endpoint_url: LocalStack endpoint URL
        """
        self.endpoint_url = endpoint_url
        self.aws_config = {
            "endpoint_url": endpoint_url,
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "region_name": "us-east-1",
        }

    def create_s3_bucket(self, bucket_name: str) -> bool:
        """Create S3 bucket in LocalStack.

        Args:
            bucket_name: Name of the bucket

        Returns:
            True if successful, False otherwise
        """
        try:
            import boto3

            s3_client = boto3.client("s3", **self.aws_config)
            s3_client.create_bucket(Bucket=bucket_name)
            return True
        except Exception as e:
            print(f"Failed to create S3 bucket: {e}")
            return False

    def upload_to_s3(self, bucket_name: str, key: str, content: str) -> bool:
        """Upload content to S3 bucket.

        Args:
            bucket_name: Bucket name
            key: Object key
            content: Content to upload

        Returns:
            True if successful, False otherwise
        """
        try:
            import boto3

            s3_client = boto3.client("s3", **self.aws_config)
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=content.encode(),
                ContentType="application/json",
            )
            return True
        except Exception as e:
            print(f"Failed to upload to S3: {e}")
            return False

    def create_sqs_queue(self, queue_name: str) -> Optional[str]:
        """Create SQS queue in LocalStack.

        Args:
            queue_name: Name of the queue

        Returns:
            Queue URL if successful, None otherwise
        """
        try:
            import boto3

            sqs_client = boto3.client("sqs", **self.aws_config)
            response = sqs_client.create_queue(QueueName=queue_name)
            return response["QueueUrl"]
        except Exception as e:
            print(f"Failed to create SQS queue: {e}")
            return None

    def send_sqs_message(self, queue_url: str, message: Dict[str, Any]) -> bool:
        """Send message to SQS queue.

        Args:
            queue_url: Queue URL
            message: Message to send

        Returns:
            True if successful, False otherwise
        """
        try:
            import boto3

            sqs_client = boto3.client("sqs", **self.aws_config)
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message),
            )
            return True
        except Exception as e:
            print(f"Failed to send SQS message: {e}")
            return False

    def cleanup_resources(self) -> None:
        """Clean up LocalStack test resources."""
        try:
            import boto3

            # Clean up S3 buckets
            s3_client = boto3.client("s3", **self.aws_config)
            buckets = s3_client.list_buckets()
            for bucket in buckets.get("Buckets", []):
                if bucket["Name"].startswith("e2e-test-"):
                    # Delete all objects first
                    objects = s3_client.list_objects_v2(Bucket=bucket["Name"])
                    for obj in objects.get("Contents", []):
                        s3_client.delete_object(Bucket=bucket["Name"], Key=obj["Key"])
                    # Delete bucket
                    s3_client.delete_bucket(Bucket=bucket["Name"])

            # Clean up SQS queues
            sqs_client = boto3.client("sqs", **self.aws_config)
            queues = sqs_client.list_queues(QueueNamePrefix="e2e-test-")
            for queue_url in queues.get("QueueUrls", []):
                sqs_client.delete_queue(QueueUrl=queue_url)

            print("LocalStack test resources cleaned up")
        except Exception as e:
            print(f"Failed to cleanup LocalStack resources: {e}")


def setup_test_environment() -> Dict[str, str]:
    """Set up test environment variables.

    Returns:
        Dictionary of environment variables
    """
    env = {
        "ENV": "test",
        "DEBUG": "true",
        "LOCALSTACK": "true",
        "LOCALSTACK_ENDPOINT": "http://localhost:4566",
        "SUPABASE_URL": "http://localhost:54321",
        "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        "REDIS_URL": "redis://localhost:6379",
        "CELERY_BROKER_URL": "redis://localhost:6379/0",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/0",
    }
    os.environ.update(env)
    return env
