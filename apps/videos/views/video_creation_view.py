import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from apps.core.services import ArtworkInfoOrchestrator
from apps.videos.services import VideoGenerator
from apps.videos.services.visionstory_service import VisionStoryService
from apps.gcs.storage_service import upload_video_to_gcs
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
        tags=["videos"],
        operation_summary="작품 기반 영상 생성",
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
    def post(self, request):
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
            
            # 2단계: 작품 정보 추출 및 스크립트 생성 (비동기 호출을 동기적으로 처리)
            logger.info("작품 정보 추출 시작")
            artwork_info = asyncio.run(self.orchestrator.extract_and_enrich(
                ocr_text=ocr_text,
                museum_name=museum_name
            ))
            
            # 3단계: VisionStory 영상 생성 (완성될 때까지 대기)
            logger.info("VisionStory 영상 생성 시작")
            video_info = self.video_generator.generate_video(
                artwork_info=artwork_info,
                avatar_id=avatar_id,
                voice_id=voice_id,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                emotion=emotion,
                background_color=background_color,
                wait_for_completion=True  # 영상이 완성될 때까지 대기
            )
            
            # VisionStory URL을 GCS에 업로드 (영상이 완성된 경우에만)
            visionstory_video_url = video_info.video_url
            gcs_video_url = None
            
            if visionstory_video_url and video_info.status == "created":
                logger.info(f"VisionStory 영상을 GCS에 업로드 시작: {visionstory_video_url}")
                gcs_video_url = upload_video_to_gcs(visionstory_video_url, folder="videos")
                
                if gcs_video_url:
                    logger.info(f"GCS 업로드 성공: {gcs_video_url}")
                else:
                    logger.warning("GCS 업로드 실패, VisionStory URL 사용")
                    gcs_video_url = visionstory_video_url
            else:
                # 영상 생성 실패 또는 URL이 없는 경우
                logger.error(f"영상 생성 실패: status={video_info.status}, url={visionstory_video_url}")
                return Response({
                    'error': '영상 생성에 실패했습니다.',
                    'status': video_info.status,
                    'error_message': video_info.error_message
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 4단계: 응답 데이터 구성
            response_data = {
                'videoId': video_info.video_id,  # 영상 ID 추가
                'visionstoryUrl': gcs_video_url,  # GCS URL
                'thumbnailUrl': video_info.thumbnail_url,
                'status': video_info.status,  # 상태 정보 추가
                'artworkInfo': {
                    'title': artwork_info.basic_info.title if artwork_info.basic_info and artwork_info.basic_info.title else '',
                    'artist': artwork_info.basic_info.artist if artwork_info.basic_info and artwork_info.basic_info.artist else '',
                    'description': artwork_info.web_search.description if artwork_info.web_search and artwork_info.web_search.description else '',
                    'videoScript': artwork_info.video_script.script_content if artwork_info.video_script and artwork_info.video_script.script_content else ''
                }
            }
            
            logger.info(f"영상 생성 및 GCS 업로드 완료: video_id={video_info.video_id}")
            return Response(response_data, status=status.HTTP_201_CREATED)  # 201 Created로 변경
                
        except Exception as e:
            logger.error(f"영상 생성 중 오류: {str(e)}")
            return Response(
                {'error': f'영상 생성 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 