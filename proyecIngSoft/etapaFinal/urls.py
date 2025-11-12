from django.urls import path
from . import views

app_name = "etapaFinal"

urlpatterns = [
    path("", views.coevaluacion_home, name="home"),
]
