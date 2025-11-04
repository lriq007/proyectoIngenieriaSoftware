from django.db import models
from django.utils import timezone

# Create your models here.

#Aqui va la data que entregara la base de datos

#TABLE CONTADOR TOKENS

#TABLE GRUPO

#TABLE INTENTO DESAFIO

#TABLE DESAFIO

#TABLE DESAFIO

#TABLE ACTIVIDAD

#TABLE PITCH

#TABLE FEEDBACK PITCH

#TABLE IDEA EMPRENDIMIENTO

###############################################

class TeamGameSession(models.Model):
    id = models.BigAutoField(primary_key=True)
    team_id = models.CharField(max_length=64, db_index=True)
    board_size = models.PositiveIntegerField(default=10)
    words = models.JSONField(default=list)
    soup = models.JSONField(default=list)
    dict_word_position = models.JSONField(default=dict)
    found_words = models.JSONField(default=list)
    locked_cells = models.JSONField(default=list)
    active_selections = models.JSONField(default=dict)
    progress_pct = models.FloatField(default=0.0)
    started_at = models.DateTimeField(default=timezone.now)   # default
    ended_at = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(default=timezone.now)    # default
    actualizado_en = models.DateTimeField(auto_now=True)      # auto_now

    class Meta:
        managed = False
        db_table = 'team_game_session'

    # ✅ Agrega este método que tu vista usa:
    def mark_found(self, word: str):
        # normaliza
        words = list(self.words or [])
        found = list(self.found_words or [])

        if word and word not in found:
            found.append(word)
            self.found_words = found

        total = len(words)
        if total > 0:
            pct = 100.0 * (len(found) / total)
            self.progress_pct = min(100.0, round(pct, 2))
            if len(found) >= total and not self.ended_at:
                self.ended_at = timezone.now()
        else:
            self.progress_pct = 0.0

        # timestamps defensivos (aunque auto_now cubre actualizado_en)
        if not self.started_at:
            self.started_at = timezone.now()
        if not self.creado_en:
            self.creado_en = timezone.now()


class Desafio(models.Model):
    numero = models.PositiveSmallIntegerField(default=1)
    titulo = models.CharField(max_length=150)

    # Descripciones
    historia = models.TextField(help_text="Texto narrativo breve del desafío o problemática.")
    descripcion_larga = models.TextField(
        blank=True, null=True,
        help_text="Descripción más extensa que se mostrará en el modal."
    )

    # Personaje e imagen
    personaje = models.CharField(max_length=100)
    imagen_personaje = models.ImageField(
        upload_to="desafios/", blank=True, null=True,
        help_text="Imagen del personaje asociado."
    )

    # Video (archivo o URL)
    video_file = models.FileField(
        upload_to="desafios/videos/", blank=True, null=True,
        help_text="Archivo de video del desafío (loop)."
    )
    video_url = models.URLField(
        blank=True, null=True,
        help_text="Enlace directo a un video externo (YouTube, CDN o MP4)."
    )

    duracion_min = models.PositiveSmallIntegerField(default=3)
    etapa = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero}. {self.titulo}"
