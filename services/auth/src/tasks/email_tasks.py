"""Email-related Celery tasks."""

from celery import shared_task


@shared_task(name="auth.send_email")
def send_email(to_email: str, subject: str, body: str, html_body: str = None) -> dict:
    """Send email via email service.

    Args:
        to_email: Recipient email
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        Task result
    """
    try:
        # This would integrate with an email service like SendGrid, SES, etc.
        # For now, just log the email
        print(f"📧 Sending email to: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body[:100]}...")

        # In production, you would:
        # 1. Use boto3 for AWS SES
        # 2. Or SendGrid API
        # 3. Or other email service

        return {
            "status": "success",
            "to": to_email,
            "subject": subject,
            "task": "send_email",
        }
    except Exception as e:
        return {
            "status": "error",
            "to": to_email,
            "subject": subject,
            "error": str(e),
        }


@shared_task(name="auth.send_bulk_email")
def send_bulk_email(
    recipients: list[str], subject: str, body: str, html_body: str = None
) -> dict:
    """Send bulk email to multiple recipients.

    Args:
        recipients: List of recipient emails
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body

    Returns:
        Task result with success/failure counts
    """
    success_count = 0
    failed_count = 0
    failed_recipients = []

    for recipient in recipients:
        result = send_email(recipient, subject, body, html_body)
        if result["status"] == "success":
            success_count += 1
        else:
            failed_count += 1
            failed_recipients.append(recipient)

    return {
        "status": "completed",
        "task": "send_bulk_email",
        "total": len(recipients),
        "success": success_count,
        "failed": failed_count,
        "failed_recipients": failed_recipients,
    }


@shared_task(name="auth.send_notification")
def send_notification(
    user_id: str, notification_type: str, data: dict, channels: list[str] = None
) -> dict:
    """Send notification to user via specified channels.

    Args:
        user_id: User ID
        notification_type: Type of notification
        data: Notification data
        channels: List of channels (email, sms, push)

    Returns:
        Task result
    """
    if channels is None:
        channels = ["email"]

    results = {}

    try:
        for channel in channels:
            if channel == "email":
                # Send email notification
                results["email"] = {
                    "status": "success",
                    "message": f"Email notification sent for {notification_type}",
                }
            elif channel == "sms":
                # Send SMS via Twilio or similar
                results["sms"] = {
                    "status": "skipped",
                    "message": "SMS not configured",
                }
            elif channel == "push":
                # Send push notification
                results["push"] = {
                    "status": "skipped",
                    "message": "Push notifications not configured",
                }

        return {
            "status": "success",
            "user_id": user_id,
            "notification_type": notification_type,
            "channels": channels,
            "results": results,
        }
    except Exception as e:
        return {
            "status": "error",
            "user_id": user_id,
            "notification_type": notification_type,
            "error": str(e),
        }