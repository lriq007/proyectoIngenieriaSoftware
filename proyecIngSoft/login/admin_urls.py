from django.urls import path

from . import panel_views as views

app_name = "adminpanel"

urlpatterns = [
    path("", views.admin_dashboard, name="dashboard"),
    path("secciones/", views.admin_secciones, name="secciones"),
    path("secciones/<int:pk>/editar/", views.admin_seccion_editar, name="seccion_editar"),
    path("secciones/<int:pk>/eliminar/", views.admin_seccion_eliminar, name="seccion_eliminar"),
    path("sesiones/", views.admin_sesiones, name="sesiones"),
    path("sesiones/<int:pk>/editar/", views.admin_sesion_editar, name="sesion_editar"),
    path("sesiones/<int:pk>/eliminar/", views.admin_sesion_eliminar, name="sesion_eliminar"),
    path("topics/", views.admin_topics, name="topics"),
    path("topics/<int:pk>/editar/", views.admin_topic_editar, name="topic_editar"),
    path("topics/<int:pk>/eliminar/", views.admin_topic_eliminar, name="topic_eliminar"),
    path("desafios/", views.admin_challenges, name="challenges"),
    path("desafios/<int:pk>/editar/", views.admin_challenge_editar, name="challenge_editar"),
    path("desafios/<int:pk>/eliminar/", views.admin_challenge_eliminar, name="challenge_eliminar"),
    path("tablets/", views.admin_tablets, name="tablets"),
    path("tablets/<int:pk>/editar/", views.admin_tablet_editar, name="tablet_editar"),
    path("tablets/<int:pk>/eliminar/", views.admin_tablet_eliminar, name="tablet_eliminar"),
    path("evaluaciones/", views.admin_evaluaciones, name="evaluaciones"),
    path("evaluaciones/<int:pk>/editar/", views.admin_evaluacion_editar, name="evaluacion_editar"),
    path("evaluaciones/<int:pk>/eliminar/", views.admin_evaluacion_eliminar, name="evaluacion_eliminar"),
    path("usuarios/", views.admin_usuarios, name="usuarios"),
    path("usuarios/<int:pk>/editar/", views.admin_usuario_editar, name="usuario_editar"),
    path("equipos/", views.admin_equipos, name="equipos"),
    path("equipos/<int:pk>/editar/", views.admin_equipo_editar, name="equipo_editar"),
    path("estudiantes/", views.admin_estudiantes, name="estudiantes"),
    path("estudiantes/<int:pk>/editar/", views.admin_estudiante_editar, name="estudiante_editar"),
]
