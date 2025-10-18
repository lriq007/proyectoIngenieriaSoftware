from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

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
                return redirect('estudiante_dashboard')
            else:
                messages.error(request, "Por favor completa todos los campos para estudiante")
        else:
            messages.error(request, "Por favor selecciona un tipo de usuario válido")
    
    form = AuthenticationForm()
    return render(request, 'login/login.html', {'form': form})