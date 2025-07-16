from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Create your views here.
def index(request):
    return HttpResponse("설정이 완료되었습니다.")

class PostListView(APIView):
    """
    게시글 목록 조회 및 생성 API
    """
    
    @swagger_auto_schema(
        operation_description="게시글 목록을 조회합니다",
        responses={
            200: openapi.Response(
                description="성공",
                examples={
                    "application/json": {
                        "posts": [
                            {"id": 1, "title": "첫 번째 게시글", "content": "내용입니다."},
                            {"id": 2, "title": "두 번째 게시글", "content": "또 다른 내용입니다."}
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        """게시글 목록 조회"""
        sample_posts = [
            {"id": 1, "title": "첫 번째 게시글", "content": "내용입니다."},
            {"id": 2, "title": "두 번째 게시글", "content": "또 다른 내용입니다."}
        ]
        return Response({"posts": sample_posts}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="새 게시글을 생성합니다",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='게시글 제목'),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='게시글 내용'),
            },
            required=['title', 'content']
        ),
        responses={
            201: openapi.Response(description="게시글 생성 성공"),
            400: openapi.Response(description="잘못된 요청")
        }
    )
    def post(self, request):
        """새 게시글 생성"""
        title = request.data.get('title')
        content = request.data.get('content')
        
        if not title or not content:
            return Response(
                {"error": "제목과 내용은 필수입니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 실제로는 데이터베이스에 저장
        new_post = {
            "id": 3,
            "title": title,
            "content": content
        }
        
        return Response(new_post, status=status.HTTP_201_CREATED)