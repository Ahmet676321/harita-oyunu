import json
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import Score


def game_view(request: HttpRequest):
    top_scores = Score.objects.all()[:10]
    return render(request, "game/game.html", {"top_scores": top_scores})


@require_POST
@csrf_protect
def save_score(request: HttpRequest):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    name = (payload.get("name") or "").strip()
    score = payload.get("score")

    if not name:
        return HttpResponseBadRequest("Name is required")

    # Name length clamp
    if len(name) > 32:
        name = name[:32]

    try:
        score_int = int(score)
    except Exception:
        return HttpResponseBadRequest("Score must be an integer")

    if score_int < 0:
        score_int = 0

    # 1 dakikalık oyunda aşırı uçuk değerleri basitçe reddet (istersen kaldır)
    if score_int > 5000:
        return HttpResponseBadRequest("Score out of range")

    Score.objects.create(name=name, score=score_int)

    top_scores = list(
        Score.objects.all()
        .values("name", "score", "created_at")[:10]
    )
    for row in top_scores:
        row["created_at"] = row["created_at"].isoformat()

    return JsonResponse({"ok": True, "top_scores": top_scores})
