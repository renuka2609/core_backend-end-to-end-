"""
Centralized role and permission constants to ensure consistency across the application.
"""

# Role choices
class Roles:
    """Standard role constants"""
    ADMIN = "admin"
    REVIEWER = "reviewer"
    VENDOR = "vendor"
    
    CHOICES = [
        (ADMIN, "Admin"),
        (REVIEWER, "Reviewer"),
        (VENDOR, "Vendor"),
    ]
    
    ALL_ROLES = [ADMIN, REVIEWER, VENDOR]


# Permission constants
class Permissions:
    """Permission mappings by role"""
    
    # Admin can do everything
    ADMIN_PERMISSIONS = [
        "create_template",
        "update_template",
        "delete_template",
        "create_assessment",
        "update_assessment",
        "submit_assessment",
        "review_assessment",
        "approve_assessment",
        "create_vendor",
        "update_vendor",
    ]
    
    # Reviewer can view and review
    REVIEWER_PERMISSIONS = [
        "review_assessment",
        "approve_assessment",
    ]
    
    # Vendor can create responses and submit
    VENDOR_PERMISSIONS = [
        "submit_assessment",
    ]
    
    @classmethod
    def can_perform(cls, role: str, action: str) -> bool:
        """Check if a role can perform an action"""
        if role == Roles.ADMIN:
            return action in cls.ADMIN_PERMISSIONS
        elif role == Roles.REVIEWER:
            return action in cls.REVIEWER_PERMISSIONS
        elif role == Roles.VENDOR:
            return action in cls.VENDOR_PERMISSIONS
        return False
