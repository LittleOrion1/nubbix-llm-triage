
from pydantic import ValidationError

from .cliente import ask
from .esquema import ClasificacionTriage
from .datos import SYSTEM_PROMPT
from .security import (
    validar_entrada,
    final_gate,
    EntradaNoSegura,
    SalidaNoSegura
)

# --------------------------------------------------
# ERRORES TIPADOS
# --------------------------------------------------

class ErrorClasificacion(Exception):
    """Error general durante la clasificación."""


class ErrorProveedor(ErrorClasificacion):
    """Error durante la comunicación con el proveedor."""


class ErrorValidacionAgotada(ErrorClasificacion):
    """El modelo no consiguió generar una respuesta válida."""


# --------------------------------------------------
# CLASIFICACIÓN CON VALIDACIÓN Y REINTENTOS
# --------------------------------------------------

def clasificar_consulta(
    texto: str,
    provider: str = "openai",
    system: str = SYSTEM_PROMPT,
    max_intentos: int = 3,
    # Comprobación de seguridad antes de consultar al LLM.
    
) -> tuple[ClasificacionTriage, object]:

    """
    Clasifica una consulta y valida la respuesta con Pydantic.

    Si la respuesta no cumple el esquema, vuelve a consultar
    al modelo indicándole el error de validación.

    Devuelve:
        Tupla con la clasificación validada y la última respuesta LLM.
    """

    if max_intentos < 1:
        raise ValueError("max_intentos debe ser al menos 1")
    validar_entrada(texto)
    prompt_actual = texto
    ultimo_error = None

    for intento in range(1, max_intentos + 1):

        # 1. Consultamos al proveedor.
        try:
            response = ask(
                provider=provider,
                prompt=prompt_actual,
                system=system
            )

        except Exception as error:
            raise ErrorProveedor(
                f"Error del proveedor {provider}: {error}"
            ) from error
        # 2. Comprobamos la seguridad de la respuesta.
        gate = final_gate(response.text)

        if gate["action"] == "bloquear":
            raise SalidaNoSegura(gate["reason"])


        # 3. Validamos respuesta con pydantic.
        try:
            resultado = ClasificacionTriage.model_validate_json(
                response.text
            )

            return resultado, response

        except (ValidationError, ValueError, TypeError) as error:

            ultimo_error = error

            # 3. Si quedan intentos, preparamos la corrección.
            if intento < max_intentos:

                prompt_actual = f"""
La consulta original del usuario es:

<consulta>
{texto}
</consulta>

Tu respuesta anterior no cumplió el esquema JSON requerido.

Error de validación:
{error}

Volvé a clasificar la consulta original.

Devolvé exclusivamente un JSON válido con esta estructura:

{{
    "category": "billing | technical | account | other",
    "confidence": 0.95
}}

No agregues explicaciones ni bloques Markdown.
"""

    # 4. Se agotaron los intentos.
    raise ErrorValidacionAgotada(
        f"No se obtuvo una respuesta válida después de "
        f"{max_intentos} intentos. Último error: {ultimo_error}"
    ) from ultimo_error
