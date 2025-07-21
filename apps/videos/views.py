from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Video
from .serializers import VideoSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

class UserVideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        videos = Video.objects.filter(user=user)
        serializer = VideoSerializer(videos, many=True)
        return Response({
            "videos": serializer.data,
            "total": videos.count(),
            "message": "영상 목록을 성공적으로 조회했습니다."
        })

    def post(self, request):
        serializer = VideoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, video_id):
        user = request.user
        try:
            video = Video.objects.get(id=video_id, user=user)
        except Video.DoesNotExist:
            return Response(
                {"message": "해당 영상이 없거나 권한이 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        video.delete()
        return Response(
            {"id": video_id, "message": "영상이 성공적으로 삭제되었습니다"},
            status=status.HTTP_200_OK
        )