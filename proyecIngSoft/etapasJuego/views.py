import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import TeamGameSession
from .wordsearch.engine import create_soup, validate_selection


def etapas_index(request):
    # /etapasJuego/ → redirige a la primera etapa
    return redirect("etapa1")

# --- Helpers ---
def _get_or_create_session(request):
    """
    Obtiene/crea una partida por equipo (tablet).
    Usamos session_key de Django como team_id por defecto.
    """
    if not request.session.session_key:
        request.session.create()
    team_id = request.session.session_key

    tgs = TeamGameSession.objects.filter(team_id=team_id, ended_at__isnull=True).order_by("-started_at").first()
    return tgs, team_id

def _ensure_active_session(team_id, words=None, board_size=10):
    # Busca una sesión "activa"
    tgs = TeamGameSession.objects.filter(
        team_id=team_id, ended_at__isnull=True
    ).order_by("-started_at").first()

    # Si existe pero ya está completa, ciérrala y fuerza nueva
    if tgs and tgs.words and set(tgs.found_words) == set(tgs.words):
        tgs.ended_at = timezone.now()
        tgs.save(update_fields=["ended_at"])
        tgs = None

    # Si no hay activa, crea una nueva
    if tgs is None:
        if words is None:
            words = ["custom", "white", "glass", "computer"]  # cambia por tu lista
        soup, dict_pos = create_soup(words=words, board_size=board_size)
        tgs = TeamGameSession.objects.create(
            team_id=team_id,
            board_size=board_size,
            words=words,
            soup=soup,
            dict_word_position=dict_pos,
            started_at=timezone.now(),
            active_selections={},
        )
    return tgs

def etapa1(request):
    return render(request, "etapasJuego/etapa1.html")

# --- API ---
@require_POST
def api_init(request):
    body = json.loads(request.body.decode("utf-8") or "{}")
    words = body.get("words")
    board_size = int(body.get("board_size", 10))

    _, team_id = _get_or_create_session(request)
    tgs = _ensure_active_session(team_id, words=words, board_size=board_size)

    return JsonResponse({
        "team_id": tgs.team_id,
        "board_size": tgs.board_size,
        "soup": tgs.soup,
        "words": tgs.words,
        "found_words": tgs.found_words,
        "progress_pct": tgs.progress_pct,
        "active_selections": tgs.active_selections,
        "ended": tgs.ended_at is not None,
    })

@require_POST
def api_reset(request):
    _, team_id = _get_or_create_session(request)
    TeamGameSession.objects.filter(team_id=team_id, ended_at__isnull=True).update(ended_at=timezone.now())
    # nueva partida
    tgs = _ensure_active_session(team_id)
    return JsonResponse({"ok": True, "new_session": tgs.id})

@require_POST
def api_select_start(request):
    """
    Inicia una selección (multi-touch). Permite máximo 2 selecciones activas.
    Entrada: {"color":"#hex", "start":[i,j]}
    Devuelve selection_id: "s1" o "s2"
    """
    _, team_id = _get_or_create_session(request)
    tgs = _ensure_active_session(team_id)

    body = json.loads(request.body.decode("utf-8"))
    color = body.get("color")
    start = body.get("start")

    act = dict(tgs.active_selections)
    if len(act) >= 2:
        return JsonResponse({"ok": False, "error": "max_selections"}, status=409)

    sid = "s1" if "s1" not in act else "s2"
    act[sid] = {"color": color, "path": [start]}
    tgs.active_selections = act
    tgs.save(update_fields=["active_selections"])
    return JsonResponse({"ok": True, "selection_id": sid, "active_selections": act})

@require_POST
def api_select_extend(request):
    """
    Extiende la selección (drag/pointermove).
    Entrada: {"selection_id":"s1","cell":[i,j]}
    """
    _, team_id = _get_or_create_session(request)
    tgs = _ensure_active_session(team_id)

    body = json.loads(request.body.decode("utf-8"))
    sid = body.get("selection_id")
    cell = body.get("cell")

    act = dict(tgs.active_selections)
    if sid not in act:
        return JsonResponse({"ok": False, "error": "invalid_selection"}, status=400)

    path = act[sid].get("path", [])
    if cell not in path:
        path.append(cell)
    act[sid]["path"] = path

    # “Bloqueo” suave: que otras selecciones no puedan usar estas celdas
    locked = set(map(tuple, tgs.locked_cells))
    for c in path:
        locked.add(tuple(c))
    tgs.locked_cells = list(locked)

    tgs.active_selections = act
    tgs.save(update_fields=["active_selections", "locked_cells"])
    return JsonResponse({"ok": True, "active_selections": act, "locked_cells": tgs.locked_cells})

@require_POST
def api_select_commit(request):
    """
    El jugador suelta (pointerup). Validamos la palabra.
    Entrada: {"selection_id":"s1"}
    """
    _, team_id = _get_or_create_session(request)
    tgs = _ensure_active_session(team_id)

    body = json.loads(request.body.decode("utf-8"))
    sid = body.get("selection_id")

    act = dict(tgs.active_selections)
    if sid not in act:
        return JsonResponse({"ok": False, "error": "invalid_selection"}, status=400)

    path = act[sid].get("path", [])
    found, word = validate_selection(path, tgs.dict_word_position)

    message = None
    if found and word and word not in tgs.found_words:
        tgs.mark_found(word)
        message = "found"
    elif found and word in tgs.found_words:
        message = "already_found"
    else:
        message = "not_found"

    # Liberamos bloqueo de las celdas de esta selección
    locked = set(map(tuple, tgs.locked_cells))
    for c in path:
        locked.discard(tuple(c))
    tgs.locked_cells = list(locked)

    # Quitamos la selección activa
    del act[sid]
    tgs.active_selections = act
    tgs.save(update_fields=["active_selections", "locked_cells", "found_words", "progress_pct", "ended_at"])

    return JsonResponse({
        "ok": True,
        "result": message,
        "word": word,
        "found_words": tgs.found_words,
        "progress_pct": tgs.progress_pct,
        "ended": tgs.ended_at is not None
    })

################################################################

def etapa2(request):
    return render(request, "etapasJuego/etapa2.html")

def etapa3(request):
    return render(request, "etapasJuego/etapa3.html")

def etapa4(request):
    return render(request, "etapasJuego/etapa4.html")