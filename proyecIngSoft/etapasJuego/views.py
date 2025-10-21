from django.shortcuts import render, redirect

def etapas_index(request):
    # /etapasJuego/ → redirige a la primera etapa
    return redirect("etapa1")

def etapa1(request):
    return render(request, "etapasJuego/etapa1.html")

def etapa2(request):
    return render(request, "etapasJuego/etapa2.html")

def etapa3(request):
    return render(request, "etapasJuego/etapa3.html")

def etapa4(request):
    return render(request, "etapasJuego/etapa4.html")