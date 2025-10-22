from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .models import Estudiante
import random

def estudiante_ingresado(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    compañeros = Estudiante.objects.filter(grupo=estudiante.grupo).exclude(id=estudiante.id)
    return render(request, 'login/estudiante_ingresado.html', {
        'estudiante': estudiante,
        'compañeros': compañeros
    })

def home_estudiante(request):
    return render(request, 'login/home_estudiante.html')

def login_view(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')

        if user_type in ['profesor', 'administrador']:
            form = AuthenticationForm(request, data=request.POST)
            
            if form.is_valid():
                email = form.cleaned_data.get('email')
                password = form.cleaned_data.get('password')
                user = authenticate(email=email, password=password)

                if user is not None:
                    login(request, user)
                    messages.success(request, 'Bienvenido')
                    if user_type == 'profesor':
                        return redirect('profesor_dashboard')
                    elif user_type == 'administrador':
                        return redirect('admin_dashboard')
                else:
                    messages.error(request, "Correo o contraseña inválidos")
            else:
                messages.error(request, "Correo o contraseña inválidos")

        elif user_type == 'estudiante':
            nombre_apellido = request.POST.get('nombre_apellido')
            carrera = request.POST.get('carrera')
            
            if nombre_apellido and carrera:
                grupos = ['A', 'B', 'C', 'D']
                grupos_disponibles = []

                for grupo in grupos:
                    cantidad_en_grupo = Estudiante.objects.filter(grupo=grupo).count()
                    if cantidad_en_grupo < 8:
                        grupos_disponibles.append(grupo)

                if grupos_disponibles:
                    grupo_asignado = random.choice(grupos_disponibles)
                else:
                    grupo_asignado = random.choice(grupos)
                
                estudiante = Estudiante.objects.create(
                    nombre_apellido=nombre_apellido,
                    carrera=carrera,
                    grupo=grupo_asignado)
                return redirect('login:estudiante_ingresado', estudiante_id=estudiante.id)
            else:
                messages.error(request, "Por favor completa todos los campos para estudiante")
        else:
            messages.error(request, "Por favor selecciona un tipo de usuario válido")
    
    form = AuthenticationForm()
    return render(request, 'login/login.html', {'form': form})