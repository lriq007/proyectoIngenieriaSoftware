from django.contrib import admin
from .models import Carrera, Estudiante, SeccionEstudiantes


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("nombre_apellido", "carrera", "team", "seccion", "fecha_registro")
    list_filter = ("team", "carrera")


class EstudianteInline(admin.TabularInline):
    model = Estudiante
    extra = 0
    fields = ("nombre_apellido", "carrera", "team", "fecha_registro")
    readonly_fields = ("fecha_registro",)


@admin.register(SeccionEstudiantes)
class SeccionEstudiantesAdmin(admin.ModelAdmin):
    list_display = ("nombre", "carrera_fk", "carrera", "anio_ingreso", "fecha_creacion")
    search_fields = ("nombre", "carrera", "carrera_fk__nombre")
    ordering = ("-fecha_creacion",)
    inlines = [EstudianteInline]


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nombre_facultad")
    search_fields = ("nombre", "nombre_facultad")
