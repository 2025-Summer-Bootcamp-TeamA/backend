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
import json

# GCS 업로드 서비스 import
from apps.gcs.storage_service import upload_image_to_gcs, upload_file_to_gcs, move_gcs_file
from apps.videos.services.visionstory_service import VisionStoryService

load_dotenv()

logger = logging.getLogger(__name__)

VISIONSTORY_API_KEY = os.getenv("VISIONSTORY_API_KEY")
VISIONSTORY_GENERATE_URL = "https://openapi.visionstory.ai/api/v1/avatar"

def _call_visionstory_api(image_url):
    # API 키 확인
    if not VISIONSTORY_API_KEY:
        logger.error("VISIONSTORY_API_KEY가 설정되지 않았습니다.")
        return None
    
    # API 키 일부만 로깅 (보안상)
    api_key_preview = VISIONSTORY_API_KEY[:8] + "..." if len(VISIONSTORY_API_KEY) > 8 else "None"
    logger.info(f"VisionStory API 키 확인: {api_key_preview}")
    
    headers = {
        "X-API-Key": VISIONSTORY_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"img_url": image_url}
    
    logger.info(f"VisionStory API 호출 시작: {image_url}")
    logger.info(f"API URL: {VISIONSTORY_GENERATE_URL}")
    logger.info(f"요청 헤더: {headers}")
    logger.info(f"요청 페이로드: {payload}")
    
    try:
        response = requests.post(
            VISIONSTORY_GENERATE_URL,
            json=payload,
            headers=headers,
            timeout=30  # timeout 증가
        )
        logger.info(f"VisionStory 응답({image_url}): {response.status_code}")
        logger.info(f"VisionStory 응답 내용: {response.text}")
        return response
    except requests.exceptions.Timeout:
        logger.error(f"VisionStory API 호출 타임아웃: {image_url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"VisionStory API 호출 네트워크 에러: {e}")
        return None
    except Exception as e:
        logger.error(f"VisionStory API 호출 예상치 못한 에러: {e}")
        return None

def _generate_prompt(image_url):
    # OpenAI 클라이언트 초기화 (최신 방식)
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = (
        "사용자가 업로드한 이미지를 기반으로, 이미지의 주요 시각적 요소를 요약해 주세요.\n"
        "특히 다음 항목들을 중심으로 구체적으로 설명해 주세요:\n"
        "- 이미지에 작품 윤곽을 정확하게 알려주세요\n"
        "- 이미지의 전체적인 형태나 구조 (예: 원형, 인체, 동물, 조형물 등)\n"
        "- 이미지의 색감이나 분위기 (예: 고대, 현대, 만화 스타일, 사실적 등)\n"
        "- 이미지에 작품의 색깔을 정확하게 알려주세요\n"
        "- 표면 질감이나 재질 (예: 금속, 석재, 유화 느낌 등)\n"
        "- 눈, 코, 입과 같이 사람처럼 보일 수 있는 요소가 존재하는지 여부\n"
        "- 이미지의 중심이 되는 대상과 배경의 구성\n"
        "설명은 최대한 객관적으로, DALL·E가 아바타용 이미지를 생성하는 데 활용할 수 있도록 해 주세요."
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
        logger.info(f"GPT-4o 프롬프트 결과: {result}")
        return result
    except Exception as e:
        logger.error(f"프롬프트 생성 에러: {e}")
        return None

def _generate_dalle_image(prompt_text):
    # OpenAI 클라이언트 초기화 (최신 방식)  
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # 안전하고 명확한 기본 프롬프트
    safe_prompt = (
        "업로드한 이미지를 기반으로 원본의 형태, 구조, 질감을 최대한 그대로 유지해 주세요.\n"
            "새로운 사람을 생성하지 말고, 기존 이미지 위에 눈, 코, 입을 자연스럽게 삽입하거나 선명하게 보완해 주세요.\n"
            "AI가 얼굴로 인식할 수 있도록 눈, 코, 입은 명확하게 표현하고, 어깨 라인을 약간 추가해도 괜찮습니다.\n"
            "결과물이 애니메이션 스타일이더라도 괜찮지만, 반드시 원본 이미지의 구조와 분위기를 유지해야 합니다."
            "눈은 반드시 2개있어야하고 코는 1개있어야하고 입은 1개있어야합니다."
            "어깨 라인은 반드시 있어야합니다."
            "반드시 정면을 바라봐야합니다"
            "사물인경우 그냥 이미지설명을 바탕으로 작품모양과 색깔을 유지한 얼굴을 만들어주세요"
    )
    
    # 사용자 프롬프트가 있으면 결합, 없으면 기본 프롬프트 사용
    final_prompt = f"{prompt_text} {safe_prompt}" if prompt_text else safe_prompt
    
    try:
        dalle_response = client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            n=1,
            size="1024x1024"
        )
        url = dalle_response.data[0].url if dalle_response.data and dalle_response.data[0].url else None
        logger.info(f"DALL·E 3 이미지 URL: {url}")
        return url
    except Exception as e:
        logger.error(f"DALL·E 3 이미지 생성 에러: {e}")
        return None

# GCS 업로드 함수는 apps.gcs.storage_service로 이동됨
# 기존 함수명 호환성을 위한 래퍼 함수
def _upload_image_to_gcs(image_url):
    """DALL·E 이미지 URL을 GCS에 업로드 (기존 호환성)"""
    result = upload_image_to_gcs(image_url, folder="avatars")
    if result:
        logger.info(f"GCS 업로드된 DALL·E 3 이미지 URL: {result}")
        return result
    else:
        logger.error("GCS 업로드 에러: 업로드 실패")
        return None


class AvatarListView(APIView):
    """아바타 목록 조회 및 생성 API"""
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]  # 파일 업로드를 위한 파서 추가
    
    @swagger_auto_schema(
        tags=["avatars"],
        operation_summary="아바타 목록 조회",
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
        tags=["avatars"],
        operation_summary="아바타 생성",
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
                        'used_dalle': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='DALL-E 3 사용 여부', example=False),
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

        # 모킹 모드 확인 (기본값을 false로 변경)
        use_mock = os.getenv("VISIONSTORY_USE_MOCK", "false").lower() == "true"
        
        if use_mock:
            # 모킹 모드에서는 임시로 파일을 메모리에 저장하여 VisionStory API 호출
            import tempfile
            
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # 임시 파일을 VisionStory API에 전달 (실제로는 모킹이므로 호출하지 않음)
            logger.info("🚫 모킹 모드 활성화 - 모의 아바타 데이터 반환")
            import time
            mock_avatar_id = f"mock_avatar_{int(time.time())}"
            
            # 모킹 모드에서도 성공 후 GCS에 저장
            file_url = upload_file_to_gcs(image_file, folder="avatars")
            
            # 임시 파일 삭제
            os.unlink(temp_file_path)
            
            return Response({
                "success": True,
                "avatar_id": mock_avatar_id,
                "thumbnail_url": "https://mock.visionstory.ai/thumbnails/mock_avatar.jpg",
                "uploaded_url": file_url,
                "message": "모의 아바타 생성 성공 (모킹 모드)",
                "used_dalle": False  # 모킹 모드에서는 DALL-E 3 사용 안함
            }, status=status.HTTP_200_OK)
        
        # 실제 VisionStory API 호출을 위해 임시로 파일을 메모리에 저장
        import tempfile
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        try:
            # 임시 파일을 VisionStory API에 전달 (실제로는 URL이 필요하므로 임시 업로드)
            # 실제 구현에서는 임시 스토리지나 직접 파일 업로드 방식을 사용해야 함
            # 여기서는 간단히 임시 GCS 업로드 후 VisionStory API 호출
            
            # 임시 GCS 업로드 (VisionStory API 호출용)
            temp_file_url = upload_file_to_gcs(image_file, folder="temp_avatars")
            if not temp_file_url:
                return Response({
                    "success": False,
                    "error": "임시 이미지 업로드 실패",
                    "message": "이미지를 임시 업로드할 수 없습니다.",
                    "retry_required": True
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # VisionStory API 호출
            logger.info(f"VisionStory API 호출 시작: temp_file_url={temp_file_url}")
            response = _call_visionstory_api(temp_file_url)
            logger.info(f"_call_visionstory_api 반환값: {response}")
            logger.info(f"response 타입: {type(response)}")
            if response is None:
                logger.error("VisionStory API 호출 실패: response가 None")
                return Response({
                    "success": False,
                    "error": "VisionStory API 호출 실패",
                    "message": "VisionStory API 호출에 실패했습니다. API 키 설정을 확인해주세요.",
                    "retry_required": True
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            logger.info(f"VisionStory API 응답 상태코드: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                avatar_id = result.get("data", {}).get("avatar_id")
                
                if avatar_id:
                    # VisionStory API 성공 후 영구 GCS 저장
                    logger.info(f"VisionStory 아바타 생성 성공: {avatar_id}, 영구 GCS 저장 시작")
                    
                    # 임시 폴더에서 영구 폴더로 파일 이동 (재업로드 대신)
                    file_url = move_gcs_file(temp_file_url, "temp_avatars", "avatars")
                    if not file_url:
                        logger.warning("GCS 파일 이동 실패, 임시 URL 사용")
                        file_url = temp_file_url
                    
                    return Response({
                        "success": True,
                        "avatar_id": avatar_id,
                        "thumbnail_url": result.get("data", {}).get("thumbnail_url"),
                        "uploaded_url": file_url,
                        "message": result.get("message", "아바타 생성 성공"),
                        "used_dalle": False  # 원본 이미지로 성공
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "success": False,
                        "error": "아바타 생성 실패",
                        "message": "VisionStory에서 아바타 ID를 받지 못했습니다.",
                        "retry_required": True
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # VisionStory API 실패 - DALL-E 3로 새 이미지 생성 시도
                logger.info(f"VisionStory 아바타 생성 실패 (상태코드: {response.status_code}), DALL-E 3로 새 이미지 생성 시도")
                logger.info(f"VisionStory 실패 응답: {response.text}")
                
                # 원본 이미지로 프롬프트 생성
                logger.info("GPT-4o로 프롬프트 생성 시작")
                prompt = _generate_prompt(temp_file_url)
                if not prompt:
                    logger.error("GPT-4o 프롬프트 생성 실패")
                    return Response({
                        "success": False,
                        "error": "프롬프트 생성 실패",
                        "message": "이미지 분석에 실패했습니다. 다른 이미지를 시도해주세요.",
                        "retry_required": True
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # DALL-E 3로 새 이미지 생성
                logger.info("DALL-E 3 이미지 생성 시작")
                logger.info(f"생성할 프롬프트: {prompt}")
                dalle_image_url = _generate_dalle_image(prompt)
                if not dalle_image_url:
                    logger.error("DALL-E 3 이미지 생성 실패")
                    return Response({
                        "success": False,
                        "error": "DALL-E 3 이미지 생성 실패",
                        "message": "새 이미지 생성에 실패했습니다. 다른 이미지를 시도해주세요.",
                        "retry_required": True
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 생성된 이미지를 GCS에 업로드
                logger.info(f"DALL-E 3 생성 이미지 GCS 업로드 시작: {dalle_image_url}")
                dalle_gcs_url = _upload_image_to_gcs(dalle_image_url)
                if not dalle_gcs_url:
                    logger.error("DALL-E 3 생성 이미지 GCS 업로드 실패")
                    return Response({
                        "success": False,
                        "error": "DALL-E 3 이미지 업로드 실패",
                        "message": "생성된 이미지 업로드에 실패했습니다.",
                        "retry_required": True
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # DALL-E 3로 생성된 이미지로 VisionStory 다시 시도
                logger.info("DALL-E 3 생성 이미지로 VisionStory 재시도")
                retry_response = _call_visionstory_api(dalle_gcs_url)
                
                if retry_response and retry_response.status_code == 200:
                    # 재시도 성공
                    result = retry_response.json()
                    avatar_id = result.get("data", {}).get("avatar_id")
                    
                    if avatar_id:
                        logger.info(f"DALL-E 3 이미지로 VisionStory 아바타 생성 성공: {avatar_id}")
                        
                        return Response({
                            "success": True,
                            "avatar_id": avatar_id,
                            "thumbnail_url": result.get("data", {}).get("thumbnail_url"),
                            "uploaded_url": dalle_gcs_url,
                            "message": "DALL-E 3로 생성된 이미지로 아바타 생성 성공",
                            "used_dalle": True  # DALL-E 3 사용 여부 표시
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            "success": False,
                            "error": "DALL-E 3 이미지 아바타 생성 실패",
                            "message": "새 이미지로도 아바타 생성에 실패했습니다. 다른 이미지를 시도해주세요.",
                            "retry_required": True
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # DALL-E 3 이미지로도 실패
                    error_message = "원본 이미지와 새로 생성된 이미지 모두로 아바타 생성에 실패했습니다."
                    if retry_response:
                        try:
                            error_data = retry_response.json()
                            error_message = error_data.get("message", error_message)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"재시도 응답 파싱 실패: {e}")
                    
                    return Response({
                        "success": False,
                        "error": "VisionStory API 오류 (DALL-E 3 재시도 포함)",
                        "message": error_message,
                        "retry_required": True,
                        "suggestion": "더 선명하고 정면을 바라보는 인물 사진을 업로드해주세요."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
