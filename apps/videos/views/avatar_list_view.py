import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.videos.services.visionstory_service import VisionStoryService

logger = logging.getLogger(__name__)


class AvatarListView(APIView):
    """아바타 목록 조회 API"""
    permission_classes = [AllowAny]
    
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