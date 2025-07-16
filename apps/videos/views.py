from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Video
from .serializers import VideoSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class VideoUploadView(APIView):
    """
    영상 자동 저장 API
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="영상을 자동으로 저장합니다",
        request_body=VideoSerializer,
        responses={
            201: openapi.Response(description="영상 저장 성공", schema=VideoSerializer),
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