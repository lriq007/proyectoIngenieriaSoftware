import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import TeamGameSession, Desafio, Topic, Challenge, Project, EmpathyMap, Pitch
from .wordsearch.engine import create_soup, validate_selection
from django.urls import reverse
from django.db import connection
from django.templatetags.static import static
from .context import get_or_create_team_for_request
from .services.pitch_ai import generar_sugerencias_pitch, actualizar_score_ai



def etapas_index(request):
    # /etapasJuego/ → redirige a la primera etapa
    return redirect("etapa1")


def seleccion_modalidad(request):
    """
    Pantalla previa para tablets: elige modalidad antes de la sopa de letras.
    Asume que la tablet ya tiene sesión iniciada.
    """
    return render(request, "etapasJuego/seleccion_modalidad.html")


def rompehielo(request):
    """
    Placeholder de la opción 'No nos conocemos': presentación + rompehielo.
    La lógica de temporizador/dinámica se agregará en un prompt posterior.
    """
    return render(request, "etapasJuego/rompehielo.html")


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
    sesion, team = get_or_create_team_for_request(request)
    return render(request, "etapasJuego/etapa1.html", {"sesion": sesion, "team": team})


def etapa2_tema(request):
    """
    Pantalla de Etapa 2.0: selección de tema.

    - En GET: muestra todas las opciones de Topic activos.
    - En POST: recibe un topic_id, lo guarda en la sesión y redirige a Etapa 2.
    """
    sesion, team = get_or_create_team_for_request(request)

    if request.method == "POST":
        topic_id = request.POST.get("topic_id")
        if topic_id:
            topic = get_object_or_404(Topic, id=topic_id, activo=True)
            # Guardamos solo el ID en la sesión para usarlo después en Etapa 2
            request.session["topic_id"] = topic.id
            request.session.modified = True
            # Redirigimos a la vista de Etapa 2 (listado de desafíos)
            return redirect("etapa2")

        # Si no viene topic_id, simplemente recargamos la misma pantalla
        return redirect("etapa2_tema")

    # GET: mostrar todos los temas activos
    topics = Topic.objects.filter(activo=True).order_by("nombre")

    context = {
        "sesion": sesion,
        "team": team,
        "topics": topics,
    }
    return render(request, "etapasJuego/etapa2_0.html", context)

