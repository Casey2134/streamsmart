from rest_framework import generics, status
from rest_framework.response import Response
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

    def create(self, request, *args, **kwargs):
        url = request.data.get('url')
        if url:
            existing_job = Job.objects.filter(url=url).last()
            if existing_job:
                serializer = self.get_serializer(existing_job)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        transaction.on_commit(lambda: process_video.delay(instance.id))
        