import os
import uuid
import requests
from dotenv import load_dotenv
import openai
from django.conf import settings
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.files.storage import default_storage
import logging

# GCS 업로드 서비스 import
from apps.gcs.storage_service import upload_image_to_gcs, upload_file_to_gcs
from apps.videos.services.visionstory_service import VisionStoryService

load_dotenv()

logger = logging.getLogger(__name__)

VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")
VISIONSTORY_GENERATE_URL = "https://openapi.visionstory.ai/api/v1/avatar"

def _call_visionstory_api(image_url):
    headers = {
        "X-API-Key": VISIONSTORY_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"img_url": image_url}
    try:
        response = requests.post(
            VISIONSTORY_GENERATE_URL,
            json=payload,
            headers=headers,
            timeout=15
        )
        print(f"VisionStory 응답({image_url}):", response.status_code, response.text)
        return response
    except Exception as e:
        print(f"VisionStory API 호출 에러: {e}")
        return None

def _generate_prompt(image_url):
    # OpenAI 클라이언트 초기화 (최신 방식)
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
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
        gpt_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=500
        )
        result = gpt_response.choices[0].message.content if gpt_response.choices and gpt_response.choices[0].message.content else None
        print("GPT-4o 프롬프트 결과:", result)
        return result
    except Exception as e:
        print(f"프롬프트 생성 에러: {e}")
        return None

def _generate_dalle_image(prompt_text):
    # OpenAI 클라이언트 초기화 (최신 방식)  
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            n=1,
            size="1024x1024"
        )
        url = dalle_response.data[0].url if dalle_response.data and dalle_response.data[0].url else None
        print("DALL·E 3 이미지 URL:", url)
        return url
    except Exception as e:
        print(f"DALL·E 3 이미지 생성 에러: {e}")
        return None

# GCS 업로드 함수는 apps.gcs.storage_service로 이동됨
# 기존 함수명 호환성을 위한 래퍼 함수
def _upload_image_to_gcs(image_url):
    """DALL·E 이미지 URL을 GCS에 업로드 (기존 호환성)"""
    result = upload_image_to_gcs(image_url, folder="avatars")
    if result:
        print("GCS 업로드된 DALL·E 3 이미지 URL:", result)
        return result
    else:
        print("GCS 업로드 에러: 업로드 실패")
        return None


class AvatarListView(APIView):
    """아바타 목록 조회 및 생성 API"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]  # 파일 업로드를 위한 파서 추가
    
    @swagger_auto_schema(
        operation_description="VisionStory에서 사용 가능한 아바타 목록을 조회합니다",
        responses={
            200: openapi.Response(
                description="아바타 목록 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'public_avatars': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                                'my_avatars': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                                'total_cnt': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'latest_avatar_id': openapi.Schema(type=openapi.TYPE_STRING, description='가장 최근 생성된 아바타 ID'),
                            }
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='아바타 목록 조회 성공'),
                    }
                )
            ),
            500: openapi.Response(description="서버 오류")
        }
    )
    def get(self, request):
        """아바타 목록 조회"""
        try:
            logger.info("아바타 목록 조회 요청")
            
            visionstory_service = VisionStoryService()
            avatars_data = visionstory_service.get_avatars()
            
            if not avatars_data:
                return Response(
                    {
                        'success': False,
                        'error': '아바타 목록 조회에 실패했습니다.',
                        'message': 'VisionStory API 호출 실패'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 최신 아바타 ID도 함께 제공
            latest_avatar_id = visionstory_service.get_latest_avatar_id()
            
            # 응답 데이터 구성
            response_data = avatars_data.get('data', {})
            response_data['latest_avatar_id'] = latest_avatar_id
            
            logger.info(f"아바타 목록 조회 성공: latest_avatar_id={latest_avatar_id}")
            
            return Response(
                {
                    'success': True,
                    'data': response_data,
                    'message': '아바타 목록 조회 성공'
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"아바타 목록 조회 중 오류 발생: {e}")
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'message': '아바타 목록 조회 중 오류가 발생했습니다.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
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
    def post(self, request):
        """아바타 생성"""
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({
                "success": False, 
                "error": "이미지 파일이 필요합니다.",
                "retry_required": True
            }, status=status.HTTP_400_BAD_REQUEST)

        # GCS 서비스를 사용하여 이미지 업로드
        file_url = upload_file_to_gcs(image_file, folder="avatars")
        if not file_url:
            return Response({
                "success": False, 
                "error": "이미지 업로드 실패", 
                "message": "이미지를 업로드할 수 없습니다.",
                "retry_required": True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print("원본 이미지 GCS URL:", file_url)

        # 1차 VisionStory 시도 - 크레딧 절약을 위해 주석처리
        # response = _call_visionstory_api(file_url)
        # if not response:
        #     return Response({
        #         "success": False,
        #         "error": "VisionStory API 호출 실패",
        #         "message": "VisionStory API 호출에 실패했습니다.",
        #         "retry_required": True
        #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # if response.status_code == 200:
        #     result = response.json()
        #     return Response({
        #         "success": True,
        #         "avatar_id": result.get("data", {}).get("avatar_id"),
        #         "thumbnail_url": result.get("data", {}).get("thumbnail_url"),
        #         "uploaded_url": file_url,
        #         "message": result.get("message", "아바타 생성 성공")
        #     }, status=status.HTTP_200_OK)
        
        # 모의 아바타 생성 성공 응답 (크레딧 절약용)
        logger.info("🚫 VisionStory 아바타 API 호출이 주석처리됨 - 모의 데이터 반환")
        import time
        mock_avatar_id = f"mock_avatar_{int(time.time())}"
        return Response({
            "success": True,
            "avatar_id": mock_avatar_id,
            "thumbnail_url": "https://mock.visionstory.ai/thumbnails/mock_avatar.jpg",
            "uploaded_url": file_url,
            "message": "모의 아바타 생성 성공 (크레딧 절약 모드)"
        }, status=status.HTTP_200_OK)
