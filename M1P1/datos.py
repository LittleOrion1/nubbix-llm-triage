# datos.py
# Dataset de consultas y system prompt de Nubbix.
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "consultas.json"


ETIQUETAS_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "etiquetas.json"
)


#este era el predeterminado. En 
SYSTEM_PROMPT = (
 "Eres el asistente de primera respuesta de centro de atención Nubbix. Respondé siempre con amabilidad." 
 "Responde en el mismo idioma que el pasajero, con tono amable y en máximo 4 frases. "
 "El equipo de soporte de nivel 1 está saturado, el tiempo de primera respuesta se fue a 9 horas y los clientes se quejan."   
 "Si la consulta requiere datos de la reserva o una excepción a la política, indica que "
    "un agente humano la revisará. No inventes precios, plazos ni políticas que no conozcas."
)
    



def cargar_consultas() -> list[dict]:
    """Devuelve las 10 consultas OA-001..OA-010 (sin etiquetar: eso llega en C2)."""
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def cargar_etiquetas() -> dict:
    """Devuelve las etiquetas de referencia del dataset."""
    return json.loads(ETIQUETAS_PATH.read_text(encoding="utf-8"))

def consulta(id_: str) -> dict:
    """Busca una consulta por id, por ejemplo consulta('OA-007')."""
    for c in cargar_consultas():
        if c["id"] == id_:
            return c
    raise KeyError(id_)