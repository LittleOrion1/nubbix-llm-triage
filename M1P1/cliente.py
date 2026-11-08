
# ============================================================
# CLIENTE MULTIPROVEEDOR - NUBBIX
# ============================================================
# Este módulo permite consultar distintos proveedores de LLM
# utilizando una misma función: ask().
#
# Proveedores:
#   - OpenAI
#   - Gemini
#
# También permite trabajar en modo MOCK, simulando respuestas
# sin realizar llamadas reales a las APIs.
# ============================================================

# -------------------------
# 1. LIBRERÍAS
# -------------------------

import time
from dataclasses import dataclass, asdict
from .reintentos import with_retry
# Importamos la configuración, el módulo de simulación
# y el prompt del sistema.
from . import config, mock, datos

from M1P1.prompts import renderizar_system

# -------------------------
# 2. CONTRATO DE RESPUESTA
# -------------------------

@dataclass
class LLMResponse:
    """
    Estructura unificada de respuesta.

    Independientemente del proveedor utilizado, ask()
    siempre devolverá un objeto de esta clase.
    """

    provider: str
    model: str
    text: str

    input_tokens: int
    output_tokens: int

    cost_usd: float
    latency_s: float

    finish_reason: str

    # Campos opcionales o complementarios.
    ttft_s: float | None = None
    thinking_tokens: int = 0
    usage_disponible: bool = True
    mock: bool = False

    def to_dict(self) -> dict:
        """
        Convierte el objeto en un diccionario.
        asdict() pertenece al módulo dataclasses.
        """
        return asdict(self)

    @property
    def latency(self) -> float:
        """
        Alias para mantener compatibilidad con código
        anterior que utilice response.latency.
        """
        return self.latency_s


# -------------------------
# 3. NORMALIZACIÓN
# -------------------------

# Los proveedores utilizan diferentes nombres para indicar
# por qué terminó una generación.
#
# Nosotros unificamos esos nombres.

_FINISH = {
    "stop": "stop",
    "end_turn": "stop",
    "stop_sequence": "stop",
    "STOP": "stop",

    "length": "length",
    "max_tokens": "length",
    "MAX_TOKENS": "length",
}


# -------------------------
# 4. CLIENTES DE LOS SDK
# -------------------------

# Diccionario que almacena los clientes ya inicializados.
#
# Así evitamos crear un cliente nuevo cada vez que
# llamamos a ask().

_clientes = {}


def _cliente(provider: str):
    """
    Inicializa el cliente del proveedor solicitado.

    Se utiliza caché: si el cliente ya fue creado,
    se devuelve el existente.
    """

    if provider in _clientes:
        return _clientes[provider]

    # OpenAI
    if provider == "openai":

        from openai import OpenAI

        cliente = OpenAI(
            api_key=config.OPENAI_API_KEY
        )

    # Anthropic
    elif provider == "anthropic":

        from anthropic import Anthropic

        cliente = Anthropic(
            api_key=config.ANTHROPIC_API_KEY
        )

    # Gemini
    elif provider == "gemini":

        from google import genai

        cliente = genai.Client(
            api_key=config.GEMINI_API_KEY
        )

    else:
        raise ValueError(
            f"Proveedor desconocido: {provider}"
        )

    # Guardamos el cliente para reutilizarlo.
    _clientes[provider] = cliente

    return cliente


# -------------------------
# 5. ADAPTADORES
# -------------------------

# Cada adaptador traduce la llamada genérica de ask()
# al formato particular que necesita cada SDK.
#
# Todos deben devolver un diccionario con la misma estructura:
#
# {
#     "text": ...,
#     "input_tokens": ...,
#     "output_tokens": ...,
#     "thinking_tokens": ...,
#     "finish_reason": ...
# }


def _openai(model, system, prompt, temperature, max_tokens):
    """
    Realiza una consulta a OpenAI.
    """

    cliente = _cliente("openai")

    respuesta = with_retry(
        lambda: cliente.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=max_tokens
        )
    )

    # Extraemos el contenido generado.
    texto = respuesta.choices[0].message.content or ""

    # Extraemos los datos de consumo.
    usage = respuesta.usage

    return {
        "text": texto,

        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,

        "thinking_tokens": 0,

        "finish_reason": respuesta.choices[0].finish_reason
    }

#=================STREAMING DE OPENAI ========================
def _openai_stream(model, system, prompt, temperature, max_tokens, incluir_usage):

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=max_tokens,
        stream=True
    )

    # Solicitamos que el último chunk incluya los datos de uso.
    if incluir_usage:
        kwargs["stream_options"] = {"include_usage": True}

    usage = None
    finish = None
    ttft = None
    cliente = _cliente("openai")
    stream = _cliente("openai").chat.completions.create(**kwargs)

    print("DEBUG STREAM:", type(stream))
    print("DEBUG STREAM VALUE:", stream)

