"""Lambda function for refreshing JWT tokens.

Handles token refresh logic for maintaining user sessions.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from jwt.exceptions import InvalidTokenError


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Refresh JWT access token using refresh token.

    Args:
        event: Lambda event containing refresh token
        context: Lambda context

    Returns:
        New access token or error response
    """
    # Extract refresh token
    refresh_token = None

    # From body (API Gateway integration)
    if "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            refresh_token = body.get("refreshToken")
        except json.JSONDecodeError:
            pass

    # Direct invocation
    if not refresh_token and "refreshToken" in event:
        refresh_token = event["refreshToken"]

    # From headers
    if not refresh_token and "headers" in event:
        refresh_token = event["headers"].get("x-refresh-token")

    if not refresh_token:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Refresh token required"})
        }

    try:
        # Get secrets from environment
        refresh_secret = os.environ.get("JWT_REFRESH_SECRET", "refresh-secret")
        access_secret = os.environ.get("JWT_SECRET", "development-secret")

        # Verify refresh token
        payload = jwt.decode(
            refresh_token,
            refresh_secret,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )

        # Check token type
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        # Generate new access token
        now = datetime.now(timezone.utc)
        access_payload = {
            "sub": payload["sub"],  # User ID
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),  # 15 minute expiry
        }

        access_token = jwt.encode(
            access_payload,
            access_secret,
            algorithm="HS256"
        )

        # Optionally generate new refresh token (token rotation)
        new_refresh_token = None
        if os.environ.get("ROTATE_REFRESH_TOKENS", "false").lower() == "true":
            refresh_payload = {
                "sub": payload["sub"],
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "type": "refresh",
                "iat": now,
                "exp": now + timedelta(days=30),  # 30 day expiry
            }

            new_refresh_token = jwt.encode(
                refresh_payload,
                refresh_secret,
                algorithm="HS256"
            )

        response_body = {
            "accessToken": access_token,
            "expiresIn": 900,  # 15 minutes in seconds
            "tokenType": "Bearer"
        }

        if new_refresh_token:
            response_body["refreshToken"] = new_refresh_token

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Cache-Control": "no-store"
            },
            "body": json.dumps(response_body)
        }

    except InvalidTokenError as e:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Invalid or expired refresh token",
                "details": str(e)
            })
        }
    except Exception as e:
        print(f"Token refresh error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Internal server error"
            })
        }