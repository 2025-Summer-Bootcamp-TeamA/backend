import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)

class JWTAuthDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            logger.debug("=== JWTAuthDebugMiddleware ===")
            logger.debug(f"Request path: {request.path}")
            logger.debug(f"Request method: {request.method}")
            
            # 민감한 정보 마스킹
            auth_header = request.headers.get('Authorization', '')
            if auth_header:
                masked_auth = re.sub(r'Bearer\s+(.{10})', r'Bearer \1***', auth_header)
                logger.debug(f"Authorization header: {masked_auth}")
        
        response = self.get_response(request)
        
        if settings.DEBUG:
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"User authenticated: {getattr(request, 'user', 'AnonymousUser').is_authenticated}")
            logger.debug(f"User ID: {getattr(getattr(request, 'user', None), 'id', 'None')}")
            logger.debug("=== End JWTAuthDebugMiddleware ===")
        
        return response 