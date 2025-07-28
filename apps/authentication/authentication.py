from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import jwt
import logging
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if settings.DEBUG:
            logger.debug("=== CustomJWTAuthentication Debug ===")
            logger.debug(f"Request path: {request.path}")
            logger.debug(f"Request method: {request.method}")
        
        auth_header = request.headers.get('Authorization')
        
        if settings.DEBUG:
            logger.debug(f"Authorization header present: {bool(auth_header)}")
        
        if not auth_header:
            if settings.DEBUG:
                logger.debug("No Authorization header found")
            return None
        
        try:
            # "Bearer " 제거
            if not auth_header.startswith('Bearer '):
                if settings.DEBUG:
                    logger.debug("Invalid Authorization header format")
                return None
                
            token = auth_header.split(' ')[1]
            
            if settings.DEBUG:
                logger.debug(f"Token extracted (first 20 chars): {token[:20]}...")
            
            # JWT 토큰 검증 (djangorestframework-simplejwt 방식)
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                
                if settings.DEBUG:
                    logger.debug(f"User ID from token: {user_id}")
                    
            except Exception as e:
                if settings.DEBUG:
                    logger.debug(f"AccessToken validation failed: {str(e)}")
                # 대안: 직접 JWT 디코드
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                
                if settings.DEBUG:
                    logger.debug(f"User ID from direct decode: {user_id}")
            
            # 사용자 조회
            user = User.objects.get(id=user_id)
            
            if settings.DEBUG:
                logger.debug(f"User authenticated successfully: {user.email}")
                logger.debug("=== Authentication Success ===")
                
            return (user, None)
            
        except (IndexError, InvalidToken, TokenError, User.DoesNotExist) as e:
            logger.warning(f"Authentication failed: {str(e)}")
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Unexpected authentication error: {str(e)}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}') 