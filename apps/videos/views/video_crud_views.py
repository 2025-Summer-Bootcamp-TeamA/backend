from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..models import Video
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


# ✅ 영상 목록 조회
class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

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
            return Response({"message": "영상이 없습니다."}, status=404)

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
            return Response({"message": "영상이 없습니다."}, status=404)

        video.delete()
        return Response({"id": video_id, "message": "영상이 성공적으로 삭제되었습니다"})