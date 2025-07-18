import requests
import jwt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import GoogleLoginSerializer
from drf_yasg.utils import swagger_auto_schema

GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

class GoogleLoginView(APIView):
    @swagger_auto_schema(request_body=GoogleLoginSerializer)
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_token = serializer.validated_data["id_token"]
        if not id_token:
            return Response({"error": "No id_token provided"}, status=400)

        # 1. 구글에 id_token 검증 요청
        resp = requests.get(GOOGLE_TOKEN_INFO_URL, params={"id_token": id_token})
        if resp.status_code != 200:
            return Response({"error": "Invalid id_token"}, status=400)
        token_info = resp.json()
        sub = token_info.get("sub")
        email = token_info.get("email")

        if not sub or not email:
            return Response({"error": "No sub/email in token"}, status=400)

        # 2. 사용자 생성/조회
        User = get_user_model()
        user, created = User.objects.get_or_create(username=sub, defaults={"email": email})

        # 3. JWT 발급
        payload = {"user_id": user.id, "sub": sub}
        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        return Response({"token": jwt_token})