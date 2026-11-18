import json
from pathlib import Path


REGISTRO_DIR = Path(__file__).resolve().parent.parent / "registro"
REGISTRO_DIR.mkdir(parents=True, exist_ok=True)


def guardar_evento(registro:dict) -> None: 
    evento =   json.dumps(registro)
    archivo_eventos = REGISTRO_DIR /"eventos.jsonl"
    with open(archivo_eventos,"a", encoding="utf-8") as archivo:
        archivo.write(evento + "\n")
        