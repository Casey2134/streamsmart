from django.urls import path
from . import api

urlpatterns = [
    path('summarize/', api.JobCreate.as_view(), name='create_job' ),
    path('jobs/<int:pk>', api.JobRetrieve.as_view(), name='get_job'),
]