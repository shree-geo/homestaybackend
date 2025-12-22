from rest_framework import permissions
from .models import TenantUser
from uuid import UUID


class IsTenantUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            return False

        return True

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
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.tenant)

    def has_object_permission(self, request, view, obj):
        tenant = getattr(request.user, 'tenant', None)
        if not tenant:
            return False

        if hasattr(obj, 'tenant'):
            return obj.tenant_id == tenant.id
        if hasattr(obj, 'property') and hasattr(obj.property, 'tenant'):
            return obj.property.tenant.id == tenant.id
        if hasattr(obj, 'room_type') and hasattr(obj.room_type, 'property') and hasattr(obj.room_type.property, 'tenant'):
            return obj.room_type.property.tenant.id == tenant.id

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
