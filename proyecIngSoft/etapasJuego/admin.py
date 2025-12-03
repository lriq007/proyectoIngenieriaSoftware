from django.contrib import admin
from login.models import Estudiante
from .models import (
    TeamGameSession,
    Desafio,
    GameSession,
    Team,
    Topic,
    Challenge,
    Project,
    EmpathyMap,
    Pitch,
    Evaluation,
    Tablet,
)


@admin.register(Desafio)
class DesafioAdmin(admin.ModelAdmin):
    list_display = ("numero", "titulo", "personaje", "challenge", "activo")
    list_filter = ("challenge", "activo", "etapa")
    search_fields = ("titulo", "personaje", "challenge__titulo")
    fields = (
        "numero",
        "titulo",
        "challenge",
        "historia",
        "personaje",
        "imagen_personaje",
        "duracion_min",
        "etapa",
        "activo",
    )


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "slug")


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "topic", "activo", "orden")
    list_filter = ("topic", "activo")
    search_fields = ("titulo", "descripcion")
    fields = (
        "topic",
        "titulo",
        "descripcion",
        "video_file",
        "activo",
        "orden",
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("equipo", "desafio", "selected_desafio", "foto_prototipo")
    search_fields = ("equipo__nombre", "desafio__titulo", "selected_desafio__titulo")


@admin.register(EmpathyMap)
class EmpathyMapAdmin(admin.ModelAdmin):
    list_display = ("proyecto",)
    search_fields = ("proyecto__equipo__nombre", "proyecto__desafio__titulo")


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ("proyecto", "guion", "sugerencias_ia", "tiempo_preparacion_seg", "tiempo_presentacion_seg")
    readonly_fields = ("sugerencias_ia",)


@admin.register(Tablet)
class TabletAdmin(admin.ModelAdmin):
    list_display = ("codigo", "codigo_acceso", "descripcion", "sesion")
    readonly_fields = ("codigo_acceso",)


class EstudianteInline(admin.TabularInline):
    model = Estudiante
    extra = 0
    fields = ("nombre_apellido", "carrera", "fecha_registro")
    readonly_fields = ("fecha_registro",)


admin.site.register(TeamGameSession)
@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "profesor", "seccion", "modo_asignacion", "fecha")
    list_filter = ("modo_asignacion", "seccion")
    search_fields = ("nombre", "codigo")

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo_grupo", "count_estudiantes", "tablet")
    inlines = [EstudianteInline]
admin.site.register(Evaluation)
