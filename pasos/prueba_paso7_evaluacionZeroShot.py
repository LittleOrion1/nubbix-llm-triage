
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from M1P1.cliente import ask
from M1P1.prompts import renderizar_system


# --------------------------------------------------
# 1. RUTAS Y CONFIGURACIÓN
# --------------------------------------------------

RUTA_CONSULTAS = BASE_DIR / "data" / "consultas_dev.json"
RUTA_PREDICCIONES = BASE_DIR / "data" / "predicciones_v1ZeroShot.json"

CATEGORIAS_VALIDAS = {
    "billing",
    "technical",
    "account",
    "other"
}


# --------------------------------------------------
# 2. CARGA DE DATOS
# --------------------------------------------------

def cargar_json(ruta):
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_predicciones():
    if not RUTA_PREDICCIONES.exists():
        return {}

    registros = cargar_json(RUTA_PREDICCIONES)

    return {
        registro["id"]: registro
        for registro in registros
        if "id" in registro
    }


# --------------------------------------------------
# 3. GUARDADO PROGRESIVO
# --------------------------------------------------

def guardar_predicciones(predicciones):

    registros = list(predicciones.values())

    with RUTA_PREDICCIONES.open("w", encoding="utf-8") as archivo:
        json.dump(
            registros,
            archivo,
            ensure_ascii=False,
            indent=2
        )


# --------------------------------------------------
# 4. PROCESAMIENTO DE CONSULTAS
# --------------------------------------------------

def main():

    consultas = cargar_json(RUTA_CONSULTAS)
    predicciones = cargar_predicciones()

    system = renderizar_system("v1ZeroShot")

    print("=" * 55)
    print("EVALUACIÓN TRIAGE - ZERO SHOT")
    print("=" * 55)

    print(f"Consultas totales: {len(consultas)}")

    completadas = sum(
        1 for registro in predicciones.values()
        if registro.get("estado") == "ok"
    )

    print(f"Consultas ya procesadas correctamente: {completadas}")

    for consulta in consultas:

        id_consulta = consulta["id"]

        # Evitamos repetir consultas ya completadas.
        if (
            id_consulta in predicciones
            and predicciones[id_consulta].get("estado") == "ok"
        ):
            print(f"\n{id_consulta}: ya procesada. Se omite.")
            continue

        print(f"\nProcesando {id_consulta}...")

        # Ejecutamos la inferencia.
        try:

            response = ask(
                provider="openai",
                prompt=consulta["texto"],
                system=system
            )

        except Exception as error:

            predicciones[id_consulta] = {
                "id": id_consulta,
                "estado": "error_api",
                "error": str(error)
            }

            guardar_predicciones(predicciones)

            print(f"Error en la API: {error}")
            continue

        # Interpretamos la respuesta JSON.
        try:

            resultado = json.loads(response.text)

            categoria = resultado["category"]
            confianza = resultado["confidence"]

            if categoria not in CATEGORIAS_VALIDAS:
                raise ValueError(
                    f"Categoría no válida: {categoria}"
                )

            if (
                isinstance(confianza, bool)
                or not isinstance(confianza, (int, float))
                or not 0 <= confianza <= 1
            ):
                raise ValueError(
                    f"Confianza no válida: {confianza}"
                )

            registro = {
                "id": id_consulta,
                "estado": "ok",
                "categoria_predicha": categoria,
                "confianza": confianza,
                "modelo": response.model,
                "tokens_entrada": response.input_tokens,
                "tokens_salida": response.output_tokens,
                "costo_usd": response.cost_usd,
                "latencia_s": response.latency_s,
                "mock": response.mock
            }

        except (ValueError, KeyError, TypeError) as error:

            registro = {
                "id": id_consulta,
                "estado": "error_respuesta",
                "respuesta_bruta": response.text,
                "error": str(error),
                "modelo": response.model,
                "tokens_entrada": response.input_tokens,
                "tokens_salida": response.output_tokens,
                "costo_usd": response.cost_usd,
                "latencia_s": response.latency_s,
                "mock": response.mock
            }

        # Guardamos inmediatamente el resultado.
        predicciones[id_consulta] = registro
        guardar_predicciones(predicciones)

        print(f"Estado: {registro['estado']}")

        if registro["estado"] == "ok":
            print(f"Categoría: {categoria}")
            print(f"Confianza: {confianza}")

    print("\n" + "=" * 55)
    print("PROCESAMIENTO FINALIZADO")
    print("=" * 55)

    total_ok = sum(
        1 for registro in predicciones.values()
        if registro.get("estado") == "ok"
    )

    print(f"Clasificaciones correctas de formato: {total_ok}")
    print(f"Registros almacenados: {len(predicciones)}")
    print(f"Archivo: {RUTA_PREDICCIONES}")


if __name__ == "__main__":
    main()
