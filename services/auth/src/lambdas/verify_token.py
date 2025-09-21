"""Lambda function for JWT token verification.

This Lambda can be used as an API Gateway authorizer or invoked directly.
"""

import json
import os
from typing import Any, Dict

import jwt
from jwt.exceptions import InvalidTokenError


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Verify JWT token and return authorization context.

    Args:
        event: Lambda event containing token in headers or authorizationToken
        context: Lambda context

    Returns:
        Authorization response for API Gateway or validation result
    """
    # Extract token from different event formats
    token = None

    # API Gateway authorizer format
    if "authorizationToken" in event:
        token = event["authorizationToken"].replace("Bearer ", "")
    # Direct invocation or HTTP API format
    elif "headers" in event:
        auth_header = event["headers"].get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    # Direct token in body
    elif "token" in event:
        token = event["token"]

    if not token:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "No token provided"})
        }

    try:
        # Get secret from environment or Parameter Store in production
        secret = os.environ.get("JWT_SECRET", "development-secret")

        # Verify and decode token
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )

        # For API Gateway authorizer response
        if "methodArn" in event:
            return {
                "principalId": payload.get("sub", "user"),
                "policyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "execute-api:Invoke",
                            "Effect": "Allow",
                            "Resource": event["methodArn"]
                        }
                    ]
                },
                "context": {
                    "userId": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role", "user")
                }
            }

        # Direct invocation response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "valid": True,
                "payload": payload
            })
        }

    except InvalidTokenError as e:
        # For API Gateway authorizer
        if "methodArn" in event:
            # Return explicit deny
            return {
                "principalId": "unauthorized",
                "policyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "execute-api:Invoke",
                            "Effect": "Deny",
                            "Resource": event["methodArn"]
                        }
                    ]
                }
            }

        # Direct invocation response
        return {
            "statusCode": 401,
            "body": json.dumps({
                "valid": False,
                "error": str(e)
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Internal error: {str(e)}"
            })
        }