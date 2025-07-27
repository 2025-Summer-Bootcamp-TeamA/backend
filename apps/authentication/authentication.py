from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import jwt
from django.conf import settings

User = get_user_model()

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        print("=== CustomJWTAuthentication Debug ===")
        print(f"Request path: {request.path}")
        print(f"Request method: {request.method}")
        
        # 모든 헤더 출력
        print("=== All Headers ===")
        for key, value in request.headers.items():
            print(f"{key}: {value}")
        print("=== End Headers ===")
        
        auth_header = request.headers.get('Authorization')
        print(f"Authorization header: {auth_header}")
        
        if not auth_header:
            print("No Authorization header found")
            return None
        
        try:
            # "Bearer " 제거
            if not auth_header.startswith('Bearer '):
                print("Invalid Authorization header format")
                return None
                
            token = auth_header.split(' ')[1]
            print(f"Extracted token: {token[:50]}...")
            
            # JWT 토큰 검증 (djangorestframework-simplejwt 방식)
            try:
                access_token = AccessToken(token)
                user_id = access_token['user_id']
                print(f"User ID from token: {user_id}")
            except Exception as e:
                print(f"AccessToken validation failed: {str(e)}")
                # 대안: 직접 JWT 디코드
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                print(f"User ID from direct decode: {user_id}")
            
            # 사용자 조회
            user = User.objects.get(id=user_id)
            print(f"User found: {user.email}")
            print("=== Authentication Success ===")
            return (user, None)
            
        except (IndexError, InvalidToken, TokenError, User.DoesNotExist) as e:
            print(f"Authentication failed: {str(e)}")
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}') 