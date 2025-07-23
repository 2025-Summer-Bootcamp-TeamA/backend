# place/serializers.py

from rest_framework import serializers



class NearbyMuseumRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    radius = serializers.IntegerField(required=False, default=3000, min_value=1)
    keyword = serializers.CharField(required=False, default="museum", min_length=1)


class NearbyMuseumResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.CharField()
    place_id = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
