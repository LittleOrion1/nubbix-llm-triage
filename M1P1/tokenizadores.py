
# tokenizadores.py
# Cómo contar tokens ANTES de llamar, según el proveedor:
# OpenAI    → tiktoken (local, oficial)
# Gemini    → LocalTokenizer del SDK google-genai
# Anthropic → solo vía API

import warnings
from functools import lru_cache

import tiktoken

O200K = tiktoken.get_encoding("o200k_base")


@lru_cache

def tokenizador_openai(modelo: str):
    """
    Obtiene el tokenizador de OpenAI.
    Si el modelo no está registrado, utiliza o200k_base
    como aproximación local.
    """
    try:
        return tiktoken.encoding_for_model(modelo)
    except KeyError:
        return tiktoken.get_encoding("o200k_base")


def contar_openai(modelo: str, texto: str) -> int:
    """Cuenta los tokens de un texto utilizando tiktoken."""
    if not isinstance(texto, str):
        raise TypeError("El texto debe ser una cadena.")

    encoding = tokenizador_openai(modelo)
    return len(encoding.encode(texto, disallowed_special=()))


def tokenizador_gemini(modelo: str):
    """
    Tokenizador LOCAL de Gemini.
    La primera vez descarga el vocabulario.
    """
    warnings.filterwarnings(
        "ignore",
        message=".*local tokenizer.*"
    )

    from google.genai.local_tokenizer import LocalTokenizer

    return LocalTokenizer(model_name=modelo)


def contar_gemini(modelo: str, texto: str) -> int:
    return tokenizador_gemini(modelo).count_tokens(texto).total_tokens


