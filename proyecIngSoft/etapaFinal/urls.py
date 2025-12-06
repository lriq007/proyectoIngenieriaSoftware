from django.urls import path
from . import views

app_name = "etapaFinal"

urlpatterns = [
    path("", views.coevaluacion_home, name="home"),
    path("save/", views.save_coevaluacion, name="save_coevaluacion"),
    path("final/", views.final_resultados, name="final_resultados"),
    path("foto-grupal/", views.upload_foto_grupal, name="upload_foto_grupal"),
]
