from django.urls import path
from . import views

urlpatterns = [
    path("", views.etapas_index, name="etapas_index"),  # /etapasJuego/
    path("etapa/1/", views.etapa1, name="etapa1"),
    path("api/init/", views.api_init, name="api_init"),
    path("api/select/start/", views.api_select_start, name="api_select_start"),
    path("api/select/extend/", views.api_select_extend, name="api_select_extend"),
    path("api/select/commit/", views.api_select_commit, name="api_select_commit"),
    path("api/reset/", views.api_reset, name="api_reset"),
    
    path("etapa/2/", views.etapa2, name="etapa2"),
    path("etapa/3/", views.etapa3, name="etapa3"),
    path("etapa/4/", views.etapa4, name="etapa4"),
]