from django.db import models
from django.contrib.postgres.fields import ArrayField


# Create your models here.
class Chapter(models.Model):
    name = models.TextField()
    start = models.IntegerField()
    end = models.IntegerField()


class Highlight(models.Model):
    name = models.TextField()
    start = models.IntegerField()
    end = models.IntegerField()
    description = models.TextField()


class Job(models.Model):
    class Status(models.TextChoices):
        downloading = "DOWNLOADING"
        transcribing = "TRANSCRIBING"
        analyzing = "ANALYZING"
        completed = "COMPLETED"

    url = models.TextField(blank=False)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.downloading
    )
    title = models.TextField(null=True, blank=True)
    duration = models.IntegerField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    audio_path = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
