from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100, default="unknown")
    placeId = models.CharField(max_length=100, default="unknown")
    thumbnailUrl = models.URLField(default="")
    videoUrl = models.URLField(default="")
    duration = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title