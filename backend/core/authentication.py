from rest_framework_simplejwt.authentication import JWTAuthentication

from core.models import TenantUser


class TenantJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        try:
            return TenantUser.objects.get(id=user_id)
        except TenantUser.DoesNotExist:
            return None