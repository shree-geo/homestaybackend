from rest_framework_simplejwt.authentication import JWTAuthentication

class TenantJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        return None
