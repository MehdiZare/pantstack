"""Integration tests for LocalStack services."""

import json
import os
import time
from typing import Dict, Any

import boto3
import pytest
import requests
from botocore.exceptions import ClientError


class TestLocalStackServices:
    """Test LocalStack AWS service emulation."""

    @pytest.fixture(scope="class")
    def localstack_endpoint(self):
        """Get LocalStack endpoint URL."""
        return os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")

    @pytest.fixture(scope="class")
    def aws_config(self, localstack_endpoint):
        """AWS client configuration for LocalStack."""
        return {
            "endpoint_url": localstack_endpoint,
            "aws_access_key_id": "test",
            "aws_secret_access_key": "test",
            "region_name": "us-east-1",
        }

    @pytest.fixture(scope="class")
    def wait_for_localstack(self, localstack_endpoint):
        """Wait for LocalStack to be ready."""
        max_retries = 30
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{localstack_endpoint}/_localstack/health")
                if response.status_code == 200:
                    health_data = response.json()
                    # Check if core services are available
                    services = health_data.get("services", {})
                    if all(
                        services.get(service) in ["available", "running"]
                        for service in ["s3", "sqs", "dynamodb"]
                    ):
                        return True
            except requests.exceptions.ConnectionError:
                pass

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        pytest.skip("LocalStack not available for integration tests")

    def test_localstack_health_check(self, localstack_endpoint, wait_for_localstack):
        """Test LocalStack health check endpoint."""
        response = requests.get(f"{localstack_endpoint}/_localstack/health")

        assert response.status_code == 200

        health_data = response.json()
        assert "services" in health_data

        # Check core services
        services = health_data["services"]
        required_services = ["s3", "sqs", "dynamodb"]

        for service in required_services:
            assert service in services
            assert services[service] in ["available", "running"]

    def test_s3_bucket_operations(self, aws_config, wait_for_localstack):
        """Test S3 bucket operations in LocalStack."""
        s3_client = boto3.client("s3", **aws_config)

        bucket_name = "test-integration-bucket"

        # Create bucket
        s3_client.create_bucket(Bucket=bucket_name)

        # List buckets
        response = s3_client.list_buckets()
        bucket_names = [bucket["Name"] for bucket in response["Buckets"]]
        assert bucket_name in bucket_names

        # Put object
        test_key = "test-file.txt"
        test_content = "Hello from integration test!"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode(),
            ContentType="text/plain",
        )

        # Get object
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        retrieved_content = response["Body"].read().decode()

        assert retrieved_content == test_content

        # List objects
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        assert "Contents" in response
        object_keys = [obj["Key"] for obj in response["Contents"]]
        assert test_key in object_keys

        # Delete object
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)

        # Delete bucket
        s3_client.delete_bucket(Bucket=bucket_name)

    def test_sqs_queue_operations(self, aws_config, wait_for_localstack):
        """Test SQS queue operations in LocalStack."""
        sqs_client = boto3.client("sqs", **aws_config)

        queue_name = "test-integration-queue"

        # Create queue
        response = sqs_client.create_queue(QueueName=queue_name)
        queue_url = response["QueueUrl"]

        assert queue_name in queue_url

        # Send message
        message_body = "Test message from integration test"
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=message_body)

        # Receive message
        response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

        assert "Messages" in response
        messages = response["Messages"]
        assert len(messages) == 1

        received_message = messages[0]
        assert received_message["Body"] == message_body

        # Delete message
        receipt_handle = received_message["ReceiptHandle"]
        sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        # Delete queue
        sqs_client.delete_queue(QueueUrl=queue_url)

    def test_dynamodb_table_operations(self, aws_config, wait_for_localstack):
        """Test DynamoDB table operations in LocalStack."""
        dynamodb = boto3.resource("dynamodb", **aws_config)

        table_name = "test-integration-table"

        # Create table
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Wait for table to be created
        table.wait_until_exists()

        # Put item
        test_item = {"id": "test-id", "name": "Test Item", "value": 42}

        table.put_item(Item=test_item)

        # Get item
        response = table.get_item(Key={"id": "test-id"})

        assert "Item" in response
        retrieved_item = response["Item"]

        assert retrieved_item["id"] == test_item["id"]
        assert retrieved_item["name"] == test_item["name"]
        assert retrieved_item["value"] == test_item["value"]

        # Scan table
        response = table.scan()
        assert "Items" in response
        assert len(response["Items"]) >= 1

        # Update item
        table.update_item(
            Key={"id": "test-id"},
            UpdateExpression="SET #n = :name",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={":name": "Updated Test Item"},
        )

        # Verify update
        response = table.get_item(Key={"id": "test-id"})
        updated_item = response["Item"]
        assert updated_item["name"] == "Updated Test Item"

        # Delete item
        table.delete_item(Key={"id": "test-id"})

        # Delete table
        table.delete()

    def test_lambda_function_operations(self, aws_config, wait_for_localstack):
        """Test Lambda function operations in LocalStack."""
        lambda_client = boto3.client("lambda", **aws_config)

        function_name = "test-integration-function"

        # Simple Lambda function code
        lambda_code = '''
def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": f"Hello from {event.get('name', 'Lambda')}!"
    }
'''

        # Create zip file content
        import zipfile
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("lambda_function.py", lambda_code)

        zip_content = zip_buffer.getvalue()

        try:
            # Create function
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime="python3.11",
                Role="arn:aws:iam::123456789012:role/lambda-role",
                Handler="lambda_function.lambda_handler",
                Code={"ZipFile": zip_content},
                Description="Test Lambda function for integration testing",
            )

            assert response["FunctionName"] == function_name
            assert response["Runtime"] == "python3.11"

            # Invoke function
            payload = {"name": "Integration Test"}

            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(payload).encode(),
            )

            assert response["StatusCode"] == 200

            # Read response
            response_payload = json.loads(response["Payload"].read().decode())
            assert response_payload["statusCode"] == 200
            assert "Hello from Integration Test!" in response_payload["body"]

        except ClientError as e:
            # Lambda might not be fully supported in LocalStack free version
            if "not implemented" in str(e).lower():
                pytest.skip("Lambda not fully supported in LocalStack free version")
            else:
                raise

        finally:
            # Clean up
            try:
                lambda_client.delete_function(FunctionName=function_name)
            except ClientError:
                pass  # Function might not exist

    def test_service_discovery_and_endpoints(self, localstack_endpoint, wait_for_localstack):
        """Test service discovery and endpoint resolution."""
        # Test that services are accessible on expected endpoints
        services_to_test = {
            "s3": f"{localstack_endpoint}",
            "sqs": f"{localstack_endpoint}",
            "dynamodb": f"{localstack_endpoint}",
        }

        for service, endpoint in services_to_test.items():
            # Test that service endpoints are reachable
            try:
                response = requests.head(endpoint, timeout=5)
                # LocalStack typically returns 404 for HEAD requests to root,
                # but the connection should succeed
                assert response.status_code in [200, 404, 405]
            except requests.exceptions.ConnectionError:
                pytest.fail(f"Could not connect to {service} at {endpoint}")

    def test_cross_service_integration(self, aws_config, wait_for_localstack):
        """Test integration between multiple AWS services."""
        # Create S3 bucket and SQS queue for integration test
        s3_client = boto3.client("s3", **aws_config)
        sqs_client = boto3.client("sqs", **aws_config)

        bucket_name = "integration-test-bucket"
        queue_name = "integration-test-queue"

        # Create resources
        s3_client.create_bucket(Bucket=bucket_name)
        response = sqs_client.create_queue(QueueName=queue_name)
        queue_url = response["QueueUrl"]

        try:
            # Upload file to S3
            test_file_key = "test-integration-file.txt"
            test_content = "Cross-service integration test content"

            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_file_key,
                Body=test_content.encode(),
            )

            # Send notification to SQS about S3 upload
            notification_message = {
                "bucket": bucket_name,
                "key": test_file_key,
                "action": "upload",
                "timestamp": "2023-09-20T10:00:00Z",
            }

            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(notification_message),
            )

            # Receive and process notification
            response = sqs_client.receive_message(QueueUrl=queue_url)
            assert "Messages" in response

            message = response["Messages"][0]
            message_data = json.loads(message["Body"])

            assert message_data["bucket"] == bucket_name
            assert message_data["key"] == test_file_key
            assert message_data["action"] == "upload"

            # Verify file exists in S3 based on notification
            response = s3_client.get_object(
                Bucket=message_data["bucket"],
                Key=message_data["key"]
            )

            retrieved_content = response["Body"].read().decode()
            assert retrieved_content == test_content

        finally:
            # Clean up
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_file_key)
                s3_client.delete_bucket(Bucket=bucket_name)
                sqs_client.delete_queue(QueueUrl=queue_url)
            except ClientError:
                pass  # Resources might not exist