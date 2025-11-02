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
    team_id = models.CharField(max_length=64, db_index=True)  # un identificador por tablet/equipo
    board_size = models.PositiveIntegerField(default=10)
    words = models.JSONField(default=list)  # lista de palabras
    soup = models.JSONField(default=list)   # matriz de letras
    dict_word_position = models.JSONField(default=dict)  # {palabra: [(i,j), ...]}

    found_words = models.JSONField(default=list)          # palabras ya encontradas
    locked_cells = models.JSONField(default=list)         # celdas bloqueadas temporalmente [(i,j), ...]
    progress_pct = models.FloatField(default=0.0)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    # hasta 2 selecciones activas: { "s1": {"color":"#..","path":[(i,j),...]}, "s2": {...} }
    active_selections = models.JSONField(default=dict)

    def mark_found(self, word: str):
        if word not in self.found_words:
            self.found_words.append(word)
            self.progress_pct = 100.0 * len(self.found_words) / max(1, len(self.words))
            if set(self.found_words) == set(self.words) and not self.ended_at:
                self.ended_at = timezone.now()
            self.save()


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
