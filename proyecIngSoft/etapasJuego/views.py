import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import TeamGameSession
from .wordsearch.engine import create_soup, validate_selection
from django.urls import reverse
from .models import Desafio
from django.db import connection
from django.templatetags.static import static



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
        "progress": float(tgs.progress_pct or 0.0),
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

### ETAPA 2: Desafíos ###

# ---------- Helpers de presentación ----------
def _desc_para_modal(d):
    """Usa descripcion_larga si existe; si no, historia; si no, resumen."""
    return (
        getattr(d, "descripcion_larga", "") 
        or getattr(d, "historia", "") 
        or getattr(d, "resumen", "") 
        or (d.get("historia", "") if isinstance(d, dict) else "")
    )

def _video_src(d):
    """
    Orden de prioridad:
      1) archivo subido (d.video_file.url)
      2) URL directa (d.video_url)
      3) fallback estático: /static/etapasJuego/videos/desafio<N>.mp4
    """
    vf = getattr(d, "video_file", None)
    if vf:
        try:
            return vf.url
        except Exception:
            pass
    vu = getattr(d, "video_url", "") or (d.get("video_url", "") if isinstance(d, dict) else "")
    if vu:
        return vu
    num = getattr(d, "numero", None) or (d.get("numero") if isinstance(d, dict) else None)
    if num:
        return static(f"etapasJuego/videos/desafio{num}.mp4")
    return ""

def _imagen_url(d):
    """Resuelve imagen_personaje.url o la clave 'imagen' del fallback."""
    ip = getattr(d, "imagen_personaje", None)
    if ip:
        try:
            return ip.url
        except Exception:
            pass
    return (d.get("imagen", "") if isinstance(d, dict) else getattr(d, "imagen", ""))


FALLBACK_DESAFIOS = [
    {
        "numero": 1,
        "titulo": "Tecnología adultos mayores",
        "historia": "Mejorar autonomía y conexión social.",
        "personaje": "Don Miguel",
        "imagen": "/static/etapasJuego/img/hombre-con-los-brazos-cruzados.png",
        "duracion_min": 3,
        "video_url": "/static/etapasJuego/videos/desafio1.mp4",
    },
    {
        "numero": 2,
        "titulo": "Fastfashion y zonas de desechos",
        "historia": "Impacto ambiental y social del consumo de ropa.",
        "personaje": "Ana",
        "imagen": "/static/etapasJuego/img/apuesto-hombre-apuntando-hacia-atras.png",
        "duracion_min": 3,
        "video_url": "/static/etapasJuego/videos/desafio2.mp4",
    },
    {
        "numero": 3,
        "titulo": "Sustentabilidad del agua en la agricultura",
        "historia": "Optimizar uso de agua y productividad.",
        "personaje": "Pedro",
        "imagen": "/static/etapasJuego/img/primer-plano-de-hombre-feliz-con-camiseta-blanca.png",
        "duracion_min": 3,
        "video_url": "/static/etapasJuego/videos/desafio3.mp4",
    },
]


BUBBLE_QUESTIONS = [
    {"key": "likes_dislikes", "label": "¿Qué le gusta y qué no le gusta?"},
    {"key": "feelings", "label": "¿Qué siente respecto a lo que le está pasando?"},
    {"key": "obstacles", "label": "¿Qué obstáculos está enfrentando?"},
    {"key": "others_say", "label": "¿Qué le dicen los demás?"},
    {"key": "hobbies", "label": "¿Cuáles son sus hobbies?"},
]


def _build_desafios_vm():
    """Genera la lista visual de desafíos desde BD o fallback."""
    desafios_vm = []

    try:
        if "etapasJuego_desafio" in connection.introspection.table_names():
            qs = Desafio.objects.filter(activo=True).order_by("numero")[:3]
            for d in qs:
                desafios_vm.append({
                    "numero":       d.numero,
                    "titulo":       d.titulo,
                    "descripcion":  _desc_para_modal(d),
                    "imagen":       _imagen_url(d),
                    "video_src":    _video_src(d),
                    "personaje":    getattr(d, "personaje", ""),
                    "duracion_min": getattr(d, "duracion_min", None),
                })
    except Exception:
        desafios_vm = []

    if not desafios_vm:
        for d in FALLBACK_DESAFIOS:
            desafios_vm.append({
                "numero":       d["numero"],
                "titulo":       d["titulo"],
                "descripcion":  _desc_para_modal(d),
                "imagen":       _imagen_url(d),
                "video_src":    _video_src(d),
                "personaje":    d.get("personaje", ""),
                "duracion_min": d.get("duracion_min"),
            })

    return desafios_vm

