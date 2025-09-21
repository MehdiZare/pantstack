"""Event backbone for publishing events to multiple targets."""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

import redis
from celery import Celery

from stack.libs.shared.core.config import BaseConfig


class EventType(Enum):
    """Auth service event types."""

    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_VERIFIED = "user.verified"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_PASSWORD_RESET = "user.password_reset"

    # Auth events
    TOKEN_GENERATED = "auth.token_generated"
    TOKEN_REFRESHED = "auth.token_refreshed"
    TOKEN_REVOKED = "auth.token_revoked"
    LOGIN_FAILED = "auth.login_failed"
    ACCOUNT_LOCKED = "auth.account_locked"
    ACCOUNT_UNLOCKED = "auth.account_unlocked"

    # Role events
    ROLE_ASSIGNED = "role.assigned"
    ROLE_REVOKED = "role.revoked"
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"


class EventTarget(Enum):
    """Event publishing targets."""

    ALL = "all"
    REDIS = "redis"
    CELERY = "celery"
    SQS = "sqs"
    EVENTBRIDGE = "eventbridge"


class Event:
    """Event data structure."""

    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        """Initialize event.

        Args:
            event_type: Type of event
            data: Event data
            user_id: User ID associated with event
            correlation_id: Correlation ID for tracking
        """
        self.event_type = event_type
        self.data = data
        self.user_id = user_id
        self.correlation_id = correlation_id or str(uuid4())
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Event as dictionary
        """
        return {
            "type": self.event_type.value,
            "data": self.data,
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "service": "auth",
        }

    def to_json(self) -> str:
        """Convert event to JSON string.

        Returns:
            Event as JSON
        """
        return json.dumps(self.to_dict())


class EventBackbone:
    """Event backbone for publishing events to multiple targets."""

    def __init__(
        self,
        config: BaseConfig,
        redis: Optional[redis.Redis] = None,
        celery_app: Optional[Celery] = None,
    ):
        """Initialize event backbone.

        Args:
            config: Service configuration
            redis: Redis client
            celery_app: Celery app
        """
        self.config = config
        self.redis = redis
        self.celery_app = celery_app

        # Initialize AWS clients if configured
        self.sqs_client = None
        self.eventbridge_client = None

        if config.aws and config.aws.region:
            try:
                import boto3

                if config.aws.localstack_enabled:
                    session_config = {"endpoint_url": config.aws.localstack_endpoint}
                else:
                    session_config = {}

                if config.aws.sqs_queue_url:
                    self.sqs_client = boto3.client("sqs", **session_config)

                if config.aws.eventbridge_bus:
                    self.eventbridge_client = boto3.client("events", **session_config)
            except ImportError:
                print("⚠️ boto3 not installed, AWS events disabled")

    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        target: EventTarget = EventTarget.ALL,
    ) -> str:
        """Publish event to specified targets.

        Args:
            event_type: Type of event
            data: Event data
            user_id: User ID
            target: Publishing target

        Returns:
            Event correlation ID
        """
        event = Event(event_type, data, user_id)

        # Publish to Redis
        if target in [EventTarget.ALL, EventTarget.REDIS] and self.redis:
            await self._publish_to_redis(event)

        # Queue as Celery task
        if target in [EventTarget.ALL, EventTarget.CELERY] and self.celery_app:
            await self._publish_to_celery(event)

        # Send to SQS
        if target in [EventTarget.ALL, EventTarget.SQS] and self.sqs_client:
            await self._publish_to_sqs(event)

        # Send to EventBridge
        if target in [EventTarget.ALL, EventTarget.EVENTBRIDGE] and self.eventbridge_client:
            await self._publish_to_eventbridge(event)

        return event.correlation_id

    async def _publish_to_redis(self, event: Event) -> None:
        """Publish event to Redis pub/sub.

        Args:
            event: Event to publish
        """
        try:
            channel = f"events:{event.event_type.value}"
            self.redis.publish(channel, event.to_json())
            print(f"📢 Published to Redis: {event.event_type.value}")
        except Exception as e:
            print(f"❌ Failed to publish to Redis: {e}")

    async def _publish_to_celery(self, event: Event) -> None:
        """Queue event as Celery task.

        Args:
            event: Event to publish
        """
        try:
            # Import task here to avoid circular dependency
            from services.auth.src.tasks.event_tasks import process_event

            process_event.delay(event.to_dict())
            print(f"📢 Queued to Celery: {event.event_type.value}")
        except Exception as e:
            print(f"❌ Failed to queue to Celery: {e}")

    async def _publish_to_sqs(self, event: Event) -> None:
        """Send event to SQS queue.

        Args:
            event: Event to publish
        """
        try:
            self.sqs_client.send_message(
                QueueUrl=self.config.aws.sqs_queue_url,
                MessageBody=event.to_json(),
                MessageAttributes={
                    "event_type": {"StringValue": event.event_type.value, "DataType": "String"},
                    "service": {"StringValue": "auth", "DataType": "String"},
                },
            )
            print(f"📢 Sent to SQS: {event.event_type.value}")
        except Exception as e:
            print(f"❌ Failed to send to SQS: {e}")

    async def _publish_to_eventbridge(self, event: Event) -> None:
        """Send event to EventBridge.

        Args:
            event: Event to publish
        """
        try:
            self.eventbridge_client.put_events(
                Entries=[
                    {
                        "Source": "pantstack.auth",
                        "DetailType": event.event_type.value,
                        "Detail": json.dumps(event.data),
                    }
                ]
            )
            print(f"📢 Sent to EventBridge: {event.event_type.value}")
        except Exception as e:
            print(f"❌ Failed to send to EventBridge: {e}")