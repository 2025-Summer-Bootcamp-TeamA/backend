from rest_framework import serializers
from ..models import Video

class VideoSerializer(serializers.ModelSerializer):
    """영상 자동 저장용 시리얼라이저"""
    visionstoryId = serializers.IntegerField(source='id', read_only=True)
    placeId = serializers.CharField(source='place_id')
    videoUrl = serializers.URLField(source='video_url')
    thumbnailUrl = serializers.URLField(source='thumbnail_url', required=False)

    class Meta:
        model = Video
        fields = ['visionstoryId', 'title', 'artist', 'placeId', 'thumbnailUrl', 'videoUrl']
        extra_kwargs = {
            'title': {'required': True},
            'artist': {'required': True},
            'placeId': {'required': True},
            'videoUrl': {'required': True},
            'thumbnailUrl': {'required': False},
        } 