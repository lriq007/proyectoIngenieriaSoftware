from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render

from etapasJuego.models import Challenge, Evaluation, GameSession, Tablet, Team, Topic
from .forms import (
    AdminUserForm,
    AdminUserEditForm,
    ChallengeForm,
    EvaluationForm,
    GameSessionForm,
    SeccionEstudiantesForm,
    TabletForm,
    TopicForm,
    EstudianteAdminForm,
    TeamAdminForm,
)
from .models import Estudiante, SeccionEstudiantes
from .permissions import ADMIN_GROUP, PROFESOR_GROUP, admin_required, is_admin, profesor_required


def _secciones_de_profesor(user):
    return SeccionEstudiantes.objects.filter(sesiones__profesor=user).distinct()


# ===============================
#   Panel ADMIN
# ===============================
@admin_required
def admin_dashboard(request):
    User = get_user_model()
    profesor_count = User.objects.filter(groups__name=PROFESOR_GROUP).distinct().count()
    admin_count = User.objects.filter(groups__name=ADMIN_GROUP).distinct().count()
    equipos_count = Team.objects.count()
    estudiantes_count = Estudiante.objects.count()
    carrera_qs = (
        Estudiante.objects.values("carrera")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    carrera_total = sum(item["total"] for item in carrera_qs) or 1
    colors = ["#fbbf24", "#22d3ee", "#a855f7", "#fb7185", "#2dd4bf", "#f97316"]
    carrera_segments = []
    cursor = 0.0
    for idx, item in enumerate(carrera_qs):
        pct = (item["total"] / carrera_total) * 100.0
        start = cursor
        end = start + pct
        carrera_segments.append(
            {
                "label": item["carrera"] or "Sin carrera",
                "count": item["total"],
                "pct": pct,
                "color": colors[idx % len(colors)],
                "start": start,
                "end": end,
            }
        )
        cursor = end
    carrera_gradient = ", ".join(
        f"{seg['color']} {seg['start']:.2f}% {seg['end']:.2f}%"
        for seg in carrera_segments
    ) or "#fbbf24 0% 100%"
    top_equipos = (
        Team.objects.select_related("sesion", "sesion__profesor")
        .order_by("-tokens_totales", "-id")[:5]
    )
    context = {
        "seccion_count": SeccionEstudiantes.objects.count(),
        "sesion_count": GameSession.objects.count(),
        "topic_count": Topic.objects.count(),
        "challenge_count": Challenge.objects.count(),
        "tablet_count": Tablet.objects.count(),
        "evaluation_count": Evaluation.objects.count(),
        "profesor_count": profesor_count,
        "equipos_count": equipos_count,
        "estudiantes_count": estudiantes_count,
        "admin_count": admin_count,
        "carrera_segments": carrera_segments,
        "carrera_gradient": carrera_gradient,
        "top_equipos": top_equipos,
        "sesiones_recientes": GameSession.objects.select_related("seccion", "profesor").order_by("-id")[
            :5
        ],
    }
    return render(request, "login/admin/dashboard.html", context)


@admin_required
def admin_secciones(request):
    q = request.GET.get("q", "").strip()
    secciones = SeccionEstudiantes.objects.all()
    if q:
        secciones = secciones.filter(
            Q(nombre__icontains=q)
            | Q(carrera__icontains=q)
            | Q(carrera_fk__nombre__icontains=q)
        )
    secciones = secciones.order_by("-fecha_creacion")
    if request.method == "POST":
        form = SeccionEstudiantesForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sección creada/actualizada correctamente.")
            return redirect("adminpanel:secciones")
    else:
        form = SeccionEstudiantesForm()

    return render(
        request,
        "login/admin/secciones.html",
        {
            "form": form,
            "secciones": secciones,
            "q": q,
        },
    )


@admin_required
def admin_seccion_editar(request, pk):
    seccion = get_object_or_404(SeccionEstudiantes, pk=pk)
    form = SeccionEstudiantesForm(request.POST or None, instance=seccion)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sección actualizada.")
        return redirect("adminpanel:secciones")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar sección", "back_url": "adminpanel:secciones"},
    )


@admin_required
def admin_seccion_eliminar(request, pk):
    seccion = get_object_or_404(SeccionEstudiantes, pk=pk)
    if request.method == "POST":
        seccion.delete()
        messages.success(request, "Sección eliminada.")
        return redirect("adminpanel:secciones")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": seccion, "back_url": "adminpanel:secciones", "title": "Eliminar sección"},
    )


