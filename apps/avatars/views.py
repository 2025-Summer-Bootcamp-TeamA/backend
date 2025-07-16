import os
import uuid
import base64
import mimetypes
import requests
from dotenv import load_dotenv

from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# ✅ .env 파일 로드 및 API 키 불러오기
load_dotenv()
VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")

# ✅ VisionStory 아바타 생성 API URL
VISIONSTORY_GENERATE_URL = "https://openapi.visionstory.ai/api/v1/avatar"


@swagger_auto_schema(
    method='post',
    operation_description="이미지를 업로드하면 아바타를 생성합니다 (base64 전송 방식)",
    manual_parameters=[
        openapi.Parameter(
            name="image",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description="업로드할 이미지 파일",
            required=True
        )
    ],
    responses={200: "아바타 생성 결과 반환"},
)
@api_view(['POST'])
@parser_classes([MultiPartParser])
def generate_avatar(request):
    image_file = request.FILES.get("image")
    if not image_file:
        return HttpResponseBadRequest("이미지 파일이 필요합니다.")

    ext = os.path.splitext(image_file.name)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs("media", exist_ok=True)
    save_path = os.path.join("media", filename)

    # 이미지 저장
    with open(save_path, "wb+") as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)

    # MIME 타입 결정
    mime_type, _ = mimetypes.guess_type(save_path)
    if not mime_type:
        mime_type = "image/jpeg"  # 기본값

    # base64로 인코딩
    with open(save_path, "rb") as img:
        encoded_string = base64.b64encode(img.read()).decode("utf-8")

    payload = {
        "inline_data": {
            "mime_type": mime_type,
            "data": encoded_string
        }
    }

    headers = {
        "X-API-Key": VISIONSTORY_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            VISIONSTORY_GENERATE_URL,
            json=payload,
            headers=headers,
            timeout=15
        )
    except requests.exceptions.RequestException as e:
        os.remove(save_path)
        return JsonResponse({
            "success": False,
            "error": "VisionStory 요청 중 예외 발생",
            "detail": str(e)
        }, status=500)

    os.remove(save_path)

    if response.status_code == 200:
        result = response.json()
        return JsonResponse({
            "success": True,
            "avatar_id": result.get("data", {}).get("avatar_id"),
            "thumbnail_url": result.get("data", {}).get("thumbnail_url"),
            "message": result.get("message", "아바타 생성 성공")
        })
    else:
        print("🔥 VisionStory 응답 실패:", response.status_code, response.text)
        return JsonResponse({
            "success": False,
            "error": "아바타 생성 실패",
            "detail": response.text
        }, status=500)
