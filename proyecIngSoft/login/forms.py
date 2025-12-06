from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.db.models import Q

from .models import Estudiante, SeccionEstudiantes
from .permissions import ADMIN_GROUP, PROFESOR_GROUP, ensure_default_groups, is_admin
from etapasJuego.models import (
    Challenge,
    Evaluation,
    GameSession,
    Tablet,
    Topic,
    Team,
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


class AdminUserForm(UserCreationForm):
    ROLE_CHOICES = (
        (ADMIN_GROUP, "Administrador"),
        (PROFESOR_GROUP, "Profesor"),
    )

    first_name = forms.CharField(max_length=150, required=False, label="Nombre")
    last_name = forms.CharField(max_length=150, required=False, label="Apellido")
    email = forms.EmailField(required=False, label="Email")
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol")

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Alinea estilos con el resto del panel
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-field".strip()
            if name == "username":
                field.widget.attrs.setdefault("placeholder", "usuario123")
            if name in ("password1", "password2"):
                field.widget.attrs.setdefault("placeholder", "••••••••")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")

        role = self.cleaned_data.get("role")
        ensure_default_groups()

        if commit:
            user.save()
            group = Group.objects.get(name=role)
            user.groups.add(group)
            if role == ADMIN_GROUP:
                # Staff permite acceso al panel admin y coincide con el helper is_admin.
                user.is_staff = True
                user.save()
        return user


class AdminUserEditForm(BaseStyledModelForm):
    ROLE_CHOICES = (
        (ADMIN_GROUP, "Administrador"),
        (PROFESOR_GROUP, "Profesor"),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Rol")

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ensure_default_groups()
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-field".strip()
            if name == "username":
                field.widget.attrs.setdefault("placeholder", "usuario123")
        user = self.instance
        if user and user.pk:
            if user.groups.filter(name=ADMIN_GROUP).exists():
                self.fields["role"].initial = ADMIN_GROUP
            elif user.groups.filter(name=PROFESOR_GROUP).exists():
                self.fields["role"].initial = PROFESOR_GROUP

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get("role")
        if commit:
            user.save()
            user.groups.clear()
            group = Group.objects.get(name=role)
            user.groups.add(group)
            if role == ADMIN_GROUP:
                user.is_staff = True
            else:
                user.is_staff = False
            user.save()
        return user


class EstudianteAdminForm(BaseStyledModelForm):
    class Meta:
        model = Estudiante
        fields = ["nombre_apellido", "carrera", "seccion", "team"]
        widgets = {
            "nombre_apellido": forms.TextInput(attrs={"placeholder": "Nombre completo"}),
            "carrera": forms.TextInput(attrs={"placeholder": "Carrera"}),
        }


class TeamAdminForm(BaseStyledModelForm):
    class Meta:
        model = Team
        fields = ["nombre", "codigo_grupo", "sesion", "tablet"]
        widgets = {
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre del equipo"}),
            "codigo_grupo": forms.TextInput(attrs={"placeholder": "Código/Grupo"}),
        }


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