@admin_required
def admin_sesiones(request):
    q = request.GET.get("q", "").strip()
    sesiones = GameSession.objects.select_related("profesor", "seccion")
    if q:
        sesiones = sesiones.filter(
            Q(nombre__icontains=q)
            | Q(codigo__icontains=q)
            | Q(profesor__username__icontains=q)
            | Q(profesor__first_name__icontains=q)
            | Q(profesor__last_name__icontains=q)
            | Q(seccion__nombre__icontains=q)
        )
    sesiones = sesiones.order_by("-fecha", "-id")
    form = GameSessionForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesión guardada.")
        return redirect("adminpanel:sesiones")

    return render(
        request,
        "login/admin/sesiones.html",
        {"sesiones": sesiones, "form": form, "q": q},
    )


@admin_required
def admin_sesion_editar(request, pk):
    sesion = get_object_or_404(GameSession, pk=pk)
    form = GameSessionForm(request.POST or None, instance=sesion, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesión actualizada.")
        return redirect("adminpanel:sesiones")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar sesión", "back_url": "adminpanel:sesiones"},
    )


@admin_required
def admin_sesion_eliminar(request, pk):
    sesion = get_object_or_404(GameSession, pk=pk)
    if request.method == "POST":
        sesion.delete()
        messages.success(request, "Sesión eliminada.")
        return redirect("adminpanel:sesiones")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": sesion, "back_url": "adminpanel:sesiones", "title": "Eliminar sesión"},
    )


@admin_required
def admin_topics(request):
    q = request.GET.get("q", "").strip()
    topics = Topic.objects.all()
    if q:
        topics = topics.filter(Q(nombre__icontains=q) | Q(slug__icontains=q))
    topics = topics.order_by("nombre")
    form = TopicForm(request.POST or None, request=request, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tema guardado.")
        return redirect("adminpanel:topics")
    return render(
        request,
        "login/admin/topics.html",
        {"topics": topics, "form": form, "q": q},
    )


@admin_required
def admin_topic_editar(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    form = TopicForm(request.POST or None, request=request, instance=topic, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tema actualizado.")
        return redirect("adminpanel:topics")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar tema", "back_url": "adminpanel:topics"},
    )


@admin_required
def admin_topic_eliminar(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method == "POST":
        topic.delete()
        messages.success(request, "Tema eliminado.")
        return redirect("adminpanel:topics")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": topic, "back_url": "adminpanel:topics", "title": "Eliminar tema"},
    )


@admin_required
def admin_challenges(request):
    q = request.GET.get("q", "").strip()
    challenges = Challenge.objects.select_related("topic").all()
    if q:
        challenges = challenges.filter(
            Q(titulo__icontains=q) | Q(topic__nombre__icontains=q)
        )
    challenges = challenges.order_by("topic__nombre", "orden")
    form = ChallengeForm(request.POST or None, request=request, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Desafío guardado.")
        return redirect("adminpanel:challenges")
    return render(
        request,
        "login/admin/challenges.html",
        {"challenges": challenges, "form": form, "q": q},
    )


@admin_required
def admin_challenge_editar(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    form = ChallengeForm(request.POST or None, request=request, instance=challenge, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Desafío actualizado.")
        return redirect("adminpanel:challenges")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar desafío", "back_url": "adminpanel:challenges"},
    )


@admin_required
def admin_challenge_eliminar(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if request.method == "POST":
        challenge.delete()
        messages.success(request, "Desafío eliminado.")
        return redirect("adminpanel:challenges")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": challenge, "back_url": "adminpanel:challenges", "title": "Eliminar desafío"},
    )


@admin_required
def admin_tablets(request):
    q = request.GET.get("q", "").strip()
    tablets = Tablet.objects.select_related("sesion", "team").all()
    if q:
        tablets = tablets.filter(
            Q(codigo__icontains=q)
            | Q(codigo_acceso__icontains=q)
            | Q(sesion__nombre__icontains=q)
        )
    tablets = tablets.order_by("sesion__nombre", "codigo")
    form = TabletForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tablet guardada.")
        return redirect("adminpanel:tablets")
    return render(
        request,
        "login/admin/tablets.html",
        {"tablets": tablets, "form": form, "q": q},
    )


@admin_required
def admin_tablet_editar(request, pk):
    tablet = get_object_or_404(Tablet, pk=pk)
    form = TabletForm(request.POST or None, request=request, instance=tablet)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tablet actualizada.")
        return redirect("adminpanel:tablets")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar tablet", "back_url": "adminpanel:tablets"},
    )


@admin_required
def admin_tablet_eliminar(request, pk):
    tablet = get_object_or_404(Tablet, pk=pk)
    if request.method == "POST":
        tablet.delete()
        messages.success(request, "Tablet eliminada.")
        return redirect("adminpanel:tablets")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": tablet, "back_url": "adminpanel:tablets", "title": "Eliminar tablet"},
    )


@admin_required
def admin_evaluaciones(request):
    q = request.GET.get("q", "").strip()
    evaluaciones = Evaluation.objects.select_related("sesion", "evaluador", "evaluado").all()
    if q:
        evaluaciones = evaluaciones.filter(
            Q(sesion__nombre__icontains=q)
            | Q(sesion__codigo__icontains=q)
            | Q(evaluador__nombre__icontains=q)
            | Q(evaluador__codigo_grupo__icontains=q)
            | Q(evaluado__nombre__icontains=q)
            | Q(evaluado__codigo_grupo__icontains=q)
        )
    evaluaciones = evaluaciones.order_by("-sesion__fecha", "evaluador__codigo_grupo")
    form = EvaluationForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Evaluación guardada.")
        return redirect("adminpanel:evaluaciones")
    return render(
        request,
        "login/admin/evaluaciones.html",
        {"evaluaciones": evaluaciones, "form": form, "q": q},
    )


@admin_required
def admin_evaluacion_editar(request, pk):
    evaluacion = get_object_or_404(Evaluation, pk=pk)
    form = EvaluationForm(request.POST or None, request=request, instance=evaluacion)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Evaluación actualizada.")
        return redirect("adminpanel:evaluaciones")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar evaluación", "back_url": "adminpanel:evaluaciones"},
    )


@admin_required
def admin_evaluacion_eliminar(request, pk):
    evaluacion = get_object_or_404(Evaluation, pk=pk)
    if request.method == "POST":
        evaluacion.delete()
        messages.success(request, "Evaluación eliminada.")
        return redirect("adminpanel:evaluaciones")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": evaluacion, "back_url": "adminpanel:evaluaciones", "title": "Eliminar evaluación"},
    )


