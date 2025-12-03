import random

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.conf import settings


class TeamGameSession(models.Model):
    id = models.BigAutoField(primary_key=True)
    team_id = models.CharField(max_length=64, db_index=True)
    board_size = models.PositiveIntegerField(default=10)

    # En SQLite, JSONField se guarda como TEXT internamente (OK).
    words = models.JSONField(default=list)
    soup = models.JSONField(default=list)
    dict_word_position = models.JSONField(default=dict)
    found_words = models.JSONField(default=list)
    locked_cells = models.JSONField(default=list)
    active_selections = models.JSONField(default=dict)

    progress_pct = models.FloatField(default=0.0)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    equipo = models.ForeignKey(
        "Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wordsearch_sessions",
        help_text="Equipo asociado a esta partida de sopa de letras (opcional).",
    )

    def __str__(self):
        return f"TeamGameSession(team={self.team_id}, progress={self.progress_pct:.1f}%)"

    # Útil para la lógica de la sopa de letras
    def mark_found(self, word: str):
        words = list(self.words or [])
        found = set(self.found_words or [])
        if word and word in words:
            found.add(word)
        self.found_words = list(found)
        total = len(words)
        self.progress_pct = (len(found) / total) * 100.0 if total else 0.0
        if total and len(found) >= total and not self.ended_at:
            self.ended_at = timezone.now()


class Desafio(models.Model):
    numero = models.PositiveSmallIntegerField(default=1)
    titulo = models.CharField(max_length=150)
    historia = models.TextField(help_text="Texto narrativo del desafío o problemática.")
    personaje = models.CharField(max_length=100)
    imagen_personaje = models.ImageField(upload_to="desafios/", blank=True, null=True)
    duracion_min = models.PositiveSmallIntegerField(default=3)
    etapa = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)
    # Cada Desafio pertenece a un Challenge; cada Challenge puede tener varios Desafios.
    challenge = models.ForeignKey(
        "Challenge",
        on_delete=models.CASCADE,
        related_name="desafios",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero}. {self.titulo}"


