"""Lambda function for processing user signups asynchronously.

Triggered by SQS or EventBridge for processing new user registrations.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process signup events from SQS or EventBridge.

    Args:
        event: Lambda event containing signup data
        context: Lambda context

    Returns:
        Processing result
    """
    processed_count = 0
    failed_count = 0
    results = []

    # Handle different event sources
    records = []

    # SQS event
    if "Records" in event:
        records = event["Records"]
    # EventBridge event
    elif "source" in event and event["source"] == "auth.service":
        records = [{"body": json.dumps(event["detail"])}]
    # Direct invocation
    elif "users" in event:
        records = [{"body": json.dumps(user)} for user in event["users"]]

    ses_client = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))

    # Get table name from environment
    table_name = os.environ.get("USERS_TABLE", "users-dev")

    for record in records:
        try:
            # Parse message body
            if isinstance(record.get("body"), str):
                data = json.loads(record["body"])
            else:
                data = record["body"]

            user_id = data.get("userId", data.get("id"))
            email = data.get("email")
            name = data.get("name", "User")

            if not email:
                raise ValueError("Email is required")

            # Store user metadata in DynamoDB
            try:
                table = dynamodb.Table(table_name)
                table.put_item(
                    Item={
                        "userId": user_id,
                        "email": email,
                        "name": name,
                        "signupDate": datetime.utcnow().isoformat(),
                        "welcomeEmailSent": False,
                        "verificationStatus": "pending"
                    }
                )
            except ClientError as e:
                print(f"DynamoDB error: {e}")
                # Continue even if DynamoDB fails

            # Send welcome email via SES
            try:
                response = ses_client.send_email(
                    Source=os.environ.get("FROM_EMAIL", "noreply@example.com"),
                    Destination={"ToAddresses": [email]},
                    Message={
                        "Subject": {"Data": "Welcome to Our Platform!"},
                        "Body": {
                            "Html": {
                                "Data": f"""
                                <html>
                                <body>
                                    <h2>Welcome {name}!</h2>
                                    <p>Thank you for signing up. Your account has been created successfully.</p>
                                    <p>User ID: {user_id}</p>
                                    <p>Please verify your email address to get started.</p>
                                </body>
                                </html>
                                """
                            }
                        }
                    }
                )

                # Update DynamoDB to mark email as sent
                table.update_item(
                    Key={"userId": user_id},
                    UpdateExpression="SET welcomeEmailSent = :sent",
                    ExpressionAttributeValues={":sent": True}
                )

                results.append({
                    "userId": user_id,
                    "status": "success",
                    "messageId": response["MessageId"]
                })
                processed_count += 1

            except ClientError as e:
                print(f"SES error for {email}: {e}")
                results.append({
                    "userId": user_id,
                    "status": "email_failed",
                    "error": str(e)
                })
                failed_count += 1

        except Exception as e:
            print(f"Error processing record: {e}")
            results.append({
                "status": "failed",
                "error": str(e),
                "record": str(record)[:200]  # Truncate for logging
            })
            failed_count += 1

    return {
        "statusCode": 200,
        "body": json.dumps({
            "processed": processed_count,
            "failed": failed_count,
            "total": len(records),
            "results": results
        })
    }