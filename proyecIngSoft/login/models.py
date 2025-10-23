from django.db import models

class Estudiante(models.Model):
    nombre_apellido = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    grupo = models.CharField(max_length=50, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_apellido