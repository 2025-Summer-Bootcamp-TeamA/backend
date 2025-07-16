from rest_framework import serializers
from .models import Video

class VideoSerializer(serializers.ModelSerializer):
    """영상 자동 저장용 간소화된 시리얼라이저"""
    videoId = serializers.IntegerField(source='id', read_only=True)
    videoUrl = serializers.URLField(source='video_url')  # 영상 URL (필수)
    thumbnailUrl = serializers.URLField(source='thumbnail_url', required=False)  # 썸네일 URL (선택)

    class Meta:
        model = Video
        fields = ['videoId', 'title', 'videoUrl', 'thumbnailUrl', 'created_at']
        extra_kwargs = {
            'title': {'required': True},
            'videoUrl': {'required': True},
        }