class GameSession(models.Model):
    THEME_CHOICES = [
        ("SALUD", "Salud"),
        ("SUST", "Sustentabilidad"),
        ("EDU", "Educación"),
    ]
    MODO_CHOICES = [
        ("LOGIN_RANDOM", "Asignación automática en el login"),
        ("PRECONFIGURADO", "Asignación preconfigurada por el profesor"),
    ]

    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    fecha = models.DateField(auto_now_add=True)
    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sesiones_juego",
    )
    # Metadato opcional de avance; hoy no gobierna la lógica de negocio.
    etapa_actual = models.CharField(max_length=20, default="ETAPA1")
    seccion = models.ForeignKey(
        "login.SeccionEstudiantes",
        related_name="sesiones",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    modo_asignacion = models.CharField(
        max_length=20,
        choices=MODO_CHOICES,
        default="LOGIN_RANDOM",
    )
    # Metadatos opcionales de duración por etapa (segundos); controlan los timers en frontend.
    duracion_etapa1_segundos = models.PositiveIntegerField(default=5 * 60)
    duracion_etapa2_segundos = models.PositiveIntegerField(default=10 * 60)
    duracion_etapa3_segundos = models.PositiveIntegerField(default=15 * 60)
    duracion_etapa4_segundos = models.PositiveIntegerField(default=10 * 60)
    qr_encuesta_url = models.URLField(blank=True, null=True)
    qr_instagram_url = models.URLField(blank=True, null=True)
    qr_linkedin_url = models.URLField(blank=True, null=True)

    # Nota: esta restricción asume que no existen múltiples GameSession para la misma sección.
    # Si hubiera duplicados previos, la migración fallará y se deberán resolver manualmente.
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["seccion"],
                name="unique_gamesession_per_seccion",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def crear_equipos_aleatorios_desde_seccion(self, minimo=4, maximo=8):
        """
        Crea equipos (Team) para esta sesión a partir de los estudiantes de la sección asociada,
        asignando estudiantes de forma aleatoria y respetando un rango aproximado de tamaño
        entre `minimo` y `maximo` integrantes por equipo.

        No elimina equipos existentes, y solo asigna estudiantes que todavía no tienen team.
        También asigna tablets disponibles de esta sesión a los nuevos equipos si hay tablets libres.
        Devuelve la lista de equipos creados.
        """
        from login.models import Estudiante
        from .models import Team, Tablet  # use local imports to avoid circular issues

        if not self.seccion:
            return []

        estudiantes_qs = Estudiante.objects.filter(seccion=self.seccion, team__isnull=True)
        estudiantes = list(estudiantes_qs)

        if not estudiantes:
            return []

        total = len(estudiantes)

        random.shuffle(estudiantes)

        num_equipos = max(1, (total + maximo - 1) // maximo)

        equipos_creados = []

        existing_codes = set(
            Team.objects.filter(sesion=self).values_list("codigo_grupo", flat=True)
        )

        def siguiente_codigo_grupo():
            letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            idx = 0
            while True:
                base = letras[idx % len(letras)]
                sufijo = idx // len(letras)
                code = base if sufijo == 0 else f"{base}{sufijo}"
                idx += 1
                if code not in existing_codes:
                    existing_codes.add(code)
                    return code

        for _ in range(num_equipos):
            codigo = siguiente_codigo_grupo()
            team = Team.objects.create(
                sesion=self,
                nombre=f"Equipo {codigo}",
                codigo_grupo=codigo,
            )

            tablet_libre = Tablet.objects.filter(sesion=self, team__isnull=True).first()
            if tablet_libre is not None:
                team.tablet = tablet_libre
                team.save()

            equipos_creados.append(team)

        idx = 0
        for est in estudiantes:
            equipo = equipos_creados[idx % len(equipos_creados)]
            est.team = equipo
            est.save()
            idx += 1

        return equipos_creados

    def clean(self):
        super().clean()
        if self.seccion:
            exists = GameSession.objects.exclude(pk=self.pk).filter(seccion=self.seccion).exists()
            if exists:
                raise ValidationError("Ya existe una sesión de juego asociada a esta sección. Solo se permite una sesión por sección.")


class Tablet(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    codigo_acceso = models.CharField(
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )
    descripcion = models.CharField(max_length=200, blank=True)
    sesion = models.ForeignKey(
        "GameSession",
        related_name="tablets",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        """
        Genera un codigo_acceso único de exactamente 4 dígitos (0000–9999)
        si aún no existe.
        """
        if not self.codigo_acceso:
            while True:
                code = get_random_string(
                    4,
                    allowed_chars="0123456789"
                )
                if not type(self).objects.filter(codigo_acceso=code).exists():
                    self.codigo_acceso = code
                    break

        super().save(*args, **kwargs)


class Team(models.Model):
    nombre = models.CharField(max_length=100)
    sesion = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="equipos")
    codigo_grupo = models.CharField(max_length=1)
    tokens_empatia = models.PositiveIntegerField(default=0)
    tokens_creatividad = models.PositiveIntegerField(default=0)
    tokens_evaluacion = models.PositiveIntegerField(default=0)
    tokens_totales = models.PositiveIntegerField(default=0)
    tablet = models.OneToOneField(
        "Tablet",
        related_name="team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Nota: la asignación automática de Tablet se centraliza aquí
    # para que cualquier Team que se asocie a una GameSession
    # obtenga una Tablet disponible de esa misma sesión (si existe).
    def assign_tablet_automatically(self):
        if self.sesion and self.tablet is None:
            tablet_libre = Tablet.objects.filter(
                sesion=self.sesion,
                team__isnull=True,
            ).order_by("id").first()
            if tablet_libre is not None:
                self.tablet = tablet_libre

    def save(self, *args, **kwargs):
        self.assign_tablet_automatically()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Equipo {self.nombre} [{self.codigo_grupo}]"

    def count_estudiantes(self):
        return self.estudiantes.count()

    def has_cupo(self):
        return self.count_estudiantes() < 8

    def meets_minimum(self):
        return self.count_estudiantes() >= 4

    def update_tokens(self):
        """
        Recalcula y guarda los tokens del equipo en base al estado actual
        de las distintas etapas (EmpathyMap, Project, Pitch, Evaluation, TeamGameSession).
        """
        from etapasJuego.services.scoring import recompute_and_save_team_tokens
        recompute_and_save_team_tokens(self)


class Topic(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(
        upload_to="topics/",
        blank=True,
        null=True,
        help_text="Imagen para mostrar en la tarjeta del tema.",
    )
    color_hex = models.CharField(
        max_length=7,
        blank=True,
        help_text="Color asociado al tema (ej: #FFCC00).",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tema"
        verbose_name_plural = "Temas"

    def __str__(self):
        return self.nombre


class Challenge(models.Model):
    topic = models.ForeignKey(
        "Topic",
        on_delete=models.PROTECT,
        related_name="desafios",
        help_text="Tema al que pertenece este desafío.",
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(
        default=1,
        help_text="Orden en que se mostrará el desafío dentro del tema.",
    )
    video_file = models.FileField(
        upload_to="challenge_videos/",
        blank=True,
        null=True,
        help_text="Archivo de video asociado a este desafío (opcional).",
    )

    def __str__(self):
        return f"[{self.topic.nombre}] {self.titulo}"


class Project(models.Model):
    equipo = models.OneToOneField(Team, on_delete=models.CASCADE, related_name="proyecto")
    desafio = models.ForeignKey(Challenge, on_delete=models.PROTECT, related_name="proyectos")
    selected_desafio = models.ForeignKey(
        Desafio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_selected",
    )
    resumen_idea = models.TextField(blank=True)
    foto_prototipo = models.ImageField(upload_to="prototipos/", blank=True, null=True)
    # Reservado para uso futuro (foto de equipo); no se usa en el flujo actual.
    foto_grupal = models.ImageField(upload_to="fotos_grupales/", blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proyecto de {self.equipo} - {self.desafio}"


class EmpathyMap(models.Model):
    proyecto = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="mapa_empatia")
    gustos = models.TextField(blank=True)
    problemas = models.TextField(blank=True)
    miedos = models.TextField(blank=True)
    contexto = models.TextField(blank=True)
    hobbies = models.TextField(blank=True, null=True)
    # Backup JSON del mapa de empatía; los campos canónicos son gustos/problemas/miedos/contexto/hobbies.
    datos_extra = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Mapa de empatía de {self.proyecto}"


class Pitch(models.Model):
    proyecto = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="pitch")
    guion = models.TextField(blank=True)
    sugerencias_ia = models.TextField(blank=True)
    score_ai = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Puntaje automático 1-5 del pitch según IA.",
    )
    # Tiempos objetivo (preparación/presentación) para futuras funcionalidades; hoy solo metadatos.
    tiempo_preparacion_seg = models.PositiveIntegerField(default=6 * 60)
    tiempo_presentacion_seg = models.PositiveIntegerField(default=90)

    def __str__(self):
        return f"Pitch - {self.proyecto}"


class Evaluation(models.Model):
    sesion = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="evaluaciones")
    evaluador = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="evaluaciones_realizadas")
    evaluado = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="evaluaciones_recibidas")
    puntaje_equipo = models.PositiveIntegerField()
    puntaje_empatia = models.PositiveIntegerField()
    puntaje_creatividad = models.PositiveIntegerField()
    puntaje_comunicacion = models.PositiveIntegerField()
    comentario = models.TextField(blank=True)

    class Meta:
        unique_together = ("sesion", "evaluador", "evaluado")

    def __str__(self):
        return f"Eval {self.evaluador} \u2192 {self.evaluado} ({self.sesion.codigo})"
