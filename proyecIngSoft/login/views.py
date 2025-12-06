from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .permissions import (
    ensure_default_groups,
    is_admin,
    is_profesor,
)
from .models import Estudiante, SeccionEstudiantes
from etapasJuego.models import GameSession, Team, Tablet
import random

def estudiante_ingresado(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)
    team = estudiante.team
    if team is not None:
        compañeros = Estudiante.objects.filter(team=team).exclude(id=estudiante.id)
        num_integrantes = team.count_estudiantes()
        min_integrantes_para_empezar = 2
        en_espera = num_integrantes < min_integrantes_para_empezar
        tablet = getattr(team, "tablet", None)
    else:
        compañeros = Estudiante.objects.none()
        num_integrantes = 0
        min_integrantes_para_empezar = 2
        en_espera = True
        tablet = None

    context = {
        "estudiante": estudiante,
        "team": team,
        "companeros": compañeros,
        "tablet": tablet,
        "num_integrantes": num_integrantes,
        "min_integrantes_para_empezar": min_integrantes_para_empezar,
        "en_espera": en_espera,
    }
    return render(request, 'login/estudiante_ingresado.html', context)

def home_estudiante(request):
    return render(request, 'login/home_estudiante.html')

def mission_launch(request):
    return render(request, 'login/mission_launch.html')

def logout_view(request):
    logout(request)
    return redirect('login:login')

def login_view(request):
    ensure_default_groups()
    if request.method == 'POST':
        user_type = request.POST.get('user_type')

        if user_type in ['profesor', 'administrador']:
            form_data = {
                "username": request.POST.get("email"),
                "password": request.POST.get("password"),
            }
            form = AuthenticationForm(request, data=form_data)

            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)

                if user is not None:
                    if user_type == 'profesor' and not is_profesor(user):
                        messages.error(request, "Tu usuario no tiene rol de profesor.")
                        return redirect('login:login')
                    if user_type == 'administrador' and not is_admin(user):
                        messages.error(request, "Tu usuario no tiene permisos de administrador.")
                        return redirect('login:login')
                    login(request, user)
                    messages.success(request, 'Bienvenido')
                    if user_type == 'profesor':
                        return redirect('profesorpanel:dashboard')
                    elif user_type == 'administrador':
                        return redirect('adminpanel:dashboard')
                else:
                    messages.error(request, "Correo o contraseña inválidos")
            else:
                messages.error(request, "Correo o contraseña inválidos")

        elif user_type == 'estudiante':
            nombre_apellido = request.POST.get('nombre_apellido')
            carrera = request.POST.get('carrera')
            seccion_id = request.POST.get('seccion_id')
            
            if nombre_apellido and carrera and seccion_id:
                seccion = SeccionEstudiantes.objects.filter(id=seccion_id).first()
                if not seccion:
                    messages.error(request, "Selecciona una sección válida.")
                    return redirect('login:login')

                game_session = GameSession.objects.filter(
                    seccion=seccion
                ).order_by("-fecha", "-id").first()
                if not game_session:
                    messages.error(request, "Todavía no hay una sesión de juego activa para tu sección. Por favor, contacta a tu profesor.")
                    return redirect('login:login')

                if game_session.modo_asignacion == "LOGIN_RANDOM":
                    teams = list(Team.objects.filter(sesion=game_session).order_by("id"))
                    assigned_team = None
                    for team in teams:
                        if team.has_cupo():
                            assigned_team = team
                            break

                    if assigned_team is None:
                        existing_codes = set(Team.objects.filter(sesion=game_session).values_list("codigo_grupo", flat=True))
                        new_code = None
                        for i in range(26):
                            code = chr(ord('A') + i)
                            if code not in existing_codes:
                                new_code = code
                                break
                        if new_code is None:
                            new_code = str(len(existing_codes) + 1)
                        assigned_team = Team.objects.create(
                            nombre=f"Equipo {new_code}",
                            sesion=game_session,
                            codigo_grupo=new_code,
                        )
                        tablet = Tablet.objects.filter(
                            sesion=game_session,
                            team__isnull=True
                        ).first()
                        if tablet is not None:
                            assigned_team.tablet = tablet
                            assigned_team.save(update_fields=["tablet"])

                    estudiante = Estudiante.objects.create(
                        nombre_apellido=nombre_apellido,
                        carrera=carrera,
                        seccion=seccion,
                        team=assigned_team)
                    return redirect('login:estudiante_ingresado', estudiante_id=estudiante.id)
                else:
                    if not game_session.seccion:
                        messages.error(request, "La sesión no tiene sección asignada. Consulta a tu profesor.")
                        return redirect('login:login')

                    estudiante = Estudiante.objects.filter(
                        nombre_apellido=nombre_apellido,
                        carrera=carrera,
                        seccion=seccion,
                    ).first()

                    if not estudiante:
                        messages.error(request, "No estás registrado en la sección de esta sesión. Consulta a tu profesor.")
                        return redirect('login:login')

                    if estudiante.team is None:
                        messages.error(request, "Tu profesor aún no te ha asignado a un grupo.")
                        return redirect('login:login')

                    return redirect('login:estudiante_ingresado', estudiante_id=estudiante.id)
            else:
                messages.error(request, "Por favor completa todos los campos para estudiante, incluida la sección")
            
        elif user_type == 'tableta':
            pin = request.POST.get('pin')
            tablet = Tablet.objects.filter(codigo_acceso=pin).first()
            if tablet is None:
                messages.error(request, "Código de acceso inválido")
                return redirect('login:login')
            else:
                request.session["tablet_id"] = tablet.id
                # Si la tablet ya tiene team asociado, guardamos la referencia
                from etapasJuego.models import Team  # import local para evitar ciclos
                existing_team = Team.objects.filter(tablet=tablet).first()
                if existing_team:
                    request.session["team_id"] = existing_team.id
                request.session.modified = True
                messages.success(request, f'Acceso concedido a tableta con código: {pin}')
                return redirect('login:home_estudiante')

        else:
            messages.error(request, "Por favor selecciona un tipo de usuario válido")

    form = AuthenticationForm()
    secciones = SeccionEstudiantes.objects.all()
    return render(request, 'login/login.html', {'form': form, 'secciones': secciones})
