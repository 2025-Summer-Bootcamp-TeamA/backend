import asyncio
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os

from apps.core.services import ArtworkInfoOrchestrator
from apps.videos.services import VideoGenerator
from apps.videos.services.visionstory_service import VisionStoryService
from apps.gcs.storage_service import upload_video_to_gcs
from apps.videos.models import Video

logger = logging.getLogger(__name__)


class VideoCreationView(APIView):
    """
    작품 기반 영상 생성 API
    
    OCR 텍스트를 입력받아 자동으로 영상을 생성하는 기능
    """
    
    def get_permissions(self):
        """환경변수로 인증 제어"""
        # 개발/테스트 환경에서는 인증 비활성화
        if os.getenv('DISABLE_AUTH', 'false').lower() == 'true':
            return [AllowAny()]
        return [IsAuthenticated()]
    
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
                        'videoId': openapi.Schema(type=openapi.TYPE_INTEGER, description='DB에 저장된 영상 ID'),
                        'visionstoryId': openapi.Schema(type=openapi.TYPE_STRING, description='VisionStory 영상 ID'),
                        'videoUrl': openapi.Schema(type=openapi.TYPE_STRING, description='영상 URL (GCS)'),
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='영상 상태'),
                        'museumName': openapi.Schema(type=openapi.TYPE_STRING, description='박물관명'),
                        'placeId': openapi.Schema(type=openapi.TYPE_STRING, description='장소 ID'),
                        'artworkInfo': openapi.Schema(type=openapi.TYPE_OBJECT, description='추출된 작품 정보'),
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
            
            # 4단계: DB에 영상 정보 저장
            video = None
            try:
                # 작품 제목과 작가 정보 추출
                title = artwork_info.basic_info.title if artwork_info.basic_info and artwork_info.basic_info.title else 'Unknown Artwork'
                artist = artwork_info.basic_info.artist if artwork_info.basic_info and artwork_info.basic_info.artist else 'Unknown Artist'
                
                # Video 모델에 저장 (인증된 사용자만 user 필드 설정)
                video = Video.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    title=title,
                    artist=artist,
                    place_id='unknown',  # 기본값으로 설정
                    museum_name=museum_name,  # 박물관명 저장
                    video_url=gcs_video_url,
                    thumbnail_url=video_info.thumbnail_url if video_info.thumbnail_url else None
                )
                
                logger.info(f"DB에 영상 정보 저장 완료: video_id={video.id}")
                
            except Exception as db_error:
                logger.error(f"DB 저장 중 오류: {str(db_error)}")
                # DB 저장 실패해도 영상 생성은 성공했으므로 경고만 남기고 계속 진행
                # video 변수는 None으로 유지
            
            # 5단계: 응답 데이터 구성
            response_data = {
                'videoId': video.id if video else None,  # DB에 저장된 영상 ID
                'visionstoryId': video_info.video_id,  # VisionStory 영상 ID
                'videoUrl': gcs_video_url,  # GCS URL
                'status': video_info.status,  # 상태 정보
                'museumName': museum_name,  # 박물관명
                'placeId': 'unknown',  # 기본값으로 설정
                'artworkInfo': {
                    'title': title,
                    'artist': artist,
                    'description': artwork_info.web_search.description if artwork_info.web_search and artwork_info.web_search.description else '',
                    'videoScript': artwork_info.video_script.script_content if artwork_info.video_script and artwork_info.video_script.script_content else ''
                }
            }
            
            logger.info(f"영상 생성, GCS 업로드, DB 저장 완료: video_id={video.id if video else 'N/A (DB 저장 실패)'}")
            return Response(response_data, status=status.HTTP_201_CREATED)  # 201 Created
                
        except Exception as e:
            logger.error(f"영상 생성 중 오류: {str(e)}")
            return Response(
                {'error': f'영상 생성 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 