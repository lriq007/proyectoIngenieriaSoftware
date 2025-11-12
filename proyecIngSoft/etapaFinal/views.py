from django.shortcuts import render

# Create your views here.

def coevaluacion_home(request):
    # Por ahora solo renderiza la plantilla base
    return render(request, "etapaFinal/index.html")