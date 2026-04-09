from .models import AuditEvent


def log_event(user, action, resource_type, resource_id=None, metadata=None):
    """
    Log an audit event.

    Args:
        user: The user performing the action
        action: The action being logged
        resource_type: The type of resource affected
        resource_id: The ID of the resource being acted upon
        metadata: Additional metadata about the action

    Returns:
        AuditEvent: The created audit log entry
    """
    org = getattr(user, "org", None)

    if not org:
        # Don't fail if org is missing, but log it for review
        print(f"Warning: Audit event for action '{action}' has no org")

    return AuditEvent.objects.create(
        user=user,
        org=org,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata
    )



