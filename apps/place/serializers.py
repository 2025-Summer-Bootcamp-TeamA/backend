# place/serializers.py

from rest_framework import serializers


class NearbyMuseumRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField(
        min_value=-90, 
        max_value=90,
        help_text="위도 (-90 ~ 90)"
    )
    longitude = serializers.FloatField(
        min_value=-180, 
        max_value=180,
        help_text="경도 (-180 ~ 180)"
    )
    radius = serializers.IntegerField(
        required=False, 
        default=5000, 
        min_value=1,
        max_value=50000,
        help_text="검색 반경 (미터, 기본값: 5000)"
    )
    keyword = serializers.CharField(
        required=False, 
        default="museum", 
        min_length=1,
        max_length=100,
        help_text="검색 키워드 (기본값: museum)"
    )


class NearbyMuseumResponseSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="장소명")
    address = serializers.CharField(help_text="주소")
    place_id = serializers.CharField(help_text="Google Places ID")
    latitude = serializers.FloatField(help_text="위도")
    longitude = serializers.FloatField(help_text="경도")
    rank = serializers.IntegerField(help_text="검색 결과 순위")
    web_url = serializers.URLField(
        allow_null=True, 
        required=False,
        help_text="웹사이트 URL (없을 수 있음)"
    )
    distance_m = serializers.FloatField(help_text="사용자 위치로부터의 거리 (미터)")


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField(help_text="오류 메시지")
    details = serializers.DictField(
        required=False,
        help_text="오류 상세 정보"
    )


class ValidationErrorResponseSerializer(serializers.Serializer):
    """입력 데이터 검증 실패 시 응답"""
    latitude = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="위도 필드 오류"
    )
    longitude = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="경도 필드 오류"
    )
    radius = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="반경 필드 오류"
    )
    keyword = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="키워드 필드 오류"
    )
