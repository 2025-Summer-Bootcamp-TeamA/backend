from django.db import models
from django.core.exceptions import ValidationError

class Video(models.Model):
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100, default="unknown")
    place_id = models.CharField(max_length=100, default="unknown")
    thumbnail_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    duration = models.PositiveIntegerField(default=0)  # 음수 불가
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'videos'

    def clean(self):
        if self.duration < 0:
            raise ValidationError({'duration': 'Duration must be non-negative.'})

    def __str__(self):
        return self.title