"""
Funciones de apoyo para calcular los tokens de un equipo por etapa.
"""

from django.db.models import Avg

from etapasJuego.models import (
    EmpathyMap,
    Evaluation,
    Pitch,
    Project,
    Team,
    TeamGameSession,
)


def _tokens_etapa1(team: Team) -> int:
    """
    Calcula tokens de la etapa 1 (sopa de letras) según el progreso de la última sesión.
    """
    session = (
        TeamGameSession.objects.filter(equipo=team)
        .order_by("-id")
        .first()
    )
    if session is None or session.progress_pct is None:
        return 0

    progress = float(session.progress_pct)
    if progress == 100:
        return 3
    if 80 <= progress < 100:
        return 2
    if 40 <= progress < 80:
        return 1
    return 0


def _tokens_etapa2_empatia(team: Team) -> int:
    """
    Calcula tokens de empatía según los campos completados del mapa de empatía.
    """
    emp_map = (
        EmpathyMap.objects.filter(proyecto__equipo=team)
        .order_by("-id")
        .first()
    )
    if emp_map is None:
        return 0

    fields = [
        getattr(emp_map, "gustos", "") or "",
        getattr(emp_map, "problemas", "") or "",
        getattr(emp_map, "miedos", "") or "",
        getattr(emp_map, "contexto", "") or "",
        getattr(emp_map, "hobbies", "") or "",
    ]

    tokens = sum(1 for value in fields if value.strip())
    all_filled = tokens == len(fields) and tokens > 0
    if all_filled:
        tokens += 1

    return min(tokens, 5)


def _tokens_etapa3_creatividad(team: Team) -> int:
    """
    Calcula tokens de creatividad por el prototipo y resumen del proyecto.
    """
    project = (
        Project.objects.filter(equipo=team)
        .order_by("-id")
        .first()
    )
    if project is None or not project.foto_prototipo:
        return 0

    resumen = (project.resumen_idea or "").strip()
    length = len(resumen)

    if length < 50:
        return 1
    if 50 <= length < 200:
        return 2
    return 4


def _tokens_etapa4_creatividad(team: Team) -> int:
    """
    Calcula tokens de creatividad a partir del puntaje automático del pitch (score_ai).
    """
    pitch = (
        Pitch.objects.filter(proyecto__equipo=team)
        .order_by("-id")
        .first()
    )
    if pitch is None or pitch.score_ai is None:
        return 0

    score = pitch.score_ai
    if score in (1, 2):
        return 0
    if score == 3:
        return 1
    if score == 4:
        return 2
    if score == 5:
        return 3
    return 0


def _tokens_etapa_final_eval(team: Team) -> int:
    """
    Calcula tokens finales a partir del promedio de puntaje_equipo en coevaluaciones.
    """
    avg_data = Evaluation.objects.filter(evaluado=team).aggregate(
        avg_equipo=Avg("puntaje_equipo")
    )
    avg_equipo = avg_data.get("avg_equipo")
    if avg_equipo is None:
        return 0

    avg_value = float(avg_equipo)
    if avg_value < 2.5:
        return 0
    if 2.5 <= avg_value < 3.5:
        return 2
    if 3.5 <= avg_value < 4.5:
        return 4
    return 6


def compute_tokens_for_team(team: Team) -> dict:
    """
    Devuelve el desglose de tokens para un equipo, agrupado por categoría.
    """
    empatia = _tokens_etapa2_empatia(team)
    creatividad = _tokens_etapa3_creatividad(team) + _tokens_etapa4_creatividad(team)
    evaluacion = _tokens_etapa1(team) + _tokens_etapa_final_eval(team)
    total = empatia + creatividad + evaluacion

    return {
        "empatia": empatia,
        "creatividad": creatividad,
        "evaluacion": evaluacion,
        "total": total,
    }


def recompute_and_save_team_tokens(team: Team) -> None:
    """
    Recalcula y persiste los tokens de un equipo en sus campos canónicos.
    """
    tokens = compute_tokens_for_team(team)
    team.tokens_empatia = tokens["empatia"]
    team.tokens_creatividad = tokens["creatividad"]
    team.tokens_evaluacion = tokens["evaluacion"]
    team.tokens_totales = tokens["total"]
    team.save(
        update_fields=[
            "tokens_empatia",
            "tokens_creatividad",
            "tokens_evaluacion",
            "tokens_totales",
        ]
    )
