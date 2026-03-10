"""
Tenant-aware query guard mixins for enforcing multi-tenant data isolation.

This module provides mixins that ensure all list and detail endpoints
only return data belonging to the current user's tenant/organization.
"""

from rest_framework.exceptions import NotFound, PermissionDenied


class TenantAwareQueryGuardMixin:
    """
    Mixin for ViewSets to enforce tenant-aware query filtering.
    
    Ensures that:
    1. List queries only return objects belonging to the user's tenant/org
    2. Detail queries verify object belongs to user's tenant/org before access
    3. Cross-tenant access attempts are denied
    
    Subclasses should define:
    - tenant_filter_field: The field name to filter by (e.g., 'org', 'org_id', 'tenant_id')
    - tenant_lookup_path: For nested relations (e.g., 'assessment__org' for Evidence)
    """
    
    # Override these in subclass if needed
    tenant_filter_field = 'org'  # Default field to filter by
    tenant_lookup_path = None     # For nested lookups
    
    def get_tenant_value(self):
        """Extract tenant value from the current user's request."""
        user = self.request.user
        
        # Try common tenant attributes
        if hasattr(user, 'org') and user.org:
            return user.org
        if hasattr(user, 'org_id') and user.org_id:
            return user.org_id
        if hasattr(user, 'tenant_id') and user.tenant_id:
            return user.tenant_id
        if hasattr(user, 'tenant') and user.tenant:
            return user.tenant
        
        raise PermissionDenied("User has no associated tenant/organization")
    
    def get_queryset(self):
        """
        Override to apply tenant filtering to all queries.
        """
        queryset = super().get_queryset()
        
        if not self.request.user or not self.request.user.is_authenticated:
            return queryset.none()
        
        tenant_value = self.get_tenant_value()
        
        # Use tenant_lookup_path if defined (for nested relationships)
        if self.tenant_lookup_path:
            filter_kwargs = {self.tenant_lookup_path: tenant_value}
        else:
            filter_kwargs = {self.tenant_filter_field: tenant_value}
        
        return queryset.filter(**filter_kwargs)
    
    def get_object(self):
        """
        Override to verify object belongs to tenant before returning.
        Prevents direct access to cross-tenant objects via detail endpoints.
        """
        obj = super().get_object()
        
        # Verify the object belongs to the user's tenant
        if not self._verify_object_belongs_to_tenant(obj):
            raise PermissionDenied(
                "You do not have permission to access this resource. "
                "It belongs to a different organization."
            )
        
        return obj
    
    def _verify_object_belongs_to_tenant(self, obj):
        """
        Verify that an object belongs to the current user's tenant.
        """
        tenant_value = self.get_tenant_value()
        
        # Check direct tenant relationship
        if self.tenant_lookup_path:
            # Navigate nested relationship
            attrs = self.tenant_lookup_path.split('__')
            current_obj = obj
            try:
                for attr in attrs:
                    current_obj = getattr(current_obj, attr)
                return current_obj == tenant_value
            except AttributeError:
                return False
        else:
            # Check simple attribute
            obj_tenant = getattr(obj, self.tenant_filter_field, None)
            return obj_tenant == tenant_value


class TenantFilterPermission:
    """
    Object-level permission to check tenant membership.
    Can be combined with TenantAwareQueryGuardMixin.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user's tenant matches object's tenant.
        """
        user = request.user
        
        if not user or not user.is_authenticated:
            return False
        
        # Get user's tenant
        user_tenant = None
        if hasattr(user, 'org') and user.org:
            user_tenant = user.org
        elif hasattr(user, 'org_id') and user.org_id:
            user_tenant = user.org_id
        elif hasattr(user, 'tenant_id') and user.tenant_id:
            user_tenant = user.tenant_id
        elif hasattr(user, 'tenant') and user.tenant:
            user_tenant = user.tenant
        
        if not user_tenant:
            return False
        
        # Get object's tenant (try multiple possible fields)
        obj_tenant = None
        if hasattr(obj, 'org') and obj.org:
            obj_tenant = obj.org
        elif hasattr(obj, 'org_id') and obj.org_id:
            obj_tenant = obj.org_id
        elif hasattr(obj, 'tenant_id') and obj.tenant_id:
            obj_tenant = obj.tenant_id
        elif hasattr(obj, 'tenant') and obj.tenant:
            obj_tenant = obj.tenant
        elif hasattr(obj, 'assessment') and hasattr(obj.assessment, 'org'):
            # Handle nested assessment relationship (Evidence, Response)
            obj_tenant = obj.assessment.org
        elif hasattr(obj, 'assessment') and hasattr(obj.assessment, 'org_id'):
            obj_tenant = obj.assessment.org_id
        
        if not obj_tenant:
            return False
        
        return obj_tenant == user_tenant
