from django.urls import path
from . import views

urlpatterns = [
    path("", views.etapas_index, name="etapas_index"),  # /etapasJuego/
    path("tablet/seleccion-modalidad/", views.seleccion_modalidad, name="seleccion_modalidad"),
    path("tablet/rompehielo/", views.rompehielo, name="rompehielo"),
    path("etapa/0/", views.etapa2_tema),
    path("etapa2/tema/", views.etapa2_tema, name="etapa2_tema"),
    path("etapa/1/", views.etapa1, name="etapa1"),
    path("api/init/", views.api_init, name="api_init"),
    path("api/select/start/", views.api_select_start, name="api_select_start"),
    path("api/select/extend/", views.api_select_extend, name="api_select_extend"),
    path("api/select/commit/", views.api_select_commit, name="api_select_commit"),
    path("api/reset/", views.api_reset, name="api_reset"),
    
    path("etapa/2/", views.etapa2, name="etapa2"),
    path("etapa/2/seleccionar/", views.etapa2_seleccionar, name="etapa2_select"),
    path("etapa/2/seleccion/", views.etapa2_1, name="etapa2_1"),
    path("etapa/2/mapa/guardar/", views.etapa2_guardar_mapa, name="etapa2_guardar_mapa"),
    path("etapa/3/", views.etapa3, name="etapa3"),
    path("etapa/3/guardar-foto/", views.etapa3_guardar_foto, name="etapa3_guardar_foto"),
    path("etapa/4/", views.etapa4, name="etapa4"),
    path("etapa/4/guardar-pitch/", views.etapa4_guardar_pitch, name="etapa4_guardar_pitch"),
    path("inicio_juego/", views.inicio_juego, name="inicio_juego"),
]
