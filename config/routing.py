from django.urls import path, include

websocket_urlpatterns = [
    path("ws/", include("game.routing")),
]
