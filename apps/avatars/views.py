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
    operation_description="이미지를 업로드하면 아바타를 생성합니다. 실패 시 다른 이미지 업로드를 요청합니다.",
    manual_parameters=[
        openapi.Parameter(
            name="image",
            in_=openapi.IN_FORM,
            type=openapi.TYPE_FILE,
            description="업로드할 이미지 파일 (선명하고 정면을 바라보는 인물 사진 권장)",
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="아바타 생성 성공",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                    'avatar_id': openapi.Schema(type=openapi.TYPE_STRING, description='생성된 아바타 ID'),
                    'thumbnail_url': openapi.Schema(type=openapi.TYPE_STRING, description='아바타 썸네일 URL'),
                    'uploaded_url': openapi.Schema(type=openapi.TYPE_STRING, description='업로드된 원본 이미지 URL'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='성공 메시지'),
                }
            )
        ),
        400: openapi.Response(
            description="아바타 생성 실패 - 다른 이미지 필요",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='에러 타입'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='사용자에게 보여줄 메시지'),
                    'retry_required': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True, description='새 이미지 업로드 필요'),
                    'suggestion': openapi.Schema(type=openapi.TYPE_STRING, description='개선 제안'),
                }
            )
        ),
        500: openapi.Response(
            description="서버 오류",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='에러 타입'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='사용자에게 보여줄 메시지'),
                    'retry_required': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True, description='새 이미지 업로드 필요'),
                    'detail': openapi.Schema(type=openapi.TYPE_STRING, description='상세 에러 정보'),
                }
            )
        )
    },
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
            "error": "아바타 생성 서비스 연결 실패",
            "message": "현재 이미지로는 아바타를 생성할 수 없습니다. 다른 이미지를 업로드해주세요.",
            "retry_required": True,
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
        prompt = (
            "한국어로 대답해줘. 이 이미지를 바탕으로 다음 항목에 대해 매우 구체적으로 설명해줘:\n\n"
            "- 주요 인물 또는 중심 객체는 무엇이며, 외형적 특징은 어떤가요?\n"
            "- 배경은 어떤 장소이며, 그 분위기와 색감은 어떤가요?\n"
            "- 전체적인 스타일은 현실적인가요, 예술적인가요, 고전적인가요?\n"
            "- 조명, 그림자, 구도는 어떤 느낌인가요?\n\n"
            "⚠️ 주의: 이 설명은 'VisionStory'라는 AI 영상 생성 시스템에서 인식 가능한 **아바타 이미지 생성**에 사용됩니다.\n"
            "따라서 반드시 아래 조건을 충족하도록 묘사해줘:\n"
            "- 사람의 얼굴이 정면을 바라보고 있어야 함\n"
            "- 상반신이 명확히 드러나야 함 (허리 위 중심)\n"
            "- 배경은 흐릿하거나 단색 등으로 단순하게 표현되어야 함\n"
            "- 전체적으로 뚜렷하고 선명한 이미지여야 함\n\n"
            "이 모든 요소를 하나의 자연스러운 문단으로 통합해서 작성해줘. "
            "너무 예술적인 표현보다는, 구체적이고 사실적인 묘사로 구성해줘. "
            "결과는 DALL·E 3 이미지 생성 프롬프트로 바로 사용할 예정이야."
        )

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
                max_tokens=500
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
                # 재시도 실패 시 사용자에게 새로운 이미지 요청
                return JsonResponse({
                    "success": False,
                    "error": "아바타 생성 실패",
                    "message": "현재 이미지로는 아바타를 생성할 수 없습니다. 다른 이미지를 업로드해주세요.",
                    "retry_required": True,
                    "suggestion": "더 선명하고 정면을 바라보는 인물 사진을 사용해보세요."
                }, status=400)
        except Exception as e:
            return JsonResponse({
                "success": False, 
                "error": "아바타 생성 중 오류 발생",
                "message": "현재 이미지로는 아바타를 생성할 수 없습니다. 다른 이미지를 업로드해주세요.",
                "retry_required": True,
                "detail": str(e)
            }, status=500)