@admin_required
def admin_usuarios(request):
    User = get_user_model()
    usuarios_admin = User.objects.filter(groups__name=ADMIN_GROUP).distinct()
    usuarios_prof = User.objects.filter(groups__name=PROFESOR_GROUP).distinct()
    form = AdminUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuario creado y rol asignado.")
        return redirect("adminpanel:usuarios")
    return render(
        request,
        "login/admin/usuarios.html",
        {
            "form": form,
            "usuarios_admin": usuarios_admin,
            "usuarios_prof": usuarios_prof,
        },
    )


@admin_required
def admin_usuario_editar(request, pk):
    User = get_user_model()
    usuario = get_object_or_404(User, pk=pk, groups__name=PROFESOR_GROUP)
    form = AdminUserEditForm(request.POST or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil de profesor actualizado.")
        return redirect("adminpanel:usuarios")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar profesor", "back_url": "adminpanel:usuarios"},
    )


@admin_required
def admin_equipos(request):
    q = request.GET.get("q", "").strip()
    equipos = (
        Team.objects.select_related("sesion", "sesion__profesor", "tablet")
        .prefetch_related("estudiantes")
        .order_by("-tokens_totales", "sesion__nombre", "codigo_grupo")
    )
    if q:
        equipos = equipos.filter(
            Q(nombre__icontains=q)
            | Q(codigo_grupo__icontains=q)
            | Q(sesion__nombre__icontains=q)
            | Q(tablet__codigo__icontains=q)
        )
    form = TeamAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Equipo creado correctamente.")
        return redirect("adminpanel:equipos")
    return render(
        request,
        "login/admin/equipos.html",
        {"equipos": equipos, "form": form, "q": q},
    )


@admin_required
def admin_estudiantes(request):
    q = request.GET.get("q", "").strip()
    estudiantes = (
        Estudiante.objects.select_related("seccion", "team", "team__sesion")
        .order_by("nombre_apellido")
    )
    if q:
        estudiantes = estudiantes.filter(
            Q(nombre_apellido__icontains=q)
            | Q(carrera__icontains=q)
            | Q(seccion__nombre__icontains=q)
            | Q(team__nombre__icontains=q)
        )
    form = EstudianteAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Estudiante creado correctamente.")
        return redirect("adminpanel:estudiantes")
    return render(
        request,
        "login/admin/estudiantes.html",
        {"estudiantes": estudiantes, "form": form},
    )


@admin_required
def admin_equipo_editar(request, pk):
    equipo = get_object_or_404(Team, pk=pk)
    form = TeamAdminForm(request.POST or None, instance=equipo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Equipo actualizado.")
        return redirect("adminpanel:equipos")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar equipo", "back_url": "adminpanel:equipos"},
    )


@admin_required
def admin_estudiante_editar(request, pk):
    estudiante = get_object_or_404(Estudiante, pk=pk)
    form = EstudianteAdminForm(request.POST or None, instance=estudiante)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Estudiante actualizado.")
        return redirect("adminpanel:estudiantes")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar estudiante", "back_url": "adminpanel:estudiantes"},
    )


