from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .services.ocr_service import detect_text

class OCRView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        operation_description="이미지에서 텍스트 추출 (Google Cloud Vision API)",
        manual_parameters=[
            openapi.Parameter(
                'image', 
                openapi.IN_FORM, 
                type=openapi.TYPE_FILE, 
                required=True,
                description='업로드할 이미지 파일 (JPG, PNG 등)'
            )
        ],
        responses={
            200: openapi.Response(
                description="텍스트 추출 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'ocr_text': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='추출된 전체 텍스트'
                        )
                    }
                )
            ),
            400: openapi.Response(description="이미지 파일이 업로드되지 않음"),
            500: openapi.Response(description="서버 오류 또는 Vision API 오류")
        }
    )
    def post(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'No image uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 임시 파일로 저장
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp:
            for chunk in image.chunks():
                temp.write(chunk)
            temp_path = temp.name

        try:
            result = detect_text(temp_path)
            # description만 모아서 하나의 문자열로 합치기
            ocr_text = " ".join([item['description'] for item in result if 'description' in item])
            return Response({'ocr_text': ocr_text}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)