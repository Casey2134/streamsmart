from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "code", "video_url", "current_time", "is_playing", "created_at"]
        read_only_fields = ["id", "code", "current_time", "is_playing", "created_at"]


class CreateRoomSerializer(serializers.Serializer):
    video_url = serializers.URLField()
    host_session_id = serializers.CharField(max_length=64)


class RoomCreateView(APIView):
    """Create a new watch party room."""

    def post(self, request):
        serializer = CreateRoomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = Room.objects.create(
            video_url=serializer.validated_data["video_url"],
            host_session_id=serializer.validated_data["host_session_id"],
        )

        return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)


class RoomDetailView(APIView):
    """Get room details by code."""

    def get(self, request, code):
        try:
            room = Room.objects.get(code=code)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(RoomSerializer(room).data)
