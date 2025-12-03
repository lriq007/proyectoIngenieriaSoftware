from django.db import models
from etapasJuego.models import Team


class SeccionEstudiantes(models.Model):
    nombre = models.CharField(max_length=100)
    # Campo legado de texto. Se mantiene por compatibilidad; el valor canónico debe ir en carrera_fk.
    carrera = models.CharField(max_length=100, blank=True)
    carrera_fk = models.ForeignKey(
        "Carrera",
        related_name="secciones",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Nueva referencia normalizada a Carrera; preferir este campo sobre el texto legado.",
    )
    anio_ingreso = models.PositiveIntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Estudiante(models.Model):
    nombre_apellido = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    seccion = models.ForeignKey(
        "SeccionEstudiantes",
        related_name="estudiantes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="estudiantes",
        blank=True,
        null=True,
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_apellido


class Carrera(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    nombre_facultad = models.CharField(
        max_length=200,
        blank=True,
        help_text="Facultad a la que pertenece esta carrera.",
    )

    class Meta:
        ordering = ("nombre",)

    def __str__(self):
        return self.nombre
