from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'login'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('estudiante_ingresado/<int:estudiante_id>/', views.estudiante_ingresado, name='estudiante_ingresado'),
    path('home_estudiante/', views.home_estudiante, name='home_estudiante'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]