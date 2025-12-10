import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room


class WatchPartyConsumer(AsyncWebsocketConsumer):
    # Track pending room deletions (for grace period when host refreshes)
    pending_deletions = {}

    async def connect(self):
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.room_group_name = f"watch_{self.room_code}"
        self.session_id = None
        self.username = "Anonymous"
        self.is_host = False

        # Verify room exists
        self.room = await self.get_room()
        if not self.room:
            await self.close()
            return

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send current playback state to the new joiner
        await self.send(
            text_data=json.dumps(
                {
                    "type": "sync",
                    "current_time": self.room.current_time,
                    "is_playing": self.room.is_playing,
                }
            )
        )

    async def disconnect(self, close_code):
        if self.is_host:
            # Host is leaving - start grace period before deleting room
            task = asyncio.create_task(self.delayed_room_deletion())
            WatchPartyConsumer.pending_deletions[self.room_code] = task
        else:
            # Regular viewer leaving - notify others
            if self.username:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_left",
                        "username": self.username,
                    },
                )

        # Leave the group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def delayed_room_deletion(self):
        """Wait before deleting room, in case host reconnects."""
        await asyncio.sleep(10)  # 10 second grace period

        # Check if still pending (host didn't reconnect)
        if self.room_code in WatchPartyConsumer.pending_deletions:
            del WatchPartyConsumer.pending_deletions[self.room_code]

            # Delete the room
            await self.delete_room()

            # Notify all viewers the party is over
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "room_closed",
                    "message": "The host has ended the watch party.",
                },
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "ping":
            # Respond immediately for latency measurement
            await self.send(text_data=json.dumps({"type": "pong"}))
        elif message_type == "join":
            await self.handle_join(data)
        elif message_type == "sync":
            await self.handle_sync(data)
        elif message_type == "chat":
            await self.handle_chat(data)

    async def handle_join(self, data):
        """Handle user joining with their session_id and username."""
        self.session_id = data.get("session_id")
        self.username = data.get("username", "Anonymous")

        # Refresh room data
        self.room = await self.get_room()
        if not self.room:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Room no longer exists"}
                )
            )
            await self.close()
            return

        # Check if this user is the host
        self.is_host = self.session_id == self.room.host_session_id

        # If host is reconnecting, cancel pending deletion
        if self.is_host and self.room_code in WatchPartyConsumer.pending_deletions:
            WatchPartyConsumer.pending_deletions[self.room_code].cancel()
            del WatchPartyConsumer.pending_deletions[self.room_code]

        # Send back their role and current state
        await self.send(
            text_data=json.dumps(
                {
                    "type": "role",
                    "is_host": self.is_host,
                    "video_url": self.room.video_url,
                }
            )
        )

        # Notify others that someone joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "username": self.username,
            },
        )

    async def handle_sync(self, data):
        """Handle playback sync - only host can control."""
        if not self.is_host:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Only the host can control playback"}
                )
            )
            return

        current_time = data.get("current_time", 0)
        is_playing = data.get("is_playing", False)

        # Save to database (for new joiners)
        await self.update_room_playback(current_time, is_playing)

        # Broadcast sync to everyone in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "sync_playback",
                "current_time": current_time,
                "is_playing": is_playing,
            },
        )

    async def handle_chat(self, data):
        """Handle chat messages - anyone can send."""
        message = data.get("message", "").strip()
        if not message:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": self.username,
            },
        )

    # ===== Group message handlers =====

    async def sync_playback(self, event):
        """Send sync update to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "sync",
                    "current_time": event["current_time"],
                    "is_playing": event["is_playing"],
                }
            )
        )

    async def chat_message(self, event):
        """Send chat message to client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat",
                    "message": event["message"],
                    "username": event["username"],
                }
            )
        )

    async def user_joined(self, event):
        """Notify client that a user joined."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "username": event["username"],
                }
            )
        )

    async def user_left(self, event):
        """Notify client that a user left."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "username": event["username"],
                }
            )
        )

    async def room_closed(self, event):
        """Notify client that the room was closed by host."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "room_closed",
                    "message": event["message"],
                }
            )
        )
        await self.close()

    # ===== Database operations =====

    @database_sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(code=self.room_code)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def update_room_playback(self, current_time, is_playing):
        Room.objects.filter(code=self.room_code).update(
            current_time=current_time, is_playing=is_playing
        )

    @database_sync_to_async
    def delete_room(self):
        Room.objects.filter(code=self.room_code).delete()
