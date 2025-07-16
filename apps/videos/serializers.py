from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    videoId = serializers.IntegerField(source='id', read_only=True)  # id를 videoId로 응답

    class Meta:
        model = Video
        fields = ['videoId', 'title', 'artist', 'placeId', 'thumbnailUrl', 'videoUrl', 'duration']