# --- API ---
@require_POST
def api_init(request):
    body = json.loads(request.body.decode("utf-8") or "{}")
    words = body.get("words")
    board_size = int(body.get("board_size", 10))

    _, team_id = _get_or_create_session(request)
    tgs = _ensure_active_session(team_id, words=words, board_size=board_size)
    # Asociar Team actual con esta sesión de sopa (opcional, no rompe nada)
    _, team = get_or_create_team_for_request(request)
    if tgs.equipo is None:
        tgs.equipo = team
        tgs.save(update_fields=["equipo"])

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
    Etapa 2: listado de desafíos para el tema seleccionado.
    """
    sesion, team = get_or_create_team_for_request(request)

    topic_id = request.session.get("topic_id")
    if not topic_id:
        # Si no hay tema seleccionado, volvemos a Etapa 2.0
        return redirect("etapa2_tema")

    topic = get_object_or_404(Topic, id=topic_id, activo=True)

    desafios = (
        Desafio.objects.filter(
            challenge__topic=topic,
            activo=True,
            challenge__activo=True,
        )
        .select_related("challenge")
        .order_by("challenge__orden", "numero", "id")
    )

    project = getattr(team, "proyecto", None)

    context = {
        "sesion": sesion,
        "team": team,
        "topic": topic,
        "desafios": desafios,
        "project": project,
    }
    return render(request, "etapasJuego/etapa2.html", context)


####################################################

def etapa3(request):
    sesion, team = get_or_create_team_for_request(request)
    project = None

    project_id = request.session.get("project_id")
    if project_id:
        project = Project.objects.filter(id=project_id, equipo=team).first()

    return render(
        request,
        "etapasJuego/etapa3.html",
        {
            "sesion": sesion,
            "team": team,
            "project": project,
        },
    )


@require_POST
def etapa3_guardar_foto(request):
    """
    Recibe la imagen subida en Etapa 3 y la guarda en Project.foto_prototipo
    para el equipo actual, manteniendo la relación con tema, challenge y desafío
    seleccionados en Etapa 2.
    """
    # 1) Identificar la sesión de juego y el equipo actual
    sesion, team = get_or_create_team_for_request(request)

    # 2) Recuperar el project_id guardado en la sesión durante Etapa 2
    project_id = request.session.get("project_id")
    if not project_id:
        # Si por alguna razón no hay proyecto, simplemente volvemos a Etapa 3
        # (no romper la UX ni lanzar error 500)
        return redirect("etapa3")

    # 3) Obtener el Project asociado a este equipo
    project = get_object_or_404(Project, id=project_id, equipo=team)

    # 4) Obtener los archivos de imagen desde request.FILES
    #    Los nombres deben coincidir con los atributos "name" de los inputs en la template
    image_file = request.FILES.get("lego_image")
    group_photo = request.FILES.get("foto_grupal")
    resumen_idea = (request.POST.get("resumen_idea", "") or "").strip()
    if resumen_idea and len(resumen_idea) < 70:
        resumen_idea = ""
    if resumen_idea and len(resumen_idea) > 280:
        resumen_idea = resumen_idea[:280]

    campos = []
    if image_file:
        # 5) Guardar la imagen en foto_prototipo sin alterar otros campos
        project.foto_prototipo = image_file
        campos.append("foto_prototipo")
    if group_photo:
        project.foto_grupal = group_photo
        campos.append("foto_grupal")
    if resumen_idea:
        project.resumen_idea = resumen_idea
        campos.append("resumen_idea")

    if campos:
        project.save(update_fields=campos)
        team.update_tokens()
    # Si no hay archivo, no hacer nada destructivo; simplemente continuar

    # 6) Redirigir a Etapa 4 (Pitch) manteniendo el flujo del juego
    return redirect("etapa4")

def etapa4(request):
    project_id = request.session.get("project_id")
    if not project_id:
        return HttpResponse(
            "Error: no hay project_id en la sesión. Vuelve a Etapa 2 y selecciona el desafío de nuevo.",
            status=400,
        )

    project = get_object_or_404(
        Project.objects.select_related(
            "desafio",
            "desafio__topic",
            "selected_desafio",
        ),
        id=project_id,
    )

    emp_map = getattr(project, "mapa_empatia", None)
    if emp_map is None:
        emp_map = EmpathyMap.objects.filter(proyecto=project).first()

    pitch, _ = Pitch.objects.get_or_create(proyecto=project)

    if not pitch.sugerencias_ia:
        topic = getattr(project.desafio, "topic", None)
        challenge = project.desafio
        desafio = project.selected_desafio
        sugerencias = generar_sugerencias_pitch(topic, challenge, desafio, emp_map)
        if sugerencias:
            pitch.sugerencias_ia = sugerencias
            pitch.save(update_fields=["sugerencias_ia"])
        else:
            sugerencias = ""
    else:
        sugerencias = pitch.sugerencias_ia

    desafio_numero = getattr(project.selected_desafio, "id", None) or getattr(project.desafio, "id", None)

    bubble_map = {}
    if emp_map:
        bubble_map = emp_map.datos_extra or {
            "respuestas": {
                "likes_dislikes": getattr(emp_map, "gustos", ""),
                "obstacles": getattr(emp_map, "problemas", ""),
                "feelings": getattr(emp_map, "miedos", ""),
                "others_say": getattr(emp_map, "contexto", ""),
                "hobbies": getattr(emp_map, "hobbies", ""),
            }
        }
    else:
        mapas = request.session.get("etapa2_mapas", {})
        bubble_map = mapas.get(str(desafio_numero), {})

    pitch_payload = {
        "desafio_numero": desafio_numero,
        "bubble_map": bubble_map,
    }

    sesion = getattr(project.equipo, "sesion", None)
    team = getattr(project, "equipo", None)
    return render(
        request,
        "etapasJuego/etapa4.html",
        {
            "sesion": sesion,
            "pitch_tips": sugerencias,
            "pitch_payload": pitch_payload,
            "pitch_text": pitch.guion,
            "team": team,
        },
    )


@require_POST
def etapa4_guardar_pitch(request):
    """
    Guarda el texto del pitch, evalúa score_ai y actualiza tokens del equipo.
    """
    project_id = request.session.get("project_id")
    if not project_id:
        return JsonResponse({"ok": False, "error": "no_project"}, status=400)

    project = get_object_or_404(Project, id=project_id)
    pitch, _ = Pitch.objects.get_or_create(proyecto=project)

    pitch_text = request.POST.get("pitch_text") or request.POST.get("pitch")
    if pitch_text is None:
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
            pitch_text = body.get("pitch_text") or body.get("pitch")
        except Exception:
            pitch_text = None

    pitch_text = (pitch_text or "").strip()
    pitch.guion = pitch_text
    pitch.save(update_fields=["guion"])

    actualizar_score_ai(pitch)

    team = getattr(project, "equipo", None)
    if team:
        team.update_tokens()

    return JsonResponse({"ok": True, "score_ai": pitch.score_ai})


@require_POST
def etapa2_seleccionar(request):
    """
    Guarda el desafío seleccionado para el equipo actual como parte de su Project.
    """
    sesion, team = get_or_create_team_for_request(request)

    topic_id = request.session.get("topic_id")
    if not topic_id:
        return redirect("etapa2_tema")

    topic = get_object_or_404(Topic, id=topic_id, activo=True)

    challenge_id = request.POST.get("challenge_id")
    if not challenge_id:
        # Si no viene challenge_id, volvemos al listado de desafíos
        return redirect("etapa2")

    challenge = get_object_or_404(
        Challenge,
        id=challenge_id,
        topic=topic,
        activo=True
    )
    desafio_id = request.POST.get("desafio_id")
    selected_desafio = None
    if desafio_id:
        selected_desafio = get_object_or_404(Desafio, pk=desafio_id)

    project, created = Project.objects.get_or_create(
        equipo=team,
        defaults={"desafio": challenge},
    )
    if not created:
        project.desafio = challenge
        project.save(update_fields=["desafio"])

    if selected_desafio:
        project.selected_desafio = selected_desafio
        project.save(update_fields=["selected_desafio"])

    request.session["project_id"] = project.id
    request.session["etapa2_desafio_numero"] = selected_desafio.id if selected_desafio else challenge.id
    request.session.modified = True

    return redirect("etapa2_1")


def etapa2_1(request):
    """Pantalla placeholder para el bubble map, muestra el desafío elegido."""
    sesion, team = get_or_create_team_for_request(request)
    project_id = request.session.get("project_id")
    if project_id:
        project = get_object_or_404(Project, id=project_id)
        challenge = project.desafio
        selected_desafio = project.selected_desafio
        numero = request.session.get("etapa2_desafio_numero") or (selected_desafio.id if selected_desafio else challenge.id)
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

        desafio = None
        if selected_desafio:
            desafio = {
                "titulo": selected_desafio.titulo,
                "numero": numero,
                "historia": selected_desafio.historia,
                "personaje": selected_desafio.personaje,
                "imagen_personaje": selected_desafio.imagen_personaje,
            }
        else:
            desafio = {
                "titulo": challenge.titulo,
                "numero": numero,
            }

        persona_map = {
            1: "etapasJuego/img/persona1.png",
            2: "etapasJuego/img/persona2.png",
            3: "etapasJuego/img/persona3.png",
        }
        try:
            numero_int = int(numero) if numero is not None else None
        except (TypeError, ValueError):
            numero_int = None

        desafio_image = persona_map.get(numero_int) if numero_int else None
        if not desafio_image and selected_desafio:
            if selected_desafio.imagen_personaje:
                desafio_image = selected_desafio.imagen_personaje.url
        if not desafio_image and desafio:
            desafio_image = desafio.get("imagen_personaje")

        sesion_ctx = getattr(project.equipo, "sesion", None) or getattr(team, "sesion", None)
        return render(
            request,
            "etapasJuego/etapa2_1.html",
            {
                "sesion": sesion_ctx,
                "team": team,
                "desafio": desafio,
                "bubble_questions": bubble_items,
                "bubble_responses": respuestas,
                "desafio_persona_image": desafio_image,
            },
        )

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

    sesion_ctx = getattr(team, "sesion", None)
    return render(
        request,
        "etapasJuego/etapa2_1.html",
        {
            "sesion": sesion_ctx,
            "team": team,
            "desafio": desafio,
            "bubble_questions": bubble_items,
            "bubble_responses": respuestas,
            "desafio_persona_image": desafio_image,
        },
    )


@require_POST
def etapa2_guardar_mapa(request):
    """
    Vista AJAX/POST que guarda el Bubble Map.
    - Mantiene el guardado en sesión como backup.
    - Agrega guardado persistente en EmpathyMap asociado al Project.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    sesion, team = get_or_create_team_for_request(request)

    # 1. Obtener JSON del Bubble Map
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    # 2. Guardar copia en la sesión (backup NO se elimina)
    request.session["etapa2_mapas"] = data
    request.session.modified = True

    # 3. Obtener project_id desde la sesión
    project_id = request.session.get("project_id")
    if not project_id:
        # No hay proyecto aún: no se rompe la UX, se guarda solo en sesión
        return JsonResponse({
            "ok": True,
            "warning": "no_project_yet",
            "msg": "Mapa guardado en sesión pero no en base de datos."
        })

    # 4. Obtener el Project vinculado al equipo
    project = get_object_or_404(Project, id=project_id, equipo=team)

    # 5. Obtener o crear EmpathyMap persistente
    emp_map, _ = EmpathyMap.objects.get_or_create(proyecto=project)

    # 6. Extraer clusters relevantes del JSON
    # Nuevo formato: viene un objeto "respuestas" con las claves del bubble map
    respuestas = data.get("respuestas") or {}

    if respuestas:
        # Mapeo desde las claves de bubble-map.js a los campos del modelo EmpathyMap
        gustos = respuestas.get("likes_dislikes", "")
        problemas = respuestas.get("obstacles", "")
        miedos = respuestas.get("feelings", "")
        contexto = respuestas.get("others_say", "")
        hobbies = respuestas.get("hobbies", "")
    else:
        # Compatibilidad con formato antiguo (si el JSON viniera con las claves planas)
        gustos = data.get("gustos", "")
        problemas = data.get("problemas", "")
        miedos = data.get("miedos", "")
        contexto = data.get("contexto", "")
        hobbies = data.get("hobbies", "")

    # 7. Guardar el JSON completo y los campos principales
    emp_map.gustos = gustos
    emp_map.problemas = problemas
    emp_map.miedos = miedos
    emp_map.contexto = contexto
    emp_map.hobbies = hobbies
    emp_map.datos_extra = data  # full JSON
    emp_map.save()
    team.update_tokens()

    return JsonResponse({"ok": True})

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
