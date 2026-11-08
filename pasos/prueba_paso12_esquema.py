
import sys
from pathlib import Path

# Permite correrlo como `python pasos/prueba_paso12_esquema.py`
# o desde la carpeta de scripts sin depender del directorio actual.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from M1P1.esquema import ClasificacionTriage

# Clasificación válida
resultado = ClasificacionTriage(
    category="billing",
    confidence=0.95
)

print("Clasificación validada:")
print(resultado.model_dump())


# Clasificación inválida
try:
    ClasificacionTriage(
        category="ventas",
        confidence=0.95
    )
except Exception as error:
    print("\nError de validación:")
    print(error)
