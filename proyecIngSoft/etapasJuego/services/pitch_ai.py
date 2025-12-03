from typing import Optional

from django.conf import settings
from openai import OpenAI

from etapasJuego.models import Pitch, Topic, Challenge, Desafio, EmpathyMap


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _safe(val):
    return val or ""


def generar_sugerencias_pitch(
    topic: Optional[Topic],
    challenge: Optional[Challenge],
    desafio: Optional[Desafio],
    mapa: Optional[EmpathyMap],
) -> str:
    """
    Genera tres puntos de apoyo para el pitch usando OpenAI, a partir del contexto
    de tema, desafío, personaje y mapa de empatía del proyecto.
    """
    tema_nombre = _safe(getattr(topic, "nombre", ""))
    tema_desc = _safe(getattr(topic, "descripcion", ""))

    challenge_titulo = _safe(getattr(challenge, "titulo", ""))
    challenge_desc = _safe(getattr(challenge, "descripcion", ""))

    personaje = _safe(getattr(desafio, "personaje", ""))
    historia = _safe(getattr(desafio, "historia", ""))

    gustos = _safe(getattr(mapa, "gustos", ""))
    problemas = _safe(getattr(mapa, "problemas", ""))
    miedos = _safe(getattr(mapa, "miedos", ""))
    contexto = _safe(getattr(mapa, "contexto", ""))
    hobbies = _safe(getattr(mapa, "hobbies", ""))

    prompt = f"""
Eres un asistente experto en pitch y storytelling para estudiantes hispanohablantes. Ayuda a sintetizar un pitch breve basado en el mapa de empatía y el contexto del desafío.

Contexto del tema:
- Nombre del tema: {tema_nombre}
- Descripción del tema: {tema_desc}

Contexto del desafío:
- Título del desafío: {challenge_titulo}
- Descripción del desafío: {challenge_desc}

Personaje/usuario:
- Nombre/personaje: {personaje}
- Historia / descripción breve: {historia}

Mapa de empatía (insumos clave):
- Gustos: {gustos}
- Problemas: {problemas}
- Miedos: {miedos}
- Contexto: {contexto}
- Hobbies: {hobbies}

Con esta información, devuelve exactamente 3 ideas de apoyo al pitch en este formato, una por línea y sin texto adicional:
Punto 1: ...
Punto 2: ...
Punto 3: ...
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente experto en pitch y storytelling. Responde en español claro para estudiantes y entrega solo los puntos solicitados.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=350,
    )

    texto = (response.choices[0].message.content or "").strip()

    # Limpiar etiquetas "Punto 1:", "Punto 2:", "Punto 3:"
    import re

    texto = re.sub(r"^Punto\s*\d+\s*:\s*", "", texto, flags=re.MULTILINE)

    return texto


def evaluar_pitch_con_ia(texto: str) -> Optional[int]:
    """
    Evalúa el texto de un pitch y retorna un puntaje entero 1–5 basado en calidad de redacción.
    Devuelve None si el texto es muy corto o no se puede obtener un puntaje válido.
    """
    if not texto or len(texto.strip()) < 30:
        return None

    prompt = (
        "Eres un experto en escritura, gramática y narrativa de pitch de emprendimiento, "
        "con estándares MIT, Oxford e Imperial College. Evalúa SOLO la estructura, claridad, "
        "coherencia y calidad de redacción del siguiente pitch. Devuelve SOLO un número entero "
        "del 1 al 5, sin ningún otro texto, palabra, explicación ni símbolo."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": texto},
        ],
        temperature=0,
        max_tokens=5,
    )

    raw = (response.choices[0].message.content or "").strip()
    try:
        value = int(raw)
    except (ValueError, TypeError):
        return None

    return value if 1 <= value <= 5 else None


def actualizar_score_ai(pitch: Pitch) -> None:
    """
    Evalúa pitch.guion con IA y actualiza pitch.score_ai si se obtiene un valor válido.
    """
    if not pitch.guion:
        pitch.score_ai = None
        return

    score = evaluar_pitch_con_ia(pitch.guion)
    if score is not None:
        pitch.score_ai = score
        pitch.save(update_fields=["score_ai"])
