"""
Assessment State Transition Service

Implements strict state machine with audit trail for assessment workflow:
  assigned → submitted → reviewed → {approved | remediation} → ...
  
All state transitions are logged to AuditEvent for immutable tracking.
"""

import json
from typing import Tuple
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Assessment
from audit.models import AuditEvent

User = get_user_model()


class StateTransitionError(Exception):
    """Raised when invalid state transition is attempted."""
    pass


class AssessmentStateTransitionService:
    """Service for managing assessment state transitions with audit logging."""
    
    @staticmethod
    def can_transition(assessment: Assessment, new_status: str) -> Tuple[bool, str]:
        """
        Check if transition is valid.
        Returns: (is_valid, error_message)
        """
        if new_status == assessment.status:
            return True, ""
        
        if new_status not in dict(Assessment.STATUS):
            return False, f"Invalid status: {new_status}"
        
        valid_transitions = assessment.VALID_TRANSITIONS.get(assessment.status, [])
        if new_status not in valid_transitions:
            return False, (
                f"Cannot transition from '{assessment.status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(valid_transitions) if valid_transitions else 'none (final state)'}"
            )
        
        return True, ""
    
    @staticmethod
    @transaction.atomic
    def transition(
        assessment: Assessment,
        new_status: str,
        actor_user: User,
        metadata: dict = None
    ) -> Assessment:
        """
        Execute state transition with audit logging.
        
        Args:
            assessment: Assessment instance to transition
            new_status: Target status
            actor_user: User performing the transition
            metadata: Additional context (e.g., request data, reason)
        
        Returns:
            Updated assessment
        
        Raises:
            StateTransitionError: If transition is invalid
        """
        is_valid, error_msg = AssessmentStateTransitionService.can_transition(assessment, new_status)
        if not is_valid:
            raise StateTransitionError(error_msg)
        
        old_status = assessment.status
        assessment.status = new_status
        assessment.save()
        
        # Log audit event
        audit_metadata = {
            "resource": "assessment",
            "resource_id": assessment.id,
            "action": "state_transition",
            "old_value": old_status,
            "new_value": new_status,
            "vendor_id": assessment.vendor_id,
            "template_id": assessment.template_id,
        }
        
        if metadata:
            audit_metadata.update(metadata)
        
        AuditEvent.objects.create(
            user=actor_user,
            action=f"assessment_transitioned: {old_status} → {new_status}",
            metadata=json.dumps(audit_metadata),
            resource_type="assessment",
            resource_id=assessment.id,
        )
        
        return assessment
    
    @staticmethod
    def get_valid_next_states(assessment: Assessment) -> list:
        """Get list of valid next states for current assessment."""
        return assessment.VALID_TRANSITIONS.get(assessment.status, [])
