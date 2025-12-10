from django.urls import path
from .api import RoomCreateView, RoomDetailView

urlpatterns = [
    path("rooms/", RoomCreateView.as_view(), name="room-create"),
    path("rooms/<str:code>/", RoomDetailView.as_view(), name="room-detail"),
]
