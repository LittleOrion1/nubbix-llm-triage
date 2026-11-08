
import json
from pathlib import Path
from statistics import mean

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ARCHIVOS = {
    "Zero-Shot": DATA_DIR / "predicciones_v1ZeroShot.json",
    "Few-Shot": DATA_DIR / "predicciones_v2FewShot.json"
}


def cargar_predicciones(ruta):
    with ruta.open("r", encoding="utf-8") as archivo:
        registros = json.load(archivo)

    return {
        registro["id"]: registro
        for registro in registros
        if registro.get("estado") == "ok"
    }


def analizar(nombre, predicciones):

    registros = list(predicciones.values())

    return {
        "experimento": nombre,
        "consultas": len(registros),
        "tokens_entrada_promedio": mean(
            r["tokens_entrada"] for r in registros
        ),
        "tokens_salida_promedio": mean(
            r["tokens_salida"] for r in registros
        ),
        "costo_total": sum(
            r["costo_usd"] for r in registros
        ),
        "latencia_promedio": mean(
            r["latencia_s"] for r in registros
        ),
        "modelos": set(r["modelo"] for r in registros),
        "mock": set(r["mock"] for r in registros)
    }


def main():

    zero = cargar_predicciones(ARCHIVOS["Zero-Shot"])
    few = cargar_predicciones(ARCHIVOS["Few-Shot"])

    resultados = [
        analizar("Zero-Shot", zero),
        analizar("Few-Shot", few)
    ]

    print("=" * 65)
    print("COMPARATIVA DE PROMPTS")
    print("=" * 65)

    for resultado in resultados:

        print(f"\n{resultado['experimento']}")

        for clave, valor in resultado.items():

            if clave == "experimento":
                continue

            print(f"{clave}: {valor}")

    # Consultas presentes en ambos experimentos.
    ids_comunes = set(zero) & set(few)

    discrepancias = [
        id_consulta
        for id_consulta in ids_comunes
        if zero[id_consulta]["categoria_predicha"]
        != few[id_consulta]["categoria_predicha"]
    ]

    print("\n" + "=" * 65)
    print("DISCREPANCIAS ENTRE PROMPTS")
    print("=" * 65)

    print(f"Consultas comparadas: {len(ids_comunes)}")
    print(f"Predicciones diferentes: {len(discrepancias)}")

    for id_consulta in discrepancias:

        print(f"\n{id_consulta}")
        print(
            "Zero-Shot:",
            zero[id_consulta]["categoria_predicha"]
        )
        print(
            "Few-Shot:",
            few[id_consulta]["categoria_predicha"]
        )
#Lo que arroja es que zero shot es mejor -> consume menos y tiene el mismo nivel predictivo.abs

if __name__ == "__main__":
    main()


