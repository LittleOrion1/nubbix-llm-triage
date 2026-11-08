from pathlib import Path
import sys 

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from M1P1.clasificacion import (
    clasificar_consulta,
    ErrorProveedor,
    ErrorValidacionAgotada
)

consulta = (
    "Me cobraron dos veces la última factura "
    "y necesito que me devuelvan el dinero."
)

try:
    resultado, response = clasificar_consulta(
        texto=consulta,
        provider="openai",
        max_intentos=3
    )

    print("\nCLASIFICACIÓN EXITOSA")
    print("=====================")
    print("Categoría:", resultado.category)
    print("Confianza:", resultado.confidence)
    print("Modelo:", response.model)
    print("Tokens entrada:", response.input_tokens)
    print("Tokens salida:", response.output_tokens)

except ErrorValidacionAgotada as error:
    print("VALIDACIÓN AGOTADA:", error)

except ErrorProveedor as error:
    print("ERROR DEL PROVEEDOR:", error)
