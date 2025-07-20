from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user.id', read_only=True)
    placeId = serializers.CharField(source='place_id')
    thumbnailUrl = serializers.URLField(source='thumbnail_url')
    videoUrl = serializers.URLField(source='video_url')
    createdAt = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Video
        fields = [
            'id', 'userId', 'placeId', 'title', 'thumbnailUrl',
            'videoUrl', 'createdAt', 'duration'
        ]