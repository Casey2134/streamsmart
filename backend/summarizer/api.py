from rest_framework import generics
from .serializers import JobSerializer
from .models import Job
from .tasks import process_video
from django.db import transaction

class JobRetrieve(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    
class JobCreate(generics.CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        transaction.on_commit(lambda: process_video.delay(instance.id))
        