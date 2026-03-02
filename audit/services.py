from .models import AuditEvent


def log_event(user, action, entity_type, entity_id=None, description=None):
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
        print(f"Warning: Audit event for action '{action}' has no org")
    
    AuditEvent.objects.create(
    user=user,
    action=action,
    entity_type=entity_type,
    entity_id=entity_id,
    description=description
)
AuditLog = AuditEvent


