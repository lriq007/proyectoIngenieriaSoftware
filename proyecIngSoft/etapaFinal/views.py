import json

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from etapasJuego.context import get_or_create_team_for_request
from etapasJuego.models import Evaluation, Team, Project
from login.models import Estudiante

# Create your views here.

def coevaluacion_home(request):
    sesion, team = get_or_create_team_for_request(request)
    equipos_a_evaluar = (
        Team.objects.filter(sesion=sesion)
        .exclude(id=team.id)
        .select_related("proyecto")
    )
    project = getattr(team, "proyecto", None)
    return render(
        request,
        "etapaFinal/index.html",
        {
            "sesion": sesion,
            "team_actual": team,
            "equipos_a_evaluar": equipos_a_evaluar,
            "project": project,
        },
    )


@require_POST
def save_coevaluacion(request):
    """
    Guarda/actualiza coevaluaciones enviadas desde el frontend.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"status": "error", "msg": "JSON inválido"}, status=400)

    sesion, evaluador_team = get_or_create_team_for_request(request)
    if evaluador_team is None:
        return JsonResponse({"status": "error", "msg": "El evaluador no tiene equipo asignado"}, status=400)

    evaluaciones = data.get("evaluaciones") if isinstance(data, dict) else data
    if not isinstance(evaluaciones, list):
        return JsonResponse({"status": "error", "msg": "Formato inválido"}, status=400)

    evaluados_ids = set()

    for item in evaluaciones:
        evaluado_id = item.get("evaluado_id")
        if not evaluado_id:
            continue

        evaluado_team = get_object_or_404(Team, id=evaluado_id, sesion=sesion)
        evaluados_ids.add(evaluado_team.id)

        puntaje_equipo = item.get("puntaje_equipo") or 0
        puntaje_empatia = item.get("puntaje_empatia") or 0
        puntaje_creatividad = item.get("puntaje_creatividad") or 0
        puntaje_comunicacion = item.get("puntaje_comunicacion") or 0
        comentario = item.get("comentario", "") or ""

        evaluacion, created = Evaluation.objects.get_or_create(
            sesion=sesion,
            evaluador=evaluador_team,
            evaluado=evaluado_team,
            defaults={
                "puntaje_equipo": puntaje_equipo,
                "puntaje_empatia": puntaje_empatia,
                "puntaje_creatividad": puntaje_creatividad,
                "puntaje_comunicacion": puntaje_comunicacion,
                "comentario": comentario,
            },
        )

        if not created:
            evaluacion.puntaje_equipo = puntaje_equipo
            evaluacion.puntaje_empatia = puntaje_empatia
            evaluacion.puntaje_creatividad = puntaje_creatividad
            evaluacion.puntaje_comunicacion = puntaje_comunicacion
            evaluacion.comentario = comentario
            evaluacion.save(update_fields=[
                "puntaje_equipo",
                "puntaje_empatia",
                "puntaje_creatividad",
                "puntaje_comunicacion",
                "comentario",
            ])

    for team_id in evaluados_ids:
        team_obj = Team.objects.filter(id=team_id).first()
        if team_obj:
            team_obj.update_tokens()

    return JsonResponse({"status": "ok", "ok": True, "msg": "Coevaluaciones guardadas"})


def final_resultados(request):
    sesion, team = get_or_create_team_for_request(request)
    ranking = (
        Team.objects.filter(sesion=sesion)
        .prefetch_related("estudiantes")
        .order_by("-tokens_totales", "nombre")
    )
    ganador = ranking.first() if ranking else None
    return render(
        request,
        "etapaFinal/final_resultados.html",
        {
            "sesion": sesion,
            "team_actual": team,
            "ranking": ranking,
            "ganador": ganador,
        },
    )


@require_POST
def upload_foto_grupal(request):
    """
    Guarda la foto grupal del proyecto del equipo actual.
    """
    sesion, team = get_or_create_team_for_request(request)
    if team is None:
        return JsonResponse({"ok": False, "msg": "Equipo no encontrado para esta sesión"}, status=400)

    project = getattr(team, "proyecto", None)
    if project is None:
        return JsonResponse({"ok": False, "msg": "No hay proyecto asociado al equipo"}, status=404)

    file = request.FILES.get("foto_grupal")
    if not file:
        return JsonResponse({"ok": False, "msg": "No se envió archivo"}, status=400)

    project.foto_grupal = file
    project.save(update_fields=["foto_grupal"])

    return JsonResponse({"ok": True, "msg": "Foto grupal guardada", "foto_url": project.foto_grupal.url})
