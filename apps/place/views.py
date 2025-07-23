import logging

logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .serializers import NearbyMuseumRequestSerializer, NearbyMuseumResponseSerializer
from .services.maps_mcp import search_nearby_museums
import json
from asgiref.sync import async_to_sync


MAX_RESULTS = 4

class NearbyMuseumView(APIView):

    @swagger_auto_schema(
        request_body=NearbyMuseumRequestSerializer,
        responses={200: NearbyMuseumResponseSerializer(many=True)},
        operation_summary="근처 박물관 검색",
        operation_description="사용자의 위도, 경도, 반경을 기반으로 Google Maps MCP를 사용해 근처 박물관을 검색합니다."
    )
    def post(self, request, *args, **kwargs):
        serializer = NearbyMuseumRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        lat = serializer.validated_data["latitude"]
        lng = serializer.validated_data["longitude"]
        radius = serializer.validated_data.get("radius", 3000)
        keyword = serializer.validated_data.get("keyword", "museum")

        try:
            result = async_to_sync(search_nearby_museums)(lat, lng, radius, keyword)
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()
            elif hasattr(result, "data"):
                result_dict = result.data
            else:
                result_dict = dict(result)
            content_list = result_dict.get("content", [])
            if content_list and hasattr(content_list[0], "text"):
                places_json = json.loads(content_list[0].text)
                places = places_json.get("places", [])
                for idx, p in enumerate(places[:4]):
                    p.pop("rating", None)
                    p.pop("types", None)
                    if "web_url" not in p:
                        p["web_url"] = None
                    p["rank"] = idx + 1
                places = places[:4]
            else:
                places = []
            return Response(places, status=status.HTTP_200_OK)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            return Response(
                {"error": "응답 데이터 파싱 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Google Maps MCP 호출 중 예외 발생: {str(e)}", exc_info=True)
            return Response(
                {"error": "박물관 검색 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
