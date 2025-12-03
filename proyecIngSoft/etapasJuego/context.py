from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import GameSession, Team, Tablet


def get_current_gamesession() -> GameSession | None:
    """
    Devuelve la GameSession 'actual' para el contexto del juego.

    Por ahora, la implementación es simple:
    - Si existe al menos una GameSession, devuelve la más reciente.
    - Si no existe ninguna, crea una GameSession 'demo' para entorno de desarrollo.

    Esta función se puede mejorar más adelante para:
    - Seleccionar la sesión en base a un código en la URL.
    - Seleccionar según el profesor autenticado, etc.
    """
    sesion = GameSession.objects.order_by("-id").first()
    if sesion is not None:
        return sesion

    # Crear una sesión demo mínima si no existe ninguna.
    sesion = GameSession.objects.create(
        nombre="Sesión Demo",
        codigo="DEMO01",
        fecha=timezone.now().date(),
        # No seteamos tema ni otros campos opcionales aquí.
    )
    return sesion


def get_or_create_team_for_request(request) -> tuple[GameSession, Team]:
    """
    Asocia la request actual (navegador/tablet) con un Team dentro de la GameSession actual.

    Prioriza la tablet autenticada (request.session['tablet_id']) como fuente de identidad.
    Si no hay tablet en sesión, usa el fallback anterior basado en session_key.
    """
    # Asegurarse de que la sesión de Django existe
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    tablet_id = request.session.get("tablet_id")
    team_id = request.session.get("team_id")

    # 1) Si hay tablet autenticada en sesión, priorizarla
    if tablet_id:
        tablet = Tablet.objects.filter(id=tablet_id).select_related("sesion").first()
        if tablet:
            sesion = tablet.sesion or get_current_gamesession()
            # Si ya guardamos team_id en sesión, intentar usarlo
            team = None
            if team_id:
                team = Team.objects.filter(id=team_id, sesion=sesion).first()
            # Si no, intentar encontrar Team por tablet
            if team is None:
                team = Team.objects.filter(tablet=tablet).first()
            # Si sigue sin existir, crear uno nuevo ligado a la tablet
            if team is None:
                codigo_grupo = (tablet.codigo or "A")[:1] or "A"
                team = Team.objects.create(
                    sesion=sesion,
                    nombre=f"Equipo {codigo_grupo}",
                    codigo_grupo=codigo_grupo,
                    tablet=tablet,
                )
            request.session["team_id"] = team.id
            request.session.modified = True
            return sesion, team

    # 2) Fallback legacy: usar session_key y un Team genérico
    sesion = get_current_gamesession()

    team = None
    if team_id:
        team = Team.objects.filter(id=team_id, sesion=sesion).first()

    if team is None:
        team, _ = Team.objects.get_or_create(
            sesion=sesion,
            codigo_grupo="A",  # valor placeholder legacy
            defaults={
                "nombre": f"Equipo {session_key[:5]}",
            },
        )
        request.session["team_id"] = team.id
        request.session.modified = True

    return sesion, team
