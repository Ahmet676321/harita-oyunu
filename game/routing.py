from django.urls import re_path
from .consumers import RoomConsumer

websocket_urlpatterns = [
    re_path(r"room/(?P<room_code>[A-Z0-9]{6})/$", RoomConsumer.as_asgi()),
]
