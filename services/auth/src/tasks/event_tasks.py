"""Event processing Celery tasks."""

from celery import shared_task


@shared_task(name="auth.process_event")
def process_event(event: dict) -> dict:
    """Process events from the event backbone.

    Args:
        event: Event dictionary with type, data, etc.

    Returns:
        Task result
    """
    event_type = event.get("type")
    data = event.get("data", {})
    user_id = event.get("user_id")

    try:
        # Route event to appropriate handler
        if event_type == "user.registered":
            # Send welcome email
            from .user_tasks import send_welcome_email

            send_welcome_email.delay(user_id)

            # Send verification email if token provided
            if "verification_token" in data:
                from .user_tasks import send_verification_email

                send_verification_email.delay(user_id, data["verification_token"])

        elif event_type == "user.password_reset":
            # Send password reset email
            from .user_tasks import send_password_reset_email

            send_password_reset_email.delay(data.get("email"), data.get("reset_token"))

        elif event_type == "user.login":
            # Log login event, update analytics, etc.
            print(f"User {user_id} logged in")

        elif event_type == "user.updated":
            # Sync user data with external systems
            from .user_tasks import sync_user_data

            sync_user_data.delay(user_id)

        return {
            "status": "success",
            "event_type": event_type,
            "user_id": user_id,
            "task": "process_event",
        }
    except Exception as e:
        return {
            "status": "error",
            "event_type": event_type,
            "user_id": user_id,
            "error": str(e),
        }


@shared_task(name="auth.process_batch_events")
def process_batch_events(events: list[dict]) -> dict:
    """Process multiple events in batch.

    Args:
        events: List of event dictionaries

    Returns:
        Task result with processing summary
    """
    success_count = 0
    failed_count = 0
    results = []

    for event in events:
        result = process_event(event)
        results.append(result)

        if result["status"] == "success":
            success_count += 1
        else:
            failed_count += 1

    return {
        "status": "completed",
        "task": "process_batch_events",
        "total": len(events),
        "success": success_count,
        "failed": failed_count,
        "results": results,
    }


@shared_task(name="auth.replay_events")
def replay_events(
    event_type: str = None, start_time: str = None, end_time: str = None
) -> dict:
    """Replay events from event store.

    Args:
        event_type: Optional filter by event type
        start_time: Optional start time filter
        end_time: Optional end time filter

    Returns:
        Task result with replay summary
    """
    try:
        # This would fetch events from event store (S3, database, etc.)
        # and replay them for recovery or testing purposes
        print(f"Replaying events: type={event_type}, start={start_time}, end={end_time}")

        # Placeholder for actual implementation
        replayed_count = 0

        return {
            "status": "success",
            "task": "replay_events",
            "replayed_count": replayed_count,
            "filters": {
                "event_type": event_type,
                "start_time": start_time,
                "end_time": end_time,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "task": "replay_events",
            "error": str(e),
        }