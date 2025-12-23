"""
Authentication views for GrihaStay application
"""
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import TenantRegistrationSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that uses TenantUser model
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_tenant(request):
    serializer = TenantRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        result = serializer.save()
        user = result['user']
        tenant = result['tenant']

        # Generate JWT
        refresh = RefreshToken.for_user(user)
        refresh['tenant_id'] = str(tenant.id)
        refresh['role'] = user.role
        refresh['user_name'] = user.user_name

        return Response({
            'message': 'Tenant and admin user created successfully',
            'tenant': {
                'id': str(tenant.id),
                'name': tenant.name,
                'contact_email': tenant.contact_email,
                'currency': tenant.currency,
                'timezone': tenant.timezone,
            },
            'user': {
                'id': str(user.id),
                'user_name': user.user_name,
                # 'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint returning JWT tokens.
    Payload: {"user_name": "...", "password": "..."}
    """
    serializer = CustomTokenObtainPairSerializer(data=request.data)

    try:
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    except serializers.ValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'GrihaStay API is running'
    }, status=status.HTTP_200_OK)