# ---------- Vista Etapa 2 (reemplazo) ----------
def etapa2(request):
    """
    Entrega al template una lista homogénea 'desafios' con:
    numero, titulo, descripcion, imagen, video_src, personaje, duracion_min.
    Funciona con BD real o con fallback (mock) editable.
    """
    desafios_vm = _build_desafios_vm()
    return render(request, "etapasJuego/etapa2.html", {"desafios": desafios_vm})


####################################################

def etapa3(request):
    return render(request, "etapasJuego/etapa3.html")

def etapa4(request):
    mapas = request.session.get("etapa2_mapas", {})
    desafio_numero = request.session.get("etapa2_desafio_numero")

    pitch_payload = {
        "desafio_numero": desafio_numero,
        "bubble_map": mapas.get(str(desafio_numero), {}),
    }

    pitch_tips = [
        {
            "title": "Idea clave pendiente",
            "content": "Aquí mostraremos una recomendación generada por OpenAI con base en el mapa de empatía del equipo.",
        },
        {
            "title": "Estructura sugerida",
            "content": "Una vez integrada la API, este espacio detallará cómo ordenar el pitch según los hallazgos del usuario.",
        },
        {
            "title": "Llamado a la acción",
            "content": "Este bloque resaltará la acción final que el pitch debe provocar, ajustada automáticamente con IA.",
        },
    ]

    return render(
        request,
        "etapasJuego/etapa4.html",
        {
            "pitch_tips": pitch_tips,
            "pitch_payload": pitch_payload,
        },
    )


@require_POST
def etapa2_seleccionar(request):
    """Guarda el desafío seleccionado y redirige a la vista de detalle."""
    numero = request.POST.get("desafio_numero")

    try:
        numero_int = int(numero)
    except (TypeError, ValueError):
        return redirect("etapa2")

    desafios = _build_desafios_vm()
    seleccionado = next((d for d in desafios if d["numero"] == numero_int), None)
    if not seleccionado:
        return redirect("etapa2")

    request.session["etapa2_desafio_numero"] = numero_int
    request.session.modified = True

    return redirect("etapa2_1")


def etapa2_1(request):
    """Pantalla placeholder para el bubble map, muestra el desafío elegido."""
    numero = request.session.get("etapa2_desafio_numero")
    if numero is None:
        return redirect("etapa2")

    desafios = _build_desafios_vm()
    desafio = next((d for d in desafios if d["numero"] == numero), None)

    if desafio is None:
        request.session.pop("etapa2_desafio_numero", None)
        request.session.modified = True
        return redirect("etapa2")

    mapas = request.session.get("etapa2_mapas", {})
    respuestas = mapas.get(str(numero), {})
    bubble_items = [
        {
            "key": q["key"],
            "label": q["label"],
            "answer": respuestas.get(q["key"], ""),
        }
        for q in BUBBLE_QUESTIONS
    ]

    persona_map = {
        1: "etapasJuego/img/persona1.png",
        2: "etapasJuego/img/persona2.png",
        3: "etapasJuego/img/persona3.png",
    }
    desafio_image = persona_map.get(desafio.get("numero"))
    if not desafio_image:
        desafio_image = desafio.get("imagen") or desafio.get("imagen_personaje")

    return render(
        request,
        "etapasJuego/etapa2_1.html",
        {
            "desafio": desafio,
            "bubble_questions": bubble_items,
            "bubble_responses": respuestas,
            "desafio_persona_image": desafio_image,
        },
    )


@require_POST
def etapa2_guardar_mapa(request):
    """Guarda temporalmente en sesión las respuestas del bubble map."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    numero = payload.get("desafio_numero")
    respuestas = payload.get("respuestas", {})

    try:
        numero_int = int(numero)
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_challenge"}, status=400)

    if not isinstance(respuestas, dict):
        return JsonResponse({"ok": False, "error": "invalid_payload"}, status=400)

    # Normaliza claves válidas.
    valid_keys = {q["key"] for q in BUBBLE_QUESTIONS}
    respuestas_filtradas = {}
    for key, value in respuestas.items():
        if key in valid_keys and isinstance(value, str):
            respuestas_filtradas[key] = value.strip()

    mapas = request.session.get("etapa2_mapas", {})
    mapas[str(numero_int)] = respuestas_filtradas
    request.session["etapa2_mapas"] = mapas
    request.session.modified = True

    return JsonResponse({"ok": True})
    return render(request, "etapasJuego/etapa4.html")

def ganador(request):
    return render(request, "etapasJuego/ganador.html")

def ranking(request):
    return render(request, "etapasJuego/ranking.html")

def qr(request):
    return render(request, 'etapasJuego/qr.html')

def feedback(request):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        return redirect('feedback_thank_you')
    return render(request, 'etapasJuego/feedback.html')

def inicio_juego(request):
    return render(request, 'etapasJuego/inicio_juego.html')