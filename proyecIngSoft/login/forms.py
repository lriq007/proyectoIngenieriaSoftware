from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import SeccionEstudiantes
from .permissions import PROFESOR_GROUP, is_admin
from etapasJuego.models import (
    Challenge,
    Evaluation,
    GameSession,
    Tablet,
    Topic,
)


class BaseStyledModelForm(forms.ModelForm):
    """
    Base con estilado ligero reutilizando clases usadas en el login.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-field".strip()


class SeccionEstudiantesForm(BaseStyledModelForm):
    class Meta:
        model = SeccionEstudiantes
        fields = ["nombre", "carrera_fk", "carrera", "anio_ingreso"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre de sección"}),
            "carrera_fk": forms.Select(attrs={"class": "form-field"}),
            "carrera": forms.TextInput(attrs={"placeholder": "Carrera"}),
            "anio_ingreso": forms.NumberInput(attrs={"min": 2000}),
        }


class GameSessionForm(BaseStyledModelForm):
    class Meta:
        model = GameSession
        fields = ["nombre", "codigo", "profesor", "seccion", "modo_asignacion", "etapa_actual"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre visible de la sesión"}),
            "codigo": forms.TextInput(attrs={"placeholder": "Código único"}),
            "modo_asignacion": forms.Select(attrs={"class": "form-field"}),
            "etapa_actual": forms.TextInput(attrs={"placeholder": "ETAPA1"}),
        }

    def __init__(self, *args, **kwargs):
        allowed_secciones = kwargs.pop("allowed_secciones", None)
        super().__init__(*args, **kwargs)
        User = get_user_model()

        prof_qs = User.objects.filter(groups__name=PROFESOR_GROUP).distinct()
        if self.request and not is_admin(self.request.user):
            prof_qs = prof_qs.filter(id=self.request.user.id)
            self.fields["profesor"].initial = self.request.user
        self.fields["profesor"].queryset = prof_qs

        if allowed_secciones is not None:
            self.fields["seccion"].queryset = allowed_secciones


class TopicForm(BaseStyledModelForm):
    class Meta:
        model = Topic
        fields = ["nombre", "slug", "descripcion", "imagen", "color_hex", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre del tema"}),
            "slug": forms.TextInput(attrs={"placeholder": "slug-unico"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "color_hex": forms.TextInput(attrs={"placeholder": "#ffee00"}),
        }


class ChallengeForm(BaseStyledModelForm):
    class Meta:
        model = Challenge
        fields = ["topic", "titulo", "descripcion", "activo", "orden", "video_file"]
        widgets = {
            "titulo": forms.TextInput(attrs={"placeholder": "Título del desafío"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "orden": forms.NumberInput(attrs={"min": 1}),
        }


class TabletForm(BaseStyledModelForm):
    class Meta:
        model = Tablet
        fields = ["codigo", "descripcion", "sesion"]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Código de tablet"}),
            "descripcion": forms.TextInput(attrs={"placeholder": "Notas u observaciones"}),
        }


class EvaluationForm(BaseStyledModelForm):
    class Meta:
        model = Evaluation
        fields = [
            "sesion",
            "evaluador",
            "evaluado",
            "puntaje_equipo",
            "puntaje_empatia",
            "puntaje_creatividad",
            "puntaje_comunicacion",
            "comentario",
        ]
        widgets = {
            "comentario": forms.Textarea(attrs={"rows": 2}),
            "puntaje_equipo": forms.NumberInput(attrs={"min": 0, "max": 100}),
            "puntaje_empatia": forms.NumberInput(attrs={"min": 0, "max": 100}),
            "puntaje_creatividad": forms.NumberInput(attrs={"min": 0, "max": 100}),
            "puntaje_comunicacion": forms.NumberInput(attrs={"min": 0, "max": 100}),
        }
