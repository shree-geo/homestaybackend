"""
Middleware for tenant-based multi-tenancy
"""
import threading

# Thread-local storage for tenant context
_thread_locals = threading.local()


def get_current_tenant():
    """Get the current tenant from thread-local storage"""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage"""
    _thread_locals.tenant = tenant


class TenantMiddleware:
    """
    Middleware to set tenant context for each request
    Tenant can be identified via:
    1. X-Tenant-Id header (for API requests)
    2. JWT token claims
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        
        # Try to get tenant from header
        tenant_id = request.headers.get('X-Tenant-Id')
        
        # Try to get tenant from authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'tenant'):
                tenant = request.user.tenant
        
        # If tenant_id is provided in header, validate it
        if tenant_id and tenant:
            if str(tenant.id) != tenant_id:
                # Mismatch between user's tenant and requested tenant
                tenant = None
        
        # Set tenant in thread-local storage
        set_current_tenant(tenant)
        
        # Store tenant in request for easy access
        request.tenant = tenant
        
        response = self.get_response(request)
        
        # Clean up thread-local storage
        set_current_tenant(None)
        
        return response
