from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.authentication.permissions import DebugIsAuthenticated
from apps.authentication.authentication import CustomJWTAuthentication
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
        tags=["videos"],
        operation_summary="영상 저장",
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


# ✅ 영상 목록 조회
class VideoListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

    @swagger_auto_schema(
        tags=["videos"],
        operation_summary="영상 목록 조회",
        operation_description="JWT 토큰 기반으로 사용자의 영상 목록을 조회합니다.",
        security=[{'Bearer': []}],  # JWT 토큰 인증 필요
        responses={200: openapi.Response(
            description="영상 목록",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "videos": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                "placeId": openapi.Schema(type=openapi.TYPE_STRING, example="ChIJMwd0tBdzfDURdfxQfHwh4XQ"),
                                "title": openapi.Schema(type=openapi.TYPE_STRING, example="경복궁 근정전 VR 체험"),
                                "thumbnailUrl": openapi.Schema(type=openapi.TYPE_STRING, example="https://example.com/thumbnails/video_001.jpg"),
                                "createdAt": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", example="2025-07-08T14:30:00Z"),
                            }
                        )
                    )
                }
            )
        )}
    )
    def get(self, request):
        # 디버깅: 인증 상태 확인
        print("=== VideoListView Debug Info ===")
        print(f"User authenticated: {request.user.is_authenticated}")
        print(f"User: {request.user}")
        print(f"User ID: {getattr(request.user, 'id', 'No ID')}")
        print(f"Authorization header: {request.headers.get('Authorization')}")
        print(f"All headers: {dict(request.headers)}")
        print(f"Request method: {request.method}")
        print(f"Request path: {request.path}")
        print("=== End Debug Info ===")
        
        # 인증되지 않은 경우 명시적으로 확인
        if not request.user.is_authenticated:
            print("ERROR: User is not authenticated!")
            return Response({"error": "Authentication required"}, status=401)
        
        videos = Video.objects.filter(user=request.user).order_by('-created_at')
        results = [
            {
                "id": v.id,
                "placeId": v.place_id,
                "title": v.title,
                "thumbnailUrl": v.thumbnail_url,
                "createdAt": v.created_at,
            } for v in videos
        ]
        return Response({"videos": results})


# ✅ 영상 상세 조회
class VideoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["videos"],
        operation_summary="영상 상세 조회",
        operation_description="JWT 토큰 기반으로 본인 영상 상세정보를 조회합니다.",
        security=[{'Bearer': []}],  # JWT 토큰 인증 필요
        responses={200: openapi.Response(
            description="영상 상세 정보",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    "placeId": openapi.Schema(type=openapi.TYPE_STRING),
                    "title": openapi.Schema(type=openapi.TYPE_STRING),
                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="작품 설명", example="작품 설명"),
                    "thumbnailUrl": openapi.Schema(type=openapi.TYPE_STRING),
                    "videoUrl": openapi.Schema(type=openapi.TYPE_STRING),
                    "createdAt": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
                }
            )
        )}
    )
    def get(self, request, video_id):
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response({"error": "존재하지 않거나 권한이 없는 영상입니다."}, status=404)

        return Response({
            "id": video.id,
            "placeId": video.place_id,
            "title": video.title,
            "description": video.artist,  # artist를 작품 설명으로 사용하고 있다면 여기에
            "thumbnailUrl": video.thumbnail_url,
            "videoUrl": video.video_url,
            "createdAt": video.created_at,
        })


# ✅ 영상 삭제
class VideoDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["videos"],
        operation_summary="영상 삭제",
        operation_description="본인의 영상을 삭제합니다.",
        security=[{'Bearer': []}],  # JWT 토큰 인증 필요
        responses={
            200: openapi.Response(
                description="삭제 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="영상이 성공적으로 삭제되었습니다"),
                    }
                )
            ),
            404: "존재하지 않음 또는 권한 없음"
        }
    )
    def delete(self, request, video_id):
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response({"error": "존재하지 않거나 권한이 없는 영상입니다."}, status=404)

        video.delete()
        return Response({"id": video_id, "message": "영상이 성공적으로 삭제되었습니다"}) 