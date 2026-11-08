"""
PASO 2 — Tokenización: idiomas, emojis y presupuesto de contexto (parte B de la consigna).

La tokenización con tiktoken es REAL también en modo mock.
Ejecutar:
    uv run python -m pasos.paso2_tokens
"""
import sys
from pathlib import Path

# Permite correrlo también como `python pasos/pasoX.py` o desde la carpeta pasos/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tiktoken

from M1P1 import config
from M1P1.costos import calcular_costo
from M1P1.datos import SYSTEM_PROMPT, cargar_consultas, consulta
from M1P1.tokenizadores import (
    
    contar_gemini, 
    tokenizador_gemini,
    contar_openai,
    tokenizador_openai
    )

MODELO_OPENAI = config.MODELOS["openai"]

ENC_OPENAI = tokenizador_openai(MODELO_OPENAI)

CL100K = tiktoken.get_encoding("cl100k_base")

GEMINI = config.MODELOS["gemini"]

def gemini_local_disponible() -> bool:
    try:
        tokenizador_gemini(GEMINI)
        return True
    except Exception as e:
        print(f"  (tokenizador local de Gemini no disponible para {GEMINI}: {e})")
        return False


def piezas_bytes(lista_bytes: list[bytes]) -> str:
    """Mismo formato que piezas(), para tokens que vienen como bytes (Gemini)."""
    salida = []
    for b in lista_bytes:
        try:
            salida.append(f"[{b.decode('utf-8')}]")
        except UnicodeDecodeError:
            salida.append("<" + " ".join(f"{x:02X}" for x in b) + ">")
    return "".join(salida)


def piezas(texto: str, enc=ENC_OPENAI) -> str:
    """Muestra cómo se parte un texto: [El][ pago][ fall]... Los bytes sueltos se ven como <F0 9F>."""
    salida = []
    for t in enc.encode(texto):
        b = enc.decode_single_token_bytes(t)
        try:
            salida.append(f"[{b.decode('utf-8')}]")
        except UnicodeDecodeError:  # un trozo de emoji: no es un carácter válido por sí solo
            salida.append("<" + " ".join(f"{x:02X}" for x in b) + ">")
    return "".join(salida)


def main() -> None:
    # 2.1 — Tabla de las 10 consultas
    print("=" * 78)
    print(f"2.1 Las 10 consultas con tokenización local de OpenAI ({MODELO_OPENAI})")    
    print("=" * 78)
    con_gemini = gemini_local_disponible()
    print(f"{'id':<8}{'chars':>6}{'palabras':>9}{'tokens≈':>8}{'chars/tok':>10}{'cl100k':>8}{'gemini':>8}")    
    
    
    for c in cargar_consultas():
        t = c["texto"]
        n = contar_openai(MODELO_OPENAI, t)
        g = contar_gemini(GEMINI, t) if con_gemini else "-"
        print(f"{c['id']:<8}{len(t):>6}{len(t.split()):>9}{n:>8}{len(t) / n:>10.2f}{len(CL100K.encode(t)):>8}{g:>8}")
    print("\n  → Mayor chars/token indica que se necesitan menos tokens para representar ese texto.")
    print("  → Esto no implica necesariamente menor costo: depende de la tarifa del modelo.")
    print("  → OpenAI se cuenta localmente con un encoding que puede ser aproximado para Astra.")
    # 2.2 — Desarmar las consultas clave
    print("\n" + "=" * 78)
    print("2.2 ¿Cómo se parte cada consulta?")
    print("=" * 78)
    for id_ in ("OA-001", "OA-003", "OA-004"):
        t = consulta(id_)["texto"]
        print(f"\n{id_} ({len(ENC_OPENAI.encode(t))} tokens): {t}")
        print(f"  {piezas(t)}")


    # 2.5 — Estimar ANTES de llamar (solo válido para OpenAI) y presupuesto de contexto
    print("\n" + "=" * 78)
    print("2.5 Estimación de gpt-astra-6 y presupuesto aproximado de contexto")
    print("=" * 78)
    modelo = MODELO_OPENAI


    VENTANA_CONTEXTO = 1_050_000 #Es la de gpt astra 6
    MAX_OUTPUT = 128_000 #idem

    modelo = MODELO_OPENAI

    for id_ in ("OA-001", "OA-007"):
        t = consulta(id_)["texto"]

        entrada = (
            contar_openai(modelo, SYSTEM_PROMPT)
            + contar_openai(modelo, t)
        )

        peor_caso = entrada + config.MAX_TOKENS

        print(
            f"  {id_}: system+consulta ≈ {entrada} tokens "
            f"+ max_completion_tokens {config.MAX_TOKENS} "
            f"= {peor_caso}"
        )

        print(
            f"  Uso estimado del contexto: "
            f"{peor_caso / VENTANA_CONTEXTO:.5%}" ) 

   
    # 2.6 — Gemini: dos formas de contar ANTES de llamar
    print("\n" + "=" * 78)
    print(f"2.6 Gemini ({GEMINI}): tokenizador local y count_tokens vía API")
    print("=" * 78)
    if con_gemini:
        print("  a) LOCAL (google.genai.local_tokenizer.LocalTokenizer) — sin key, sin costo:")
        for id_ in ("OA-001", "OA-004"):
            t = consulta(id_)["texto"]
            info = tokenizador_gemini(GEMINI).compute_tokens(t).tokens_info[0]
            print(f"\n  {id_} · Gemini {len(info.tokens)} tokens vs ENC_OPENAI {len(ENC_OPENAI.encode(t))}")
            print(f"    gemini: {piezas_bytes(info.tokens)}")
            print(f"    ENC_OPENAI : {piezas(t)}")
        sistema = contar_gemini(GEMINI, SYSTEM_PROMPT)
        print(f"\n  System prompt: Gemini {sistema} tokens vs ENC_OPENAI {len(ENC_OPENAI.encode(SYSTEM_PROMPT))}")
    if not config.MOCK and "gemini" in config.proveedores_disponibles():
        from google import genai

        cliente = genai.Client(api_key=config.GEMINI_API_KEY)
        print("\n  b) API (client.models.count_tokens) — exacto, gratis, pero es una llamada de red:")
        for id_ in ("OA-001", "OA-003", "OA-004"):
            t = consulta(id_)["texto"]
            r = cliente.models.count_tokens(model=GEMINI, contents=t)
            local = contar_gemini(GEMINI, t) if con_gemini else "-"
            print(f"  {id_}: API={r.total_tokens:>3} · local={local:>3} · tiktoken ENC_OPENAI={len(ENC_OPENAI.encode(t)):>3}")
    else:
        print("\n  b) count_tokens vía API: se omite (modo mock o sin GEMINI_API_KEY).")

    # 2.7 — Anthropic: no hay tokenizador local; se cuenta vía API
    print("\n" + "=" * 78)
    print("2.7 Anthropic: los tokens se consultan a la API, no se calculan localmente")
    print("=" * 78)
    if config.MOCK or "anthropic" not in config.proveedores_disponibles():
        print("  (modo mock o sin ANTHROPIC_API_KEY: se omite. En el Paso 4 verás el usage simulado de Claude.)")
        return
    import anthropic

    cliente = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    for id_ in ("OA-001", "OA-003", "OA-004"):
        t = consulta(id_)["texto"]
        r = cliente.messages.count_tokens(model=config.MODELOS["anthropic"], messages=[{"role": "user", "content": t}])
        print(f"  {id_}: Claude={r.input_tokens:>3} tokens (incluye formato) · tiktoken ENC_OPENAI={len(ENC_OPENAI.encode(t)):>3}")


if __name__ == "__main__":
    main()