def _anthropic(model, system, prompt, temperature, max_tokens):
    """
    Realiza una consulta a Anthropic.
    """

    cliente = _cliente("anthropic")

    respuesta = cliente.messages.create(
        model=model,

        max_tokens=max_tokens,
        temperature=temperature,

        system=system,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Anthropic puede devolver diferentes bloques de contenido.
    # Nos quedamos con los bloques de texto.
    texto = "".join(
        bloque.text
        for bloque in respuesta.content
        if bloque.type == "text"
    )

    usage = respuesta.usage

    return {
        "text": texto,

        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,

        "thinking_tokens": 0,

        "finish_reason": respuesta.stop_reason
    }


def _gemini(model, system, prompt, temperature, max_tokens):
    """
    Realiza una consulta a Google Gemini.
    """

    from google.genai import types

    cliente = _cliente("gemini")

    respuesta = with_retry(
        lambda: cliente.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(
                    thinking_level=config.GEMINI_THINKING_LEVEL
                )
            )
        )
    )

    usage = respuesta.usage_metadata

    # Algunos campos pueden no estar disponibles.
    input_tokens = usage.prompt_token_count or 0

    output_tokens = usage.candidates_token_count or 0

    thinking_tokens = usage.thoughts_token_count or 0

    # El thinking también consume tokens de salida.
    output_tokens += thinking_tokens

    # Normalizamos el motivo de finalización.
    finish_reason = "stop"

    if respuesta.candidates:
        reason = respuesta.candidates[0].finish_reason

        if reason is not None:
            finish_reason = reason.name

    return {
        "text": respuesta.text or "",

        "input_tokens": input_tokens,
        "output_tokens": output_tokens,

        "thinking_tokens": thinking_tokens,

        "finish_reason": finish_reason
    }


# -------------------------
# 6. REGISTRO DE ADAPTADORES
# -------------------------

# Importante:
# Las funciones anteriores deben estar definidas antes
# de registrarlas en este diccionario.

_ADAPTADORES = {
    "openai": _openai,
    "anthropic": _anthropic,
    "gemini": _gemini
}


# -------------------------
# 7. VALIDACIÓN
# -------------------------

def _validar(provider: str) -> str:
    """
    Comprueba que el proveedor exista y que tenga
    credenciales disponibles cuando no estamos en MOCK.

    Devuelve el nombre del modelo configurado.
    """

    if provider not in _ADAPTADORES:

        raise ValueError(
            f"Proveedor desconocido: {provider}. "
            f"Opciones: {list(_ADAPTADORES)}"
        )

    # En modo MOCK no necesitamos API Keys.
    if not config.MOCK:

        keys = {
            "openai": config.OPENAI_API_KEY,
            "anthropic": config.ANTHROPIC_API_KEY,
            "gemini": config.GEMINI_API_KEY
        }

        if not keys[provider]:

            raise ValueError(
                f"No hay API Key configurada para {provider}"
            )

    return config.MODELOS[provider]


# -------------------------
# 8. COSTOS
# -------------------------

def calcular_costo(model, input_tokens, output_tokens):
    """
    Calcula el costo estimado de una consulta.

    IMPORTANTE:
    Todavía no configuramos tarifas por modelo.
    Por eso devuelve 0.0 temporalmente.

    Más adelante incorporaremos una tabla de precios
    actualizada para cada proveedor y modelo.
    """

    return 0.0


# -------------------------
# 9. FUNCIÓN PRINCIPAL
# -------------------------

def ask(
    provider: str,
    prompt: str,
    *,
    system=datos.SYSTEM_PROMPT,
    temperature=None,
    max_tokens=None
) -> LLMResponse:

    """
    Consulta un LLM independientemente del proveedor.

    Parámetros:
        provider: openai, anthropic o gemini.
        prompt: consulta del usuario.
        system: instrucciones del sistema.
        temperature: nivel de variabilidad.
        max_tokens: máximo de tokens de salida.

    Devuelve:
        Un objeto LLMResponse.
    """

    # 1. Validamos el proveedor y obtenemos su modelo.
    model = _validar(provider)

    # 2. Si no se especifican parámetros,
    # utilizamos los valores del archivo config.py.

    temperature = (
        config.TEMPERATURE
        if temperature is None
        else temperature
    )

    max_tokens = (
        config.MAX_TOKENS
        if max_tokens is None
        else max_tokens
    )

    # 3. Comenzamos a medir el tiempo de ejecución.
    t0 = time.perf_counter()

    # 4. Elegimos entre simulación y API real.

    if config.MOCK:

        # Prepara el proveedor para la simulación.
        mock.preparar(provider)

        # Genera una respuesta ficticia.
        raw = mock.completar(
            provider,
            system,
            prompt,
            temperature,
            max_tokens
        )

    else:

        # Ejecuta el adaptador correspondiente.
        raw = _ADAPTADORES[provider](
            model,
            system,
            prompt,
            temperature,
            max_tokens
        )

    # 5. Calculamos la latencia.
    latency = time.perf_counter() - t0

    # 6. Normalizamos el motivo de finalización.
    finish_reason = raw.get("finish_reason", "unknown")

    finish_reason = _FINISH.get(
        finish_reason,
        finish_reason
    )

    # 7. Calculamos el costo estimado.
    cost = calcular_costo(
        model,
        raw["input_tokens"],
        raw["output_tokens"]
    )

    # 8. Construimos una respuesta unificada.
    return LLMResponse(

        provider=provider,
        model=model,

        text=raw["text"],

        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],

        thinking_tokens=raw.get("thinking_tokens", 0),

        finish_reason=finish_reason,

        cost_usd=cost,
        latency_s=latency,

        ttft_s=None,

        usage_disponible=True,

        mock=config.MOCK
    )


