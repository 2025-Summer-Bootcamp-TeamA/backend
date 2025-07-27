from rest_framework.permissions import IsAuthenticated

class DebugIsAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        print("=== DebugIsAuthenticated ===")
        print(f"User: {request.user}")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"User ID: {getattr(request.user, 'id', 'No ID')}")
        print(f"View: {view.__class__.__name__}")
        print(f"Request path: {request.path}")
        
        result = super().has_permission(request, view)
        print(f"Permission result: {result}")
        print("=== End DebugIsAuthenticated ===")
        
        return result 