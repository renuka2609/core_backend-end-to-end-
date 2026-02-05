from .models import AuditLog


def log_event(user, action, object_id=None, metadata=None):
    """
    Log an audit event
    
    Args:
        user: The user performing the action
        action: The action being logged (e.g., 'create_assessment', 'submit_assessment')
        object_id: The ID of the object being acted upon
        metadata: Additional metadata about the action
    
    Returns:
        AuditLog: The created audit log entry
    """
    org = getattr(user, "org", None)
    
    if not org:
        # Don't fail if org is missing, but log it
        print(f"Warning: Audit log for action '{action}' has no org")
    
    return AuditLog.objects.create(
        user=user,
        action=action,
        object_id=object_id,
        org=org,
        metadata=metadata or {}
    )