# ===============================
#   Panel PROFESOR
# ===============================
@profesor_required
def profesor_dashboard(request):
    q = request.GET.get("q", "").strip()
    sesiones = GameSession.objects.select_related("seccion").filter(profesor=request.user).order_by("-id")
    secciones = _secciones_de_profesor(request.user)
    equipos = Team.objects.select_related("sesion").filter(sesion__profesor=request.user)
    estudiantes_count = Estudiante.objects.filter(team__sesion__profesor=request.user).count()
    if q:
        equipos = equipos.filter(Q(nombre__icontains=q) | Q(sesion__nombre__icontains=q))
    top_equipos = equipos.order_by("-tokens_totales", "-id")[:5]
    context = {
        "sesiones": sesiones,
        "secciones": secciones,
        "sesion_count": sesiones.count(),
        "seccion_count": secciones.count(),
        "equipos_count": equipos.count(),
        "estudiantes_count": estudiantes_count,
        "top_equipos": top_equipos,
        "ranking": equipos.order_by("-tokens_totales", "nombre")[:10],
        "q": q,
    }
    return render(request, "login/profesor/dashboard.html", context)


@profesor_required
def profesor_sesiones(request):
    sesiones = GameSession.objects.select_related("seccion").filter(profesor=request.user).order_by("-id")
    secciones_disponibles = SeccionEstudiantes.objects.filter(
        Q(sesiones__profesor=request.user) | Q(sesiones__isnull=True)
    ).distinct()
    form = GameSessionForm(
        request.POST or None,
        request=request,
        allowed_secciones=secciones_disponibles,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesión guardada.")
        return redirect("profesorpanel:sesiones")
    return render(
        request,
        "login/profesor/sesiones.html",
        {"sesiones": sesiones, "form": form},
    )


@profesor_required
def profesor_sesion_editar(request, pk):
    sesion = get_object_or_404(GameSession, pk=pk, profesor=request.user)
    secciones_disponibles = SeccionEstudiantes.objects.filter(
        Q(sesiones__profesor=request.user) | Q(sesiones__isnull=True)
    ).distinct()
    form = GameSessionForm(
        request.POST or None,
        request=request,
        instance=sesion,
        allowed_secciones=secciones_disponibles,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesión actualizada.")
        return redirect("profesorpanel:sesiones")
    return render(
        request,
        "login/admin/form.html",
        {"form": form, "title": "Editar sesión", "back_url": "profesorpanel:sesiones"},
    )


@profesor_required
def profesor_sesion_eliminar(request, pk):
    sesion = get_object_or_404(GameSession, pk=pk, profesor=request.user)
    if request.method == "POST":
        sesion.delete()
        messages.success(request, "Sesión eliminada.")
        return redirect("profesorpanel:sesiones")
    return render(
        request,
        "login/admin/confirm_delete.html",
        {"object": sesion, "back_url": "profesorpanel:sesiones", "title": "Eliminar sesión"},
    )


@profesor_required
def profesor_alumnos(request):
    sesiones = GameSession.objects.filter(profesor=request.user)
    equipos = Team.objects.filter(sesion__in=sesiones)
    secciones = SeccionEstudiantes.objects.filter(sesiones__in=sesiones).distinct()
    estudiantes = Estudiante.objects.select_related("seccion", "team", "team__sesion").filter(
        Q(team__sesion__in=sesiones) | Q(seccion__in=secciones)
    ).order_by("nombre_apellido")

    form = EstudianteAdminForm(request.POST or None)
    form.fields["team"].queryset = equipos
    form.fields["seccion"].queryset = secciones

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Estudiante creado correctamente.")
        return redirect("profesorpanel:alumnos")

    return render(
        request,
        "login/profesor/alumnos.html",
        {"estudiantes": estudiantes, "form": form},
    )


@profesor_required
def profesor_equipos(request):
    sesiones = GameSession.objects.filter(profesor=request.user)
    equipos = (
        Team.objects.select_related("sesion", "tablet")
        .prefetch_related("estudiantes")
        .filter(sesion__in=sesiones)
        .order_by("sesion__nombre", "codigo_grupo")
    )

    form = TeamAdminForm(request.POST or None)
    form.fields["sesion"].queryset = sesiones
    form.fields["tablet"].queryset = form.fields["tablet"].queryset.filter(sesion__in=sesiones)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Equipo creado correctamente.")
        return redirect("profesorpanel:equipos")

    return render(
        request,
        "login/profesor/equipos.html",
        {"equipos": equipos, "form": form},
    )


@profesor_required
def profesor_secciones(request):
    sesiones = GameSession.objects.filter(profesor=request.user)
    secciones = SeccionEstudiantes.objects.filter(sesiones__in=sesiones).distinct().order_by("-fecha_creacion")

    form = SeccionEstudiantesForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sección creada/actualizada correctamente.")
        return redirect("profesorpanel:secciones")

    return render(
        request,
        "login/profesor/secciones.html",
        {"secciones": secciones, "form": form},
    )
