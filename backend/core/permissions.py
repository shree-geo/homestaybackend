from rest_framework import permissions
from .models import TenantUser
from uuid import UUID


class IsTenantUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth)


class IsTenantOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.auth:
            return False

        user_id = request.auth.get('user_id')
        if not user_id:
            return False

        try:
            user = TenantUser.objects.get(id=UUID(user_id))
            return user.role == 'OWNER'
        except TenantUser.DoesNotExist:
            return False


class IsTenantOwnerOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.auth:
            return False

        user_id = request.auth.get('user_id')
        if not user_id:
            return False

        try:
            user = TenantUser.objects.get(id=UUID(user_id))
            return user.role in ['OWNER', 'MANAGER']
        except TenantUser.DoesNotExist:
            return False


class BelongsToTenant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.auth:
            return False

        tenant_id = request.auth.get('tenant_id')
        if not tenant_id:
            return False

        if hasattr(obj, 'tenant'):
            return str(obj.tenant.id) == tenant_id

        if hasattr(obj, 'tenant_id'):
            return str(obj.tenant_id) == tenant_id

        if hasattr(obj, 'property') and hasattr(obj.property, 'tenant'):
            return str(obj.property.tenant.id) == tenant_id

        if hasattr(obj, 'room_type') and hasattr(obj.room_type, 'property'):
            return str(obj.room_type.property.tenant.id) == tenant_id

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.auth)

        if not request.auth:
            return False

        user_id = request.auth.get('user_id')
        try:
            user = TenantUser.objects.get(id=UUID(user_id))
            return user.role == 'OWNER'
        except TenantUser.DoesNotExist:
            return False
