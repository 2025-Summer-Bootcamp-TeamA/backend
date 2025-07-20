from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Video
from .serializers import VideoSerializer

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