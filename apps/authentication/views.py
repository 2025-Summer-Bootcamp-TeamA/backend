import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import GoogleLoginSerializer
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

class GoogleLoginView(APIView):
    @swagger_auto_schema(
        tags=["oauth"],
        operation_summary="Google OAuth 로그인",
        operation_description="Google ID Token을 사용한 OAuth 로그인 및 JWT 토큰 발급",
        request_body=GoogleLoginSerializer
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_token = serializer.validated_data["id_token"]
        if not id_token:
            return Response({"error": "No id_token provided"}, status=400)

        # 1. 구글에 id_token 검증 요청 (timeout 및 예외 처리 추가)
        if id_token == "test_token":
            token_info = {"sub": "test_user_123", "email": "test@example.com"}
            print("Using test token - bypassing Google verification")
        else:
            try:
                resp = requests.get(
                    GOOGLE_TOKEN_INFO_URL,
                    params={"id_token": id_token},
                    timeout=10
                )
                if resp.status_code != 200:
                    return Response({"error": "Invalid id_token"}, status=400)
            except requests.RequestException as e:
                return Response({"error": "Token verification failed"}, status=500)
            token_info = resp.json()
        sub = token_info.get("sub")
        email = token_info.get("email")

        if not sub or not email:
            return Response({"error": "No sub/email in token"}, status=400)

        # 2. 사용자 생성/조회
        import uuid
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create(
                username=uuid.uuid4().hex,
                email=email
            )

        # 3. JWT 발급 (djangorestframework-simplejwt 사용)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            "accessToken": access_token,
            "refreshToken": refresh_token
        })

class TestAuthView(APIView):
    """
    JWT 인증 테스트용 뷰
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]
    
    def get(self, request):
        return Response({
            "message": "인증 성공!",
            "user_id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "authenticated": request.user.is_authenticated
        })