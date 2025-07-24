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
        tags=["places"],
        operation_summary="근처 박물관 검색",
        operation_description="사용자의 위도, 경도, 반경을 기반으로 Google Maps MCP를 사용해 근처 박물관을 검색합니다.",
        request_body=NearbyMuseumRequestSerializer,
        responses={200: NearbyMuseumResponseSerializer(many=True)}
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
            places = self._process_mcp_response(result)
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

    def _process_mcp_response(self, result):
        """MCP 응답을 처리하여 박물관 목록을 반환합니다."""
        try:
            # 결과를 딕셔너리로 변환
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()
            elif hasattr(result, "data"):
                result_dict = result.data
            else:
                result_dict = dict(result)
            # content 추출 및 검증
            content_list = result_dict.get("content", [])
            if not content_list or not hasattr(content_list[0], "text"):
                return []
            # JSON 파싱
            places_json = json.loads(content_list[0].text)
            places = places_json.get("places", [])
            # 데이터 정리 및 순위 부여
            processed_places = []
            for idx, place in enumerate(places[:MAX_RESULTS]):
                # 불필요한 필드 제거
                place.pop("rating", None)
                place.pop("types", None)
                # web_url 필드 보장
                if "web_url" not in place:
                    place["web_url"] = None
                # 순위 부여
                place["rank"] = idx + 1
                processed_places.append(place)
            return processed_places
        except (KeyError, IndexError, AttributeError) as e:
            logger.error(f"MCP 응답 처리 중 오류: {str(e)}")
            return []
