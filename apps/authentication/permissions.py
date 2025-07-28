import logging
from django.conf import settings
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

class DebugIsAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        if settings.DEBUG:
            logger.debug("=== DebugIsAuthenticated ===")
            logger.debug(f"User authenticated: {request.user.is_authenticated}")
            logger.debug(f"User ID: {getattr(request.user, 'id', 'No ID')}")
            logger.debug(f"View: {view.__class__.__name__}")
            logger.debug(f"Request path: {request.path}")
        
        result = super().has_permission(request, view)
        
        if settings.DEBUG:
            logger.debug(f"Permission result: {result}")
            logger.debug("=== End DebugIsAuthenticated ===")
        
        return result 