from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ..models import Video
from ..serializers import VideoSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class VideoUploadView(APIView):
    """
    영상 저장 API
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="영상을 자동으로 저장합니다",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'artist', 'placeId', 'videoUrl', 'duration'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='영상 제목', example='모나리자'),
                'artist': openapi.Schema(type=openapi.TYPE_STRING, description='아티스트명', example='레오나르도 다빈치'),
                'placeId': openapi.Schema(type=openapi.TYPE_STRING, description='장소 ID', example='ChIJMwd0tBdzfDURdfxQfHwh4XQ'),
                'thumbnailUrl': openapi.Schema(type=openapi.TYPE_STRING, description='썸네일 URL', example='https://example.com/thumbnails/video_001.jpg'),
                'videoUrl': openapi.Schema(type=openapi.TYPE_STRING, description='영상 URL', example='https://example.com/videos/video_001.mp4'),
                'duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='영상 길이(초)', example=180),
            }
        ),
        responses={
            201: openapi.Response(
                description="영상 저장 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'videoId': openapi.Schema(type=openapi.TYPE_INTEGER, description='영상 ID', example=1),
                        'title': openapi.Schema(type=openapi.TYPE_STRING, description='영상 제목', example='모나리자'),
                        'artist': openapi.Schema(type=openapi.TYPE_STRING, description='아티스트명', example='레오나르도 다빈치'),
                        'placeId': openapi.Schema(type=openapi.TYPE_STRING, description='장소 ID', example='ChIJMwd0tBdzfDURdfxQfHwh4XQ'),
                        'thumbnailUrl': openapi.Schema(type=openapi.TYPE_STRING, description='썸네일 URL', example='https://example.com/thumbnails/video_001.jpg'),
                        'videoUrl': openapi.Schema(type=openapi.TYPE_STRING, description='영상 URL', example='https://example.com/videos/video_001.mp4'),
                        'duration': openapi.Schema(type=openapi.TYPE_INTEGER, description='영상 길이(초)', example=180),
                    }
                )
            ),
            400: openapi.Response(description="잘못된 요청")
        }
    )
    def post(self, request):
        """영상 자동 저장"""
        serializer = VideoSerializer(data=request.data)
        if serializer.is_valid():
            video = serializer.save()
            return Response(
                VideoSerializer(video).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


# TODO: 추후 추가할 CRUD 기능들
#
# class VideoListView(APIView):
#     """영상 목록 조회 API"""
#     pass
#
# class VideoDetailView(APIView):
#     """영상 상세 조회 API"""
#     pass
#
# class VideoUpdateView(APIView):
#     """영상 수정 API"""
#     pass
#
# class VideoDeleteView(APIView):
#     """영상 삭제 API"""
#     pass 