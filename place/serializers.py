# place/serializers.py

from rest_framework import serializers

class NearbyMuseumRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    radius = serializers.IntegerField(required=False, default=3000)
    keyword = serializers.CharField(required=False, default="museum")

class NearbyMuseumResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.CharField()
    place_id = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
