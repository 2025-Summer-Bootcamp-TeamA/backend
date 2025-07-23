from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.core.services import ArtworkInfoOrchestrator
from apps.videos.services import VideoGenerator
from apps.videos.services.visionstory_service import VisionStoryService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)


class VideoCreationView(APIView):
    """
    작품 기반 영상 생성 API
    
    OCR 텍스트를 입력받아 자동으로 영상을 생성하는 기능
    """
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator = ArtworkInfoOrchestrator()
        self.video_generator = VideoGenerator()
    
    @swagger_auto_schema(
        operation_description="OCR 텍스트를 기반으로 작품 정보를 추출하고 영상을 자동 생성합니다",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['ocrText'],
            properties={
                'ocrText': openapi.Schema(type=openapi.TYPE_STRING, description='OCR로 추출된 텍스트', example='모나리자\n레오나르도 다 빈치\n1503-1519년'),
                'museumName': openapi.Schema(type=openapi.TYPE_STRING, description='박물관/미술관 이름', example='루브르 박물관'),
                'avatarId': openapi.Schema(type=openapi.TYPE_STRING, description='사용할 아바타 ID (선택적, 미제공 시 최신 아바타 자동 사용)', example='4321918387609092991'),
                'voiceId': openapi.Schema(type=openapi.TYPE_STRING, description='사용할 음성 ID', example='Alice'),
                'aspectRatio': openapi.Schema(type=openapi.TYPE_STRING, description='비디오 비율', example='9:16'),
                'resolution': openapi.Schema(type=openapi.TYPE_STRING, description='해상도', example='480p'),
                'emotion': openapi.Schema(type=openapi.TYPE_STRING, description='감정 설정', example='cheerful'),
                'backgroundColor': openapi.Schema(type=openapi.TYPE_STRING, description='배경색', example=''),
            }
        ),
        responses={
            201: openapi.Response(
                description="영상 생성 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'visionstoryUrl': openapi.Schema(type=openapi.TYPE_STRING, description='VisionStory 영상 URL', example='https://visionstory.ai/videos/video_001.mp4'),
                        'thumbnailUrl': openapi.Schema(type=openapi.TYPE_STRING, description='썸네일 URL', example='https://example.com/thumbnails/video_001.jpg'),
                        'duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='영상 길이(초)', example=180),
                        'artworkInfo': openapi.Schema(type=openapi.TYPE_OBJECT, description='추출된 작품 정보 (title, artist, description, videoScript 포함)'),
                    }
                )
            ),
            400: openapi.Response(description="잘못된 요청"),
            500: openapi.Response(description="서버 오류")
        }
    )
    async def post(self, request):
        """작품 기반 영상 생성"""
        try:
            # 1단계: 요청 데이터 검증
            ocr_text = request.data.get('ocrText')
            museum_name = request.data.get('museumName')
            avatar_id = request.data.get('avatarId')
            voice_id = request.data.get('voiceId', 'Alice')
            aspect_ratio = request.data.get('aspectRatio', '9:16')
            resolution = request.data.get('resolution', '480p')
            emotion = request.data.get('emotion', 'cheerful')
            background_color = request.data.get('backgroundColor', '')
            
            if not ocr_text:
                return Response(
                    {'error': 'ocrText는 필수입니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # avatarId가 없으면 최신 아바타 ID 자동 조회
            if not avatar_id:
                logger.info("avatarId가 제공되지 않음. 최신 아바타 ID 조회 시작")
                visionstory_service = VisionStoryService()
                avatar_id = visionstory_service.get_latest_avatar_id()
                
                if not avatar_id:
                    return Response(
                        {'error': '사용 가능한 아바타가 없습니다. 먼저 아바타를 생성해주세요.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                logger.info(f"최신 아바타 ID 자동 설정: {avatar_id}")
            
            # 2단계: 작품 정보 추출 및 스크립트 생성
            logger.info("작품 정보 추출 시작")
            artwork_info = await self.orchestrator.extract_and_enrich(
                ocr_text=ocr_text,
                museum_name=museum_name
            )
            
            # 3단계: VisionStory 영상 생성
            logger.info("VisionStory 영상 생성 시작")
            video_info = self.video_generator.generate_video(
                artwork_info=artwork_info,
                avatar_id=avatar_id,
                voice_id=voice_id,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                emotion=emotion,
                background_color=background_color
            )
            
            # 4단계: 응답 데이터 구성
            response_data = {
                'visionstoryUrl': video_info.video_url,
                'thumbnailUrl': video_info.thumbnail_url,
                'duration': video_info.duration,
                'artworkInfo': {
                    'title': artwork_info.basic_info.title,
                    'artist': artwork_info.basic_info.artist,
                    'description': artwork_info.web_search.description,
                    'videoScript': artwork_info.video_script.script_content
                }
            }
            
            logger.info("영상 생성 완료")
            return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"영상 생성 중 오류: {str(e)}")
            return Response(
                {'error': f'영상 생성 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 