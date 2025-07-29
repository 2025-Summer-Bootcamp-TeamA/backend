from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

class Video(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100, default="unknown")
    place_id = models.CharField(max_length=100, default="unknown")
    museum_name = models.CharField(max_length=200, default="unknown")  # 박물관명 추가
    thumbnail_url = models.URLField(blank=True, null=True, max_length=1000)
    video_url = models.URLField(blank=True, null=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'videos'

    def clean(self):
        pass  # 다른 검증 로직이 추가되면 여기에 구현

    def __str__(self):
        return self.title