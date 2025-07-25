import logging
from typing import Dict, Any

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from asgiref.sync import async_to_sync

from .serializers import (
    NearbyMuseumRequestSerializer, 
    NearbyMuseumResponseSerializer,
    ErrorResponseSerializer,
    ValidationErrorResponseSerializer
)
from .services.maps_mcp import (
    search_nearby_museums, 
    process_mcp_response,
    MapsServiceError,
    MapsConfigError,
    MapsAPIError
)

logger = logging.getLogger(__name__)

# 상수 정의
MAX_RESULTS = 4
DEFAULT_RADIUS = 3000
DEFAULT_KEYWORD = "museum"


class NearbyMuseumView(APIView):
    """근처 박물관 검색 API"""

    @swagger_auto_schema(
        request_body=NearbyMuseumRequestSerializer,
        responses={
            200: NearbyMuseumResponseSerializer(many=True),
            400: ValidationErrorResponseSerializer,
            500: ErrorResponseSerializer
        },
        operation_summary="근처 박물관 검색",
        operation_description="""
        사용자의 위도, 경도, 반경을 기반으로 Google Maps MCP를 사용해 근처 박물관을 검색합니다.
        
        **주요 기능:**
        - 위치 기반 박물관 검색
        - 검색 반경 및 키워드 지정 가능
        - 최대 4개의 결과 반환
        - 검색 결과에 순위 부여
        
        **제한사항:**
        - 반경: 1m ~ 50,000m
        - 위도: -90 ~ 90
        - 경도: -180 ~ 180
        """,
        tags=['Places']
    )
    def post(self, request, *args, **kwargs):
        """근처 박물관을 검색합니다."""
        # 1. 입력 데이터 검증
        serializer = NearbyMuseumRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"입력 데이터 검증 실패: {serializer.errors}")
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. 검증된 데이터 추출
        validated_data = serializer.validated_data
        lat = validated_data["latitude"]
        lng = validated_data["longitude"]
        radius = validated_data.get("radius", DEFAULT_RADIUS)
        keyword = validated_data.get("keyword", DEFAULT_KEYWORD)

        logger.info(
            f"박물관 검색 요청: lat={lat}, lng={lng}, "
            f"radius={radius}, keyword={keyword}"
        )

        try:
            # 3. MCP 서비스 호출
            result = async_to_sync(search_nearby_museums)(lat, lng, radius, keyword)
            
            # 4. 응답 처리
            places = process_mcp_response(result, MAX_RESULTS)
            
            # 5. 응답 데이터 검증
            response_serializer = NearbyMuseumResponseSerializer(data=places, many=True)
            if not response_serializer.is_valid():
                logger.error(f"응답 데이터 검증 실패: {response_serializer.errors}")
                return self._create_error_response(
                    "응답 데이터 검증에 실패했습니다.",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    {"validation_errors": response_serializer.errors}
                )
            
            logger.info(f"박물관 검색 완료: {len(places)}개 결과 반환")
            return Response(places, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # 입력 매개변수 검증 오류
            logger.warning(f"매개변수 검증 오류: {str(e)}")
            return self._create_error_response(
                str(e),
                status.HTTP_400_BAD_REQUEST
            )
            
        except MapsConfigError as e:
            # 설정 오류 - 서버 내부 문제
            logger.error(f"Maps 설정 오류: {str(e)}")
            return self._create_error_response(
                "서비스 설정에 문제가 있습니다. 관리자에게 문의하세요.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"config_error": str(e)}
            )
            
        except MapsAPIError as e:
            # API 호출 오류
            logger.error(f"Maps API 오류: {str(e)}")
            return self._create_error_response(
                "박물관 검색 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"api_error": str(e)}
            )
            
        except MapsServiceError as e:
            # 기타 Maps 서비스 오류
            logger.error(f"Maps 서비스 오류: {str(e)}")
            return self._create_error_response(
                "박물관 검색 중 오류가 발생했습니다.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"service_error": str(e)}
            )
            
        except Exception as e:
            # 예상치 못한 오류
            logger.error(f"예상치 못한 오류 발생: {str(e)}", exc_info=True)
            return self._create_error_response(
                "시스템 오류가 발생했습니다. 관리자에게 문의하세요.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"unexpected_error": str(e)}
            )

    def _create_error_response(
        self, 
        error_message: str, 
        status_code: int, 
        details: Dict[str, Any] = None
    ) -> Response:
        """통일된 에러 응답을 생성합니다."""
        error_data = {"error": error_message}
        if details:
            error_data["details"] = details
            
        return Response(error_data, status=status_code)
