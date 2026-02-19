from django.urls import path
from . import views

app_name = "game"

urlpatterns = [
    # Singleplayer mevcut
    path("", views.game_view, name="home"),
    path("api/score/", views.save_score, name="save_score"),

    # Multiplayer yeni
    path("lobby/", views.lobby, name="lobby"),
    path("room/<str:code>/", views.room, name="room"),
]
