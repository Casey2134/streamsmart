from django.db import models
import uuid


class Room(models.Model):
    code = models.CharField(max_length=8, unique=True, db_index=True)
    video_url = models.URLField()

    # Store the host's session identifier (generated on frontend, stored in localStorage)
    host_session_id = models.CharField(max_length=64)

    # Playback state for synchronization
    current_time = models.FloatField(default=0.0)
    is_playing = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Room {self.code}"
