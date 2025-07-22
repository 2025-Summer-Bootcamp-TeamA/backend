from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .serializers import NearbyMuseumRequestSerializer, NearbyMuseumResponseSerializer
from .services.maps_mcp import search_nearby_museums

class NearbyMuseumView(APIView):

    @swagger_auto_schema(
        request_body=NearbyMuseumRequestSerializer,
        responses={200: NearbyMuseumResponseSerializer(many=True)},
        operation_summary="근처 박물관 검색",
        operation_description="사용자의 위도, 경도, 반경을 기반으로 Google Maps MCP를 사용해 근처 박물관을 검색합니다."
    )
    def post(self, request, *args, **kwargs):
        # request.data -> dict 변환
        serializer = NearbyMuseumRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        lat = serializer.validated_data["latitude"]
        lng = serializer.validated_data["longitude"]
        radius = serializer.validated_data.get("radius", 3000)
        keyword = serializer.validated_data.get("keyword", "museum")

        # 🔽 여기가 핵심: 비동기 함수를 동기에서 호출할 수 있도록 `async_to_sync` 사용
        from asgiref.sync import async_to_sync
        try:
            museums = async_to_sync(search_nearby_museums)(lat, lng, radius, keyword)
            return Response(museums, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Google Maps MCP 호출 중 오류 발생: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
