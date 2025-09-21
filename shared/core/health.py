"""Health check and validation utilities."""

import asyncio
import time
from typing import Dict, List, Optional

import redis
import requests
from pydantic import ValidationError

from shared.core.config import BaseConfig
from shared.core.environment import Environment, EnvironmentDetector


class ServiceHealth:
    """Health check for services and dependencies."""

    @staticmethod
    async def check_localstack(timeout: int = 60) -> bool:
        """Wait for LocalStack to be ready.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if LocalStack is ready, False otherwise
        """
        print("🔄 Checking LocalStack health...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    "http://localhost:4566/_localstack/health",
                    timeout=2
                )
                if response.status_code == 200:
                    data = response.json()
                    # Check if init scripts have run
                    if data.get("features", {}).get("initScripts") == "initialized":
                        print("✅ LocalStack is ready and initialized")
                        return True
                    elif data.get("services"):
                        print("⏳ LocalStack is running, waiting for initialization...")
            except requests.exceptions.RequestException:
                pass

            await asyncio.sleep(1)

        print("❌ LocalStack health check timed out")
        return False

    @staticmethod
    def check_redis(host: str = "localhost", port: int = 6379) -> bool:
        """Check if Redis is available.

        Args:
            host: Redis host
            port: Redis port

        Returns:
            True if Redis is available
        """
        try:
            client = redis.Redis(
                host=host,
                port=port,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            client.ping()
            return True
        except:
            return False

    @staticmethod
    def check_postgres(
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: str = "postgres"
    ) -> bool:
        """Check if PostgreSQL is available.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password

        Returns:
            True if PostgreSQL is available
        """
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=2
            )
            conn.close()
            return True
        except:
            return False

    @staticmethod
    async def wait_for_dependencies(
        services: List[str] = None,
        timeout: int = 60
    ) -> Dict[str, bool]:
        """Wait for service dependencies to be ready.

        Args:
            services: List of services to check
            timeout: Maximum seconds to wait

        Returns:
            Dictionary of service health status
        """
        if services is None:
            services = ["redis", "postgres"]

            # Add LocalStack if enabled
            env = EnvironmentDetector.detect()
            if env == Environment.LOCALSTACK:
                services.append("localstack")

        results = {}
        tasks = []

        for service in services:
            if service == "redis":
                tasks.append(("redis", ServiceHealth._wait_for_redis(timeout)))
            elif service == "postgres":
                tasks.append(("postgres", ServiceHealth._wait_for_postgres(timeout)))
            elif service == "localstack":
                tasks.append(("localstack", ServiceHealth.check_localstack(timeout)))

        # Run checks concurrently
        for service_name, task in tasks:
            results[service_name] = await task

        return results

    @staticmethod
    async def _wait_for_redis(timeout: int) -> bool:
        """Wait for Redis to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ServiceHealth.check_redis():
                return True
            await asyncio.sleep(1)
        return False

    @staticmethod
    async def _wait_for_postgres(timeout: int) -> bool:
        """Wait for PostgreSQL to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ServiceHealth.check_postgres():
                return True
            await asyncio.sleep(1)
        return False


class ConfigValidator:
    """Configuration validation utilities."""

    @staticmethod
    def validate_config(config: BaseConfig, environment: Optional[Environment] = None) -> List[str]:
        """Validate configuration for environment.

        Args:
            config: Configuration to validate
            environment: Target environment (auto-detected if None)

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        env = environment or EnvironmentDetector.detect()

        # Basic validation
        if not config.app_name:
            errors.append("app_name is required")

        if not config.service_name:
            errors.append("service_name is required")

        # Environment-specific validation
        if env == Environment.PRODUCTION:
            errors.extend(ConfigValidator._validate_production(config))
        elif env == Environment.STAGING:
            errors.extend(ConfigValidator._validate_staging(config))
        elif env == Environment.LOCALSTACK:
            errors.extend(ConfigValidator._validate_localstack(config))

        return errors

    @staticmethod
    def _validate_production(config: BaseConfig) -> List[str]:
        """Validate production configuration."""
        errors = []

        # Security checks
        if config.secret_key in ("", "change-me-in-production", "development-secret-key"):
            errors.append("Production requires a secure secret_key")

        if config.debug:
            errors.append("Debug must be disabled in production")

        # AWS configuration
        if hasattr(config, "aws"):
            if not config.aws.region:
                errors.append("AWS region is required in production")
            if not config.aws.account_id:
                errors.append("AWS account ID is required in production")
            if config.aws.localstack_enabled:
                errors.append("LocalStack cannot be enabled in production")

        # Database configuration
        if hasattr(config, "database"):
            if not config.database.supabase_url:
                errors.append("Database URL is required in production")
            if not config.database.supabase_anon_key:
                errors.append("Database key is required in production")

        # Redis configuration
        if hasattr(config, "redis"):
            if config.redis.host in ("localhost", "127.0.0.1"):
                errors.append("Redis must not use localhost in production")

        return errors

    @staticmethod
    def _validate_staging(config: BaseConfig) -> List[str]:
        """Validate staging configuration."""
        errors = []

        # Similar to production but allow debug
        if config.secret_key in ("", "change-me-in-production", "development-secret-key"):
            errors.append("Staging requires a secure secret_key")

        if hasattr(config, "aws"):
            if not config.aws.region:
                errors.append("AWS region is required in staging")
            if config.aws.localstack_enabled:
                errors.append("LocalStack should not be enabled in staging")

        return errors

    @staticmethod
    def _validate_localstack(config: BaseConfig) -> List[str]:
        """Validate LocalStack configuration."""
        errors = []

        if hasattr(config, "aws"):
            if not config.aws.localstack_enabled:
                errors.append("LocalStack must be enabled in LocalStack environment")
            if not config.aws.localstack_endpoint:
                errors.append("LocalStack endpoint is required")

        return errors

    @staticmethod
    def assert_valid(config: BaseConfig, environment: Optional[Environment] = None):
        """Assert configuration is valid.

        Args:
            config: Configuration to validate
            environment: Target environment

        Raises:
            ValueError: If configuration is invalid
        """
        errors = ConfigValidator.validate_config(config, environment)
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


class StartupValidator:
    """Validate system state on startup."""

    @staticmethod
    async def validate_startup(config: BaseConfig) -> Dict[str, any]:
        """Validate system is ready for startup.

        Args:
            config: Application configuration

        Returns:
            Validation results
        """
        results = {
            "config_valid": False,
            "dependencies_ready": {},
            "errors": []
        }

        # Validate configuration
        try:
            ConfigValidator.assert_valid(config)
            results["config_valid"] = True
        except ValueError as e:
            results["errors"].append(str(e))

        # Check dependencies
        env = EnvironmentDetector.detect()
        services_to_check = []

        if env == Environment.LOCALSTACK:
            services_to_check = ["redis", "postgres", "localstack"]
        elif env == Environment.DEVELOPMENT:
            services_to_check = ["redis", "postgres"]
        # Skip dependency checks in production (handled by orchestration)

        if services_to_check:
            print(f"🔍 Checking dependencies: {', '.join(services_to_check)}")
            results["dependencies_ready"] = await ServiceHealth.wait_for_dependencies(
                services=services_to_check,
                timeout=30
            )

            # Check if all dependencies are ready
            for service, ready in results["dependencies_ready"].items():
                if not ready:
                    results["errors"].append(f"Service {service} is not ready")

        return results