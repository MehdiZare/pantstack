"""Auth service public API."""

from shared.core.registry import SecurityGroup, ServiceManifest, ServiceRoute

# Create service manifest
SERVICE_MANIFEST = ServiceManifest(
    service_name="auth",
    version="1.0.0",
    routes=[
        ServiceRoute(
            path="/auth/login",
            method="POST",
            handler=None,
            security_group=SecurityGroup.PUBLIC,
        ),
        ServiceRoute(
            path="/auth/register",
            method="POST",
            handler=None,
            security_group=SecurityGroup.PUBLIC,
        ),
        ServiceRoute(
            path="/auth/verify",
            method="POST",
            handler=None,
            security_group=SecurityGroup.PUBLIC,
        ),
        ServiceRoute(
            path="/auth/refresh",
            method="POST",
            handler=None,
            security_group=SecurityGroup.AUTHENTICATED,
        ),
        ServiceRoute(
            path="/auth/logout",
            method="POST",
            handler=None,
            security_group=SecurityGroup.AUTHENTICATED,
        ),
    ],
    tasks=[
        "auth.process_user_registration",
        "auth.cleanup_inactive_users",
        "auth.send_verification_email",
        "auth.rotate_api_keys",
        "auth.audit_user_activity",
        "auth.sync_user_permissions",
        "auth.generate_auth_report",
        "auth.process_password_reset",
    ],
    handlers=[],
)

__all__ = ["SERVICE_MANIFEST"]
