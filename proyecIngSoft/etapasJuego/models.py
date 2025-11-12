from django.db import models
from django.utils import timezone

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

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero}. {self.titulo}"
