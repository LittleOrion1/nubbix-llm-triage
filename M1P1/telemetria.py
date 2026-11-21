import json
from pathlib import Path


REGISTRO_DIR = Path(__file__).resolve().parent.parent / "registro"
REGISTRO_DIR.mkdir(parents=True, exist_ok=True)


def guardar_evento(registro:dict) -> None: 
    evento =   json.dumps(registro)
    archivo_eventos = REGISTRO_DIR /"eventos.jsonl"
    with open(archivo_eventos,"a", encoding="utf-8") as archivo:
        archivo.write(evento + "\n")

def resumir_lote(batch_id:str )-> dict: 
    archivo_para_lote= REGISTRO_DIR / "eventos.jsonl"

    eventos_lote= []
    
    
    with open(archivo_para_lote, "r", encoding="utf-8") as archivo:

        for linea in archivo:
            evento = json.loads(linea)
            if evento.get("batch_id") == batch_id:
                eventos_lote.append(evento)
    total_consultas= len(eventos_lote)
    
    if total_consultas == 0:
        raise ValueError("No existe el lote indicado")   

    exitos = sum (1 for elemento in eventos_lote if elemento.get("status") == "success" )
    fallidos = total_consultas - exitos 
    
    # evento["latency"] busca la clave "latency" en el diccionario.
    # Si existe, devuelve su valor.
    # Si NO existe, produce un KeyError.

    latencia_total = sum(evento["latency"] for evento in eventos_lote)
    
    # .get() busca una clave dentro del diccionario.
    # Si existe, devuelve su valor.
    # Si NO existe, devuelve None (por defecto).
    
    costo_total = sum((evento.get("cost_usd") or 0) for evento in eventos_lote)
    
    latencia_promedio = latencia_total / total_consultas
    
    resumen = {"batch_id":batch_id, "total_consultas":total_consultas, "exitos":exitos,
               "fallidas": fallidos, "latencia_total":latencia_total,
               "costo_total_usd":costo_total, "latencia_promedio":latencia_promedio}
    
    return resumen 
 
