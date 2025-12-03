from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from etapasJuego.models import Challenge, Evaluation, GameSession, Tablet, Topic
from .forms import (
    ChallengeForm,
    EvaluationForm,
    GameSessionForm,
    SeccionEstudiantesForm,
    TabletForm,
    TopicForm,
)
from .models import SeccionEstudiantes
from .permissions import admin_required, is_admin, profesor_required


def _secciones_de_profesor(user):
    return SeccionEstudiantes.objects.filter(sesiones__profesor=user).distinct()


# ===============================
#   Panel ADMIN
# ===============================
@admin_required
def admin_dashboard(request):
    context = {
        "seccion_count": SeccionEstudiantes.objects.count(),
        "sesion_count": GameSession.objects.count(),
        "topic_count": Topic.objects.count(),
        "challenge_count": Challenge.objects.count(),
        "tablet_count": Tablet.objects.count(),
        "evaluation_count": Evaluation.objects.count(),
        "sesiones_recientes": GameSession.objects.select_related("seccion", "profesor").order_by("-id")[
            :5
        ],
    }
    return render(request, "login/admin/dashboard.html", context)


@admin_required
def admin_secciones(request):
    secciones = SeccionEstudiantes.objects.all().order_by("-fecha_creacion")
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
    sesiones = GameSession.objects.select_related("profesor", "seccion").order_by("-fecha", "-id")
    form = GameSessionForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Sesión guardada.")
        return redirect("adminpanel:sesiones")

    return render(
        request,
        "login/admin/sesiones.html",
        {"sesiones": sesiones, "form": form},
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
    topics = Topic.objects.all().order_by("nombre")
    form = TopicForm(request.POST or None, request=request, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tema guardado.")
        return redirect("adminpanel:topics")
    return render(
        request,
        "login/admin/topics.html",
        {"topics": topics, "form": form},
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
    challenges = Challenge.objects.select_related("topic").all().order_by("topic__nombre", "orden")
    form = ChallengeForm(request.POST or None, request=request, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Desafío guardado.")
        return redirect("adminpanel:challenges")
    return render(
        request,
        "login/admin/challenges.html",
        {"challenges": challenges, "form": form},
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
    tablets = Tablet.objects.select_related("sesion", "team").all().order_by("sesion__nombre", "codigo")
    form = TabletForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tablet guardada.")
        return redirect("adminpanel:tablets")
    return render(
        request,
        "login/admin/tablets.html",
        {"tablets": tablets, "form": form},
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
    evaluaciones = (
        Evaluation.objects.select_related("sesion", "evaluador", "evaluado")
        .all()
        .order_by("-sesion__fecha", "evaluador__codigo_grupo")
    )
    form = EvaluationForm(request.POST or None, request=request)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Evaluación guardada.")
        return redirect("adminpanel:evaluaciones")
    return render(
        request,
        "login/admin/evaluaciones.html",
        {"evaluaciones": evaluaciones, "form": form},
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


# ===============================
#   Panel PROFESOR
# ===============================
@profesor_required
def profesor_dashboard(request):
    sesiones = GameSession.objects.select_related("seccion").filter(profesor=request.user).order_by("-id")
    secciones = _secciones_de_profesor(request.user)
    context = {
        "sesiones": sesiones,
        "secciones": secciones,
        "sesion_count": sesiones.count(),
        "seccion_count": secciones.count(),
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
