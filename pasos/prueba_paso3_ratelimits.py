
import json
import statistics
import time
from pathlib import Path
import sys

# =============== NO SE IGUAL ESTE ARCHIVO QUE ONDA. LO DEJO COMO ALGO EXPERIMENTAL PARA PROBAR EL STREAMING Y LOS RATE LIMITS. =====================
# Agregamos la raíz del proyecto al path de Python.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


from M1P1 import config
from M1P1.cliente import _openai_stream


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

MODELO = config.MODELOS["openai"]
MAX_TOKENS = config.MAX_TOKENS

# Utilizamos el mismo prompt del Paso 2.
SYSTEM_PROMPT = """
Sos un asistente de atención al cliente.
Respondé de manera clara, precisa y concisa.
Si no tenés información suficiente, indicá que no podés confirmarla.
"""

# Cantidad de consultas a evaluar.
# None significa evaluar todas.
MAX_CONSULTAS = 3

# Solicitamos información de uso de tokens.
INCLUIR_USAGE = True

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "consultas.json"


# --------------------------------------------------
# CARGA DE CONSULTAS
# --------------------------------------------------

with open(DATA_PATH, "r", encoding="utf-8") as archivo:
    consultas = json.load(archivo)

if MAX_CONSULTAS is not None:
    consultas = consultas[:MAX_CONSULTAS]


# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------

def percentil(valores, p):
    if not valores:
        return None

    ordenados = sorted(valores)
    indice = round((len(ordenados) - 1) * p)

    return ordenados[indice]


def analizar_stream(prompt):

    tiempos_fragmentos = []
    fragmentos = []
    metadata = None

    inicio = time.perf_counter()

    eventos = _openai_stream(
        model=MODELO,
        system=SYSTEM_PROMPT,
        prompt=prompt,
        temperature=config.TEMPERATURE,
        max_tokens=MAX_TOKENS,
        incluir_usage=INCLUIR_USAGE
    )

    for evento in eventos:

        instante = time.perf_counter()

        # Fragmento de texto recibido.
        if "delta" in evento:
            fragmentos.append(evento["delta"])
            tiempos_fragmentos.append(instante)

        # Metadata final.
        else:
            metadata = evento

    latencia_cliente = time.perf_counter() - inicio

    # --------------------------------------------------
    # INTERVALOS ENTRE FRAGMENTOS
    # --------------------------------------------------

    intervalos = [
        (tiempos_fragmentos[i] - tiempos_fragmentos[i - 1]) * 1000
        for i in range(1, len(tiempos_fragmentos))
    ]

    jitter_ms = (
        statistics.pstdev(intervalos)
        if len(intervalos) >= 2
        else None
    )

    intervalo_medio_ms = (
        statistics.mean(intervalos)
        if intervalos
        else None
    )

    # --------------------------------------------------
    # MÉTRICAS
    # --------------------------------------------------

    texto_completo = "".join(fragmentos)

    usage = metadata["usage"] if metadata else None

    tokens_entrada = (
        usage.prompt_tokens
        if usage is not None
        else None
    )

    tokens_salida = (
        metadata["output_tokens"]
        if metadata
        else None
    )

    return {
        "texto": texto_completo,
        "chunks": len(fragmentos),
        "ttft_s": metadata["ttft_s"] if metadata else None,
        "latencia_s": metadata["latency_s"] if metadata else None,
        "latencia_cliente_s": latencia_cliente,
        "jitter_ms": jitter_ms,
        "intervalo_medio_ms": intervalo_medio_ms,
        "intervalo_p95_ms": percentil(intervalos, 0.95),
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "throughput": metadata["tokens_per_second"] if metadata else None,
        "finish_reason": metadata["finish_reason"] if metadata else None
    }


# --------------------------------------------------
# EJECUCIÓN DE PRUEBAS
# --------------------------------------------------

resultados = []

print(f"\nModelo evaluado: {MODELO}")
print(f"Consultas: {len(consultas)}")
print("=" * 100)

for consulta in consultas:

    identificador = consulta["id"]
    prompt = consulta["texto"]

    print(f"\nProcesando {identificador}...")

    try:
        resultado = analizar_stream(prompt)
        resultado["id"] = identificador
        resultados.append(resultado)

        print(f"Respuesta: {resultado['texto']}")
        print(f"Chunks: {resultado['chunks']}")

    except Exception as error:
        print(f"Error en {identificador}: {error}")


# --------------------------------------------------
# TABLA DE RESULTADOS
# --------------------------------------------------

print("\n\nRESULTADOS DEL STREAMING")
print("=" * 120)

encabezado = (
    f"{'ID':<10}"
    f"{'TTFT(s)':>12}"
    f"{'Latencia(s)':>14}"
    f"{'Jitter(ms)':>14}"
    f"{'Int. medio(ms)':>17}"
    f"{'Chunks':>10}"
    f"{'Tokens out':>13}"
    f"{'Tokens/s':>12}"
)

print(encabezado)
print("-" * 120)

for r in resultados:

    def formato(valor, decimales=3):
        return f"{valor:.{decimales}f}" if valor is not None else "N/D"

    print(
        f"{r['id']:<10}"
        f"{formato(r['ttft_s']):>12}"
        f"{formato(r['latencia_s']):>14}"
        f"{formato(r['jitter_ms']):>14}"
        f"{formato(r['intervalo_medio_ms']):>17}"
        f"{r['chunks']:>10}"
        f"{str(r['tokens_salida'] or 'N/D'):>13}"
        f"{formato(r['throughput']):>12}"
    )


# --------------------------------------------------
# RESUMEN GENERAL
# --------------------------------------------------

if resultados:

    print("\nRESUMEN GENERAL")
    print("=" * 60)

    for metrica in [
        "ttft_s",
        "latencia_s",
        "jitter_ms",
        "intervalo_medio_ms",
        "throughput"
    ]:

        valores = [
            r[metrica]
            for r in resultados
            if r[metrica] is not None
        ]

        if valores:
            print(
                f"{metrica:<25}"
                f"Promedio: {statistics.mean(valores):.3f}"
            )
