import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.videos.services.visionstory_service import VisionStoryService

logger = logging.getLogger(__name__)


class VisionStoryLatestVideoView(APIView):
    """VisionStory에서 생성된 가장 최근 영상 URL을 조회하는 API"""
    
    @swagger_auto_schema(
        tags=["videos"],
        operation_summary="최근 영상 조회",
        operation_description="VisionStory에서 생성된 가장 최근 영상의 URL과 정보를 조회합니다",
        responses={
            200: openapi.Response(
                description="최근 영상 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'video_id': openapi.Schema(type=openapi.TYPE_STRING, description='영상 ID'),
                                'video_url': openapi.Schema(type=openapi.TYPE_STRING, description='영상 URL'),
                                'status': openapi.Schema(type=openapi.TYPE_STRING, description='영상 상태'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='생성 시간'),
                                'duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='영상 길이(초)'),
                            }
                        ),
                    }
                )
            ),
            404: openapi.Response(description="생성된 영상이 없음"),
            500: openapi.Response(description="서버 오류")
        }
    )
    def get(self, request):
        """
        VisionStory에서 생성된 가장 최근 영상의 URL을 반환합니다.
        
        Returns:
            JSON Response:
                - success=True: 최근 영상 정보 포함
                - success=False: 에러 메시지 포함
        """
        try:
            logger.info("VisionStory 최근 영상 URL 조회 요청")
            
            # VisionStory 서비스 초기화
            visionstory_service = VisionStoryService()
            
            # 최근 영상 목록 조회
            videos_result = visionstory_service.get_recent_videos()
            
            if not videos_result or "data" not in videos_result:
                logger.error("VisionStory 영상 목록 조회 실패")
                return Response({
                    "success": False,
                    "error": "영상 목록을 가져올 수 없습니다."
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # 영상 목록에서 가장 최근 영상 찾기
            videos = videos_result["data"].get("videos", [])
            
            if not videos:
                logger.warning("생성된 영상이 없습니다")
                return Response({
                    "success": False,
                    "error": "생성된 영상이 없습니다."
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 가장 최근 영상 (첫 번째 영상이 최신이라고 가정)
            latest_video = videos[0]
            
            video_url = latest_video.get("video_url", "")
            if not video_url:
                logger.warning(f"최근 영상의 URL이 없습니다. 영상 ID: {latest_video.get('video_id', 'unknown')}")
                return Response({
                    "success": False,
                    "error": "영상 URL이 아직 생성되지 않았습니다."
                }, status=status.HTTP_202_ACCEPTED)
            
            # 성공 응답
            response_data = {
                "success": True,
                "data": {
                    "video_id": latest_video.get("video_id", ""),
                    "video_url": video_url,
                    "status": latest_video.get("status", "unknown"),
                    "created_at": latest_video.get("created_at", ""),
                    "duration": latest_video.get("duration", 0)
                }
            }
            
            logger.info(f"VisionStory 최근 영상 URL 조회 성공: {video_url}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"VisionStory 최근 영상 URL 조회 중 오류: {str(e)}")
            return Response({
                "success": False,
                "error": "서버 내부 오류가 발생했습니다."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VisionStoryVideoStatusView(APIView):
    """특정 영상의 생성 상태를 조회하는 API"""
    
    @swagger_auto_schema(
        tags=["videos"],
        operation_summary="영상 상태 조회",
        operation_description="특정 video_id로 영상의 생성 상태를 조회합니다",
        manual_parameters=[
            openapi.Parameter(
                'video_id',
                openapi.IN_QUERY,
                description="조회할 영상 ID",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="영상 상태 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'video_id': openapi.Schema(type=openapi.TYPE_STRING, description='영상 ID'),
                                'video_url': openapi.Schema(type=openapi.TYPE_STRING, description='영상 URL'),
                                'status': openapi.Schema(type=openapi.TYPE_STRING, description='영상 상태'),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING, description='생성 시간'),
                                # 'duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='영상 길이(초)'),
                                # 'thumbnail_url': openapi.Schema(type=openapi.TYPE_STRING, description='썸네일 URL'),
                            }
                        ),
                    }
                )
            ),
            400: openapi.Response(description="video_id 파라미터 누락"),
            404: openapi.Response(description="영상을 찾을 수 없음"),
            500: openapi.Response(description="서버 오류")
        }
    )
    def get(self, request):
        """
        특정 영상의 생성 상태를 조회합니다.
        
        Returns:
            JSON Response:
                - success=True: 영상 상태 정보 포함
                - success=False: 에러 메시지 포함
        """
        try:
            video_id = request.query_params.get('video_id')
            
            if not video_id:
                return Response({
                    "success": False,
                    "error": "video_id 파라미터가 필요합니다."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"VisionStory 영상 상태 조회 요청: video_id={video_id}")
            
            # VisionStory 서비스 초기화
            visionstory_service = VisionStoryService()
            
            # 영상 상태 조회
            status_info = visionstory_service.get_video_status(video_id)
            
            if not status_info:
                logger.error(f"영상 상태 조회 실패: video_id={video_id}")
                return Response({
                    "success": False,
                    "error": "영상을 찾을 수 없습니다."
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 성공 응답 (썸네일 URL 제외)
            response_data = {
                "success": True,
                "data": {
                    "video_id": status_info.get("video_id", video_id),
                    "video_url": status_info.get("video_url", ""),
                    "status": status_info.get("status", "unknown"),
                    "created_at": status_info.get("created_at", "")
                }
            }
            
            logger.info(f"VisionStory 영상 상태 조회 성공: video_id={video_id}, status={status_info.get('status')}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"VisionStory 영상 상태 조회 중 오류: {str(e)}")
            return Response({
                "success": False,
                "error": "서버 내부 오류가 발생했습니다."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 