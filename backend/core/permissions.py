"""
Custom permissions for GrihaStay application
"""
from rest_framework import permissions
from .models import TenantUser


class IsTenantUser(permissions.BasePermission):
    """
    Permission to check if the user is a valid tenant user
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated and is a TenantUser
        if not request.user or not hasattr(request, 'user'):
            return False
        
        # For JWT authentication, user info is in the token
        if hasattr(request, 'auth') and request.auth:
            return True
        
        return False


class IsTenantOwner(permissions.BasePermission):
    """
    Permission to check if the user is the tenant owner/admin
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request, 'user'):
            return False
        
        # Check if user_id exists in JWT token
        if hasattr(request, 'auth') and request.auth:
            user_id = request.auth.get('user_id')
            if user_id:
                try:
                    user = TenantUser.objects.get(id=user_id)
                    return user.role == 'OWNER'
                except TenantUser.DoesNotExist:
                    return False
        
        return False


class IsTenantOwnerOrManager(permissions.BasePermission):
    """
    Permission to check if the user is owner or manager
    """
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request, 'user'):
            return False
        
        if hasattr(request, 'auth') and request.auth:
            user_id = request.auth.get('user_id')
            if user_id:
                try:
                    user = TenantUser.objects.get(id=user_id)
                    return user.role in ['OWNER', 'MANAGER']
                except TenantUser.DoesNotExist:
                    return False
        
        return False


class BelongsToTenant(permissions.BasePermission):
    """
    Object-level permission to check if the object belongs to user's tenant
    """
    
    def has_object_permission(self, request, view, obj):
        if not hasattr(request, 'auth') or not request.auth:
            return False
        
        tenant_id = request.auth.get('tenant_id')
        if not tenant_id:
            return False
        
        # Check if object has a tenant attribute
        if hasattr(obj, 'tenant'):
            return str(obj.tenant.id) == tenant_id
        
        # Check if object has a tenant_id attribute
        if hasattr(obj, 'tenant_id'):
            return str(obj.tenant_id) == tenant_id
        
        # For nested objects (e.g., room -> room_type -> property -> tenant)
        if hasattr(obj, 'property') and hasattr(obj.property, 'tenant'):
            return str(obj.property.tenant.id) == tenant_id
        
        if hasattr(obj, 'room_type') and hasattr(obj.room_type, 'property'):
            return str(obj.room_type.property.tenant.id) == tenant_id
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for owner-level write, others read-only
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owners
        if hasattr(request, 'auth') and request.auth:
            user_id = request.auth.get('user_id')
            if user_id:
                try:
                    user = TenantUser.objects.get(id=user_id)
                    return user.role == 'OWNER'
                except TenantUser.DoesNotExist:
                    return False
        
        return False
