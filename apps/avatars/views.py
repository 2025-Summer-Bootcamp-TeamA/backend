import os
import uuid
import requests
from dotenv import load_dotenv
import openai
from django.core.files.base import ContentFile
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, parser_classes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.files.storage import default_storage

# ✅ .env 파일 로드 및 API 키 불러오기
load_dotenv()
VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")

# ✅ VisionStory 아바타 생성 API URL
VISIONSTORY_GENERATE_URL = "https://openapi.visionstory.ai/api/v1/avatar"


@swagger_auto_schema(
    method='post',
    operation_description="이미지를 업로드하면 아바타를 생성합니다",
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
    print("views.py OPENAI_API_KEY:", settings.OPENAI_API_KEY)
    image_file = request.FILES.get("image")
    if not image_file:
        return HttpResponseBadRequest("이미지 파일이 필요합니다.")

    ext = os.path.splitext(image_file.name)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = f"avatars/{filename}"

    # GCS에 이미지 저장
    file_path = default_storage.save(save_path, image_file)
    file_url = default_storage.url(file_path)
    print("file_url:", file_url)

    # base64 및 mimetypes 관련 코드 삭제됨

    payload = {
        "img_url": file_url
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
        return JsonResponse({
            "success": False,
            "error": "VisionStory 요청 중 예외 발생",
            "detail": str(e)
        }, status=500)

    # default_storage.delete(file_path)  # 삭제 코드 제거

    if response.status_code == 200:
        result = response.json()
        return JsonResponse({
            "success": True,
            "avatar_id": result.get("data", {}).get("avatar_id"),
            "thumbnail_url": result.get("data", {}).get("thumbnail_url"),
            "uploaded_url": file_url,
            "message": result.get("message", "아바타 생성 성공")
        })
    else:
        # VisionStory 실패 시 대체 생성 로직
        # 1. 프롬프트 생성 (GPT-4o)
        openai.api_key = settings.OPENAI_API_KEY
        prompt = "이 이미지를 한 문장으로 설명해줘."
        try:
            gpt_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": file_url}}
                        ]
                    }
                ],
                max_tokens=300
            )
            prompt_text = gpt_response.choices[0].message.content if gpt_response.choices and gpt_response.choices[0].message.content else None
        except Exception as e:
            return JsonResponse({"success": False, "error": f"프롬프트 생성 실패: {str(e)}"}, status=500)

        if not prompt_text:
            return JsonResponse({"success": False, "error": "프롬프트 생성 결과가 없습니다."}, status=500)

        # 2. DALL·E 3로 이미지 생성
        try:
            dalle_response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt_text,
                n=1,
                size="1024x1024"
            )
            dalle_image_url = dalle_response.data[0].url if dalle_response.data and dalle_response.data[0].url else None
        except Exception as e:
            return JsonResponse({"success": False, "error": f"DALL·E 3 이미지 생성 실패: {str(e)}"}, status=500)

        if not dalle_image_url:
            return JsonResponse({"success": False, "error": "DALL·E 3 이미지 URL이 없습니다."}, status=500)

        # 3. DALL·E 3 이미지 다운로드 및 GCS 업로드
        try:
            image_content = requests.get(dalle_image_url).content
            dalle_filename = f"avatars/dalle_{uuid.uuid4().hex}.png"
            gcs_path = default_storage.save(dalle_filename, ContentFile(image_content))
            gcs_url = default_storage.url(gcs_path)
        except Exception as e:
            return JsonResponse({"success": False, "error": f"GCS 업로드 실패: {str(e)}"}, status=500)

        # 4. VisionStory에 재시도
        payload_retry = {
            "img_url": gcs_url
        }
        try:
            retry_response = requests.post(
                VISIONSTORY_GENERATE_URL,
                json=payload_retry,
                headers=headers,
                timeout=15
            )
            if retry_response.status_code == 200:
                result = retry_response.json()
                return JsonResponse({
                    "success": True,
                    "avatar_id": result.get("data", {}).get("avatar_id"),
                    "thumbnail_url": result.get("data", {}).get("thumbnail_url"),
                    "uploaded_url": gcs_url,
                    "message": "VisionStory 실패, DALL·E 3로 대체 생성 후 성공"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": "VisionStory 재시도 실패",
                    "detail": retry_response.text
                }, status=500)
        except Exception as e:
            return JsonResponse({"success": False, "error": f"VisionStory 재시도 중 예외: {str(e)}"}, status=500)
