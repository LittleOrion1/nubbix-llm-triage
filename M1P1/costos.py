
import json
from pathlib import Path


# Cargar tarifas desde pricing.json
PRICING_PATH = Path(__file__).resolve().parent / "pricing.json"

with open(PRICING_PATH, "r", encoding="utf-8") as archivo:
    PRICING = json.load(archivo)


def obtener_tarifa(modelo: str) -> dict:
    """
    Busca las tarifas de un modelo entre todos los proveedores.
    """
    proveedores = PRICING["models"]

    for proveedor, modelos in proveedores.items():
        if modelo in modelos:
            return modelos[modelo]

    raise KeyError(
        f"El modelo '{modelo}' no está en pricing.json."
    )


def calcular_costo(
    modelo: str,
    tokens_entrada: int,
    tokens_salida: int
) -> float:
    """
    Calcula el costo de una solicitud en USD.

    Las tarifas están expresadas por millón de tokens.
    """
    if tokens_entrada < 0 or tokens_salida < 0:
        raise ValueError("Los tokens no pueden ser negativos.")

    tarifa = obtener_tarifa(modelo)

    costo_entrada = (
        tokens_entrada * tarifa["input"] / 1_000_000
    )

    costo_salida = (
        tokens_salida * tarifa["output"] / 1_000_000
    )

    return costo_entrada + costo_salida
    