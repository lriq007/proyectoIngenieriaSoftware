from django.urls import path
from . import views

urlpatterns = [
    path("", views.etapas_index, name="etapas_index"),  # /etapasJuego/
    path("etapa/1/", views.etapa1, name="etapa1"),
    path("etapa/2/", views.etapa2, name="etapa2"),
    path("etapa/3/", views.etapa3, name="etapa3"),
    path("etapa/4/", views.etapa4, name="etapa4"),
]