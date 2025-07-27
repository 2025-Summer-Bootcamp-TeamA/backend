import logging

logger = logging.getLogger(__name__)

class JWTAuthDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("=== JWTAuthDebugMiddleware ===")
        print(f"Request path: {request.path}")
        print(f"Request method: {request.method}")
        print(f"Authorization header: {request.headers.get('Authorization')}")
        print(f"All headers: {dict(request.headers)}")
        
        response = self.get_response(request)
        
        print(f"Response status: {response.status_code}")
        print(f"User authenticated: {getattr(request, 'user', None)}")
        print(f"User type: {type(getattr(request, 'user', None))}")
        print("=== End JWTAuthDebugMiddleware ===")
        
        return response 