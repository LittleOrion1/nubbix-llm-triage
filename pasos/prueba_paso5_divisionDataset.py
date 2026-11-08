
"""
PASO 5 — Dividir el dataset en desarrollo y evaluación.

Desarrollo (dev): 80 consultas (20 por categoría).
Evaluación (holdout): 20 consultas (5 por categoría).

La división es estratificada y reproducible mediante una semilla fija.

Ejecutar desde la raíz del proyecto:
    .venv/bin/python pasos/prueba_paso5_divisionDataset.py
"""

#esto va a generar los archivos: consultas_dev.json, etiquetas_dev.json, consultas_holdout.json, etiquetas_holdout.json 


import json
import random
from collections import Counter
from pathlib import Path


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CONSULTAS_PATH = DATA_DIR / "consultas.json"
ETIQUETAS_PATH = DATA_DIR / "etiquetas.json"

CATEGORIAS = ("billing", "technical", "account", "other")

SEMILLA = 42
PROPORCION_HOLDOUT = 0.20


# --------------------------------------------------
# CARGA Y GUARDADO DE JSON
# --------------------------------------------------

def cargar_json(ruta: Path):
    """Carga un archivo JSON."""
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_json(datos, ruta: Path):
    """Guarda datos en formato JSON."""
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)


# --------------------------------------------------
# VALIDACIÓN DEL DATASET
# --------------------------------------------------

def validar_dataset(consultas, etiquetas):
    """Comprueba la integridad y distribución del dataset."""

    ids_consultas = [c["id"] for c in consultas]
    ids_etiquetas = set(etiquetas)

    # Verificar IDs duplicados.
    if len(ids_consultas) != len(set(ids_consultas)):
        raise ValueError("Hay IDs duplicados en consultas.json")

    # Verificar correspondencia entre consultas y etiquetas.
    if set(ids_consultas) != ids_etiquetas:
        raise ValueError(
            "Los IDs de consultas.json y etiquetas.json no coinciden"
        )

    # Verificar categorías válidas.
    for id_, etiqueta in etiquetas.items():
        if etiqueta["categoria"] not in CATEGORIAS:
            raise ValueError(
                f"Categoría inválida en {id_}: "
                f"{etiqueta['categoria']}"
            )

    # Verificar cantidad total.
    if len(consultas) != 100:
        raise ValueError(
            f"Se esperaban 100 consultas, hay {len(consultas)}"
        )

    # Verificar distribución equilibrada.
    distribucion = Counter(
        etiquetas[c["id"]]["categoria"]
        for c in consultas
    )

    for categoria in CATEGORIAS:
        if distribucion[categoria] != 25:
            raise ValueError(
                f"{categoria}: se esperaban 25 consultas, "
                f"hay {distribucion[categoria]}"
            )


# --------------------------------------------------
# DIVISIÓN ESTRATIFICADA
# --------------------------------------------------

def dividir_dataset(consultas, etiquetas):
    """
    Divide las consultas en desarrollo y evaluación.

    Mantiene 20 consultas de desarrollo y 5 de evaluación
    para cada categoría.
    """

    rng = random.Random(SEMILLA)

    consultas_dev = []
    consultas_holdout = []

    for categoria in CATEGORIAS:

        # Agrupar consultas por categoría.
        grupo = [
            consulta
            for consulta in consultas
            if etiquetas[consulta["id"]]["categoria"] == categoria
        ]

        # Mezclar aleatoriamente el grupo.
        rng.shuffle(grupo)

        # Calcular cantidad de consultas para evaluación.
        cantidad_holdout = round(
            len(grupo) * PROPORCION_HOLDOUT
        )

        # Separar desarrollo y evaluación.
        consultas_holdout.extend(grupo[:cantidad_holdout])
        consultas_dev.extend(grupo[cantidad_holdout:])

    # Mezclar el orden general de ambos conjuntos.
    rng.shuffle(consultas_dev)
    rng.shuffle(consultas_holdout)

    # Obtener los IDs de cada conjunto.
    ids_dev = {c["id"] for c in consultas_dev}
    ids_holdout = {c["id"] for c in consultas_holdout}

    # Separar las etiquetas correspondientes.
    etiquetas_dev = {
        id_: etiqueta
        for id_, etiqueta in etiquetas.items()
        if id_ in ids_dev
    }

    etiquetas_holdout = {
        id_: etiqueta
        for id_, etiqueta in etiquetas.items()
        if id_ in ids_holdout
    }

    return (
        consultas_dev,
        etiquetas_dev,
        consultas_holdout,
        etiquetas_holdout,
    )


# --------------------------------------------------
# INFORME DE DISTRIBUCIÓN
# --------------------------------------------------

def mostrar_distribucion(nombre, consultas, etiquetas):
    """Muestra la cantidad de consultas por categoría."""

    conteo = Counter(
        etiquetas[c["id"]]["categoria"]
        for c in consultas
    )

    print(f"\n{nombre}: {len(consultas)} consultas")

    for categoria in CATEGORIAS:
        print(f"  {categoria:<12}: {conteo[categoria]}")


# --------------------------------------------------
# EJECUCIÓN PRINCIPAL
# --------------------------------------------------

def main():

    # Cargar dataset original.
    consultas = cargar_json(CONSULTAS_PATH)
    etiquetas = cargar_json(ETIQUETAS_PATH)

    # Validar integridad.
    validar_dataset(consultas, etiquetas)

    # Dividir dataset.
    (
        consultas_dev,
        etiquetas_dev,
        consultas_holdout,
        etiquetas_holdout,
    ) = dividir_dataset(consultas, etiquetas)

    # Guardar los cuatro archivos.
    guardar_json(
        consultas_dev,
        DATA_DIR / "consultas_dev.json"
    )

    guardar_json(
        etiquetas_dev,
        DATA_DIR / "etiquetas_dev.json"
    )

    guardar_json(
        consultas_holdout,
        DATA_DIR / "consultas_holdout.json"
    )

    guardar_json(
        etiquetas_holdout,
        DATA_DIR / "etiquetas_holdout.json"
    )

    # Mostrar resultados.
    print("=" * 55)
    print("DIVISIÓN DEL DATASET COMPLETADA")
    print("=" * 55)

    mostrar_distribucion(
        "DESARROLLO",
        consultas_dev,
        etiquetas_dev
    )

    mostrar_distribucion(
        "EVALUACIÓN (HOLDOUT)",
        consultas_holdout,
        etiquetas_holdout
    )

    print("\nArchivos generados correctamente.")


if __name__ == "__main__":
    main()
