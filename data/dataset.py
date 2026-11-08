
"""
Generador de dataset sintético para Nubbix.

Completa consultas.json y etiquetas.json hasta alcanzar
25 consultas por categoría.

Ejecución desde la raíz:
    .venv/bin/python M1P1/dataset.py
"""
#El dataset son consultas con rtas correctas (ground truth)
# separamos 80% para entrenamiento, 20% para evaluación
#el triage es lo que explicás cómo debe comportarse el modelo

#ojo, estos triage deben salir del entrenamiento, no de la evaluación. 

import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

from faker import Faker


# --------------------------------------------------
# 1. CONFIGURACIÓN
# --------------------------------------------------

OBJETIVO_POR_CATEGORIA = 25
SEMILLA = 42

random.seed(SEMILLA)

fake = Faker("es_AR")
fake.seed_instance(SEMILLA)

# Detectar la carpeta data, tanto si dataset.py está
# dentro de M1P1 como si está en la raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent

if not (BASE_DIR / "data").exists():
    BASE_DIR = BASE_DIR.parent

DATA_DIR = BASE_DIR / "data"

CONSULTAS_PATH = DATA_DIR / "consultas.json"
ETIQUETAS_PATH = DATA_DIR / "etiquetas.json"

CATEGORIAS = ("billing", "technical", "account", "other")


# --------------------------------------------------
# 2. ESCENARIOS DE GENERACIÓN
# --------------------------------------------------

ESCENARIOS = {
    "billing": [
        {
            "plantilla": "Me cobraron dos veces el mismo servicio y quiero reclamar.",
            "regla": "R02",
            "nota": "Reclamo por cobro duplicado.",
            "justificacion": "El usuario reclama un cargo duplicado."
        },
        {
            "plantilla": "No recibí la factura correspondiente al mes de {mes}.",
            "regla": "R02",
            "nota": "Consulta sobre facturación.",
            "justificacion": "El usuario consulta por una factura no recibida."
        },
        {
            "plantilla": "Quiero solicitar un reembolso por un importe que me cobraron incorrectamente.",
            "regla": "R02",
            "nota": "Solicitud de reembolso.",
            "justificacion": "El usuario solicita la devolución de un cobro incorrecto."
        },
        {
            "plantilla": "El importe de mi última factura es superior al que esperaba.",
            "regla": "R02",
            "nota": "Discrepancia en el importe facturado.",
            "justificacion": "El usuario reclama una diferencia en el importe de facturación."
        },
        {
            "plantilla": "¿Cómo puedo cambiar mi método de pago?",
            "regla": "R05",
            "nota": "Cambio de método de pago.",
            "justificacion": "El usuario solicita modificar su medio de pago."
        },
        {
            "plantilla": "Mi tarjeta fue rechazada al intentar realizar el pago.",
            "regla": "R05",
            "nota": "Problema con un medio de pago.",
            "justificacion": "El usuario informa un inconveniente con el procesamiento del pago."
        },
        {
            "plantilla": "Quiero consultar si se registró el pago que realicé el día {fecha}.",
            "regla": "R02",
            "nota": "Consulta sobre registro de pago.",
            "justificacion": "El usuario consulta por el estado de un pago."
        },
        {
            "plantilla": "¿Puedo eliminar mi tarjeta actual y registrar otra?",
            "regla": "R05",
            "nota": "Administración de medios de pago.",
            "justificacion": "El usuario desea modificar los medios de pago registrados."
        }
    ],

    "technical": [
        {
            "plantilla": "No puedo iniciar sesión aunque estoy ingresando correctamente mi contraseña.",
            "regla": "R03",
            "nota": "Falla técnica de acceso.",
            "justificacion": "El usuario informa un problema de acceso sin solicitar recuperar sus credenciales."
        },
        {
            "plantilla": "La aplicación muestra un error cada vez que intento ingresar.",
            "regla": "R03",
            "nota": "Error de funcionamiento.",
            "justificacion": "El usuario informa un error técnico de la aplicación."
        },
        {
            "plantilla": "La página queda cargando y nunca termina de abrir.",
            "regla": "R03",
            "nota": "Problema de carga de la plataforma.",
            "justificacion": "El usuario describe una falla de funcionamiento."
        },
        {
            "plantilla": "No puedo completar una operación porque aparece un mensaje de error.",
            "regla": "R03",
            "nota": "Error al ejecutar una operación.",
            "justificacion": "El usuario informa una falla técnica durante el uso del sistema."
        },
        {
            "plantilla": "Desde ayer la plataforma funciona muy lentamente.",
            "regla": "R03",
            "nota": "Problema de rendimiento.",
            "justificacion": "El usuario reporta lentitud en el funcionamiento del sistema."
        },
        {
            "plantilla": "La aplicación se cierra inesperadamente cuando intento utilizarla.",
            "regla": "R03",
            "nota": "Falla de la aplicación.",
            "justificacion": "El usuario informa un cierre inesperado del sistema."
        },
        {
            "plantilla": "No puedo acceder a la plataforma desde mi computadora.",
            "regla": "R03",
            "nota": "Problema técnico de acceso.",
            "justificacion": "El usuario informa dificultades técnicas para acceder a la plataforma."
        },
        {
            "plantilla": "Me aparece el código de error 503 cuando intento ingresar.",
            "regla": "R03",
            "nota": "Error técnico de acceso.",
            "justificacion": "El usuario informa un código de error del sistema."
        }
    ],

    "account": [
        {
            "plantilla": "Quiero cambiar mi correo electrónico actual por {correo}.",
            "regla": "R01",
            "nota": "Modificación de correo electrónico.",
            "justificacion": "El usuario solicita modificar el correo asociado a su cuenta."
        },
        {
            "plantilla": "Olvidé mi contraseña y necesito restablecerla.",
            "regla": "R01",
            "nota": "Recuperación de credenciales.",
            "justificacion": "El usuario necesita recuperar el acceso mediante el restablecimiento de su contraseña."
        },
        {
            "plantilla": "¿Cómo puedo consultar los datos personales registrados en mi cuenta?",
            "regla": "R04",
            "nota": "Consulta de datos personales.",
            "justificacion": "El usuario solicita consultar la información de su cuenta."
        },
        {
            "plantilla": "Necesito actualizar mi nombre de {nombre} en el perfil.",
            "regla": "R04",
            "nota": "Actualización de perfil.",
            "justificacion": "El usuario solicita modificar información personal de su cuenta."
        },
        {
            "plantilla": "Quiero eliminar definitivamente mi cuenta de Nubbix.",
            "regla": "R04",
            "nota": "Solicitud de eliminación de cuenta.",
            "justificacion": "El usuario solicita gestionar la eliminación de su cuenta."
        },
        {
            "plantilla": "¿Dónde puedo modificar la información de mi perfil?",
            "regla": "R04",
            "nota": "Administración del perfil.",
            "justificacion": "El usuario consulta cómo administrar los datos de su cuenta."
        },
        {
            "plantilla": "Ya no tengo acceso al correo asociado a mi cuenta y necesito actualizarlo.",
            "regla": "R01",
            "nota": "Actualización de credenciales.",
            "justificacion": "El usuario solicita modificar el correo vinculado a su cuenta."
        },
        {
            "plantilla": "¿Cómo puedo cambiar mi contraseña actual?",
            "regla": "R01",
            "nota": "Modificación de contraseña.",
            "justificacion": "El usuario solicita modificar sus credenciales."
        }
    ],

    "other": [
        {
            "plantilla": "¿Qué temperatura va a hacer mañana en {ciudad}?",
            "regla": "R06",
            "nota": "Consulta ajena al servicio.",
            "justificacion": "La consulta no está relacionada con las funciones de Nubbix."
        },
        {
            "plantilla": "Necesito una recomendación de restaurantes en {ciudad}.",
            "regla": "R06",
            "nota": "Consulta fuera del dominio.",
            "justificacion": "El usuario solicita información ajena al servicio."
        },
        {
            "plantilla": "¿Quién ganó el último partido de fútbol?",
            "regla": "R06",
            "nota": "Consulta sobre deportes.",
            "justificacion": "La consulta no corresponde a ninguna categoría de soporte de Nubbix."
        },
        {
            "plantilla": "¿Me pueden recomendar una película para esta noche?",
            "regla": "R06",
            "nota": "Consulta ajena al servicio.",
            "justificacion": "El usuario solicita una recomendación no relacionada con Nubbix."
        },
        {
            "plantilla": "Hola, tengo una consulta.",
            "regla": "R07",
            "nota": "Consulta sin información suficiente.",
            "justificacion": "No hay información suficiente para identificar una intención clasificable."
        },
        {
            "plantilla": "No sé qué hacer, necesito ayuda.",
            "regla": "R07",
            "nota": "Mensaje ambiguo.",
            "justificacion": "El mensaje no especifica el problema ni la intención del usuario."
        },
        {
            "plantilla": "Quería preguntarles algo, pero no sé cómo explicarlo.",
            "regla": "R07",
            "nota": "Consulta incompleta.",
            "justificacion": "No existe información suficiente para asignar otra categoría."
        },
        {
            "plantilla": "¿Me pueden ayudar con una cuestión que tengo pendiente?",
            "regla": "R07",
            "nota": "Consulta sin intención definida.",
            "justificacion": "El usuario no proporciona información suficiente para identificar el motivo de contacto."
        }
    ]
}


# --------------------------------------------------
# 3. VARIACIONES LINGÜÍSTICAS
# --------------------------------------------------

PREFIJOS = [
    "",
    "Hola, ",
    "Buenas, ",
    "Necesito ayuda: ",
    "Tengo una consulta: ",
    "Por favor, ",
]

SUFIJOS = [
    "",
    " ¿Me pueden ayudar?",
    " Gracias.",
    " No sé cómo resolverlo.",
    " Necesito una solución.",
]


def generar_texto(escenario: dict) -> str:
    """Genera una variación de un escenario utilizando Faker."""

    variables = {
        "nombre": fake.name(),
        "correo": f"{fake.user_name()}@example.com",
        "fecha": fake.date(pattern="%d/%m/%Y"),
        "mes": fake.month_name(),
        "ciudad": fake.city(),
    }

    base = escenario["plantilla"].format(**variables)

    prefijo = random.choice(PREFIJOS)
    sufijo = random.choice(SUFIJOS)

    return f"{prefijo}{base}{sufijo}"


def normalizar(texto: str) -> str:
    """Normaliza texto para detectar duplicados."""

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter for caracter in texto
        if not unicodedata.combining(caracter)
    )

    return re.sub(r"\W+", "", texto.lower())


# --------------------------------------------------
# 4. CARGA Y VALIDACIÓN DE JSON
# --------------------------------------------------

def cargar_json(ruta: Path):
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró: {ruta}")

    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_json(ruta: Path, contenido) -> None:
    ruta.write_text(
        json.dumps(contenido, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


# --------------------------------------------------
# 5. GENERACIÓN DE IDS
# --------------------------------------------------

def siguiente_id(consultas: list[dict]) -> int:
    numeros = []

    for consulta in consultas:
        coincidencia = re.fullmatch(
            r"OA-(\d+)", consulta["id"]
        )

        if coincidencia:
            numeros.append(int(coincidencia.group(1)))

    return max(numeros, default=0) + 1


# --------------------------------------------------
# 6. COMPLETAR EL DATASET
# --------------------------------------------------

def completar_dataset() -> None:

    consultas = cargar_json(CONSULTAS_PATH)
    etiquetas = cargar_json(ETIQUETAS_PATH)

    if not isinstance(consultas, list) or not isinstance(etiquetas, dict):
        raise ValueError("Formato JSON inesperado.")

    ids_consultas = [c["id"] for c in consultas]

    if len(ids_consultas) != len(set(ids_consultas)):
        raise ValueError("Hay IDs duplicados en consultas.json.")

    ids_sin_etiqueta = set(ids_consultas) - set(etiquetas)
    ids_sobrantes = set(etiquetas) - set(ids_consultas)

    if ids_sin_etiqueta or ids_sobrantes:
        raise ValueError(
            f"Los JSON no están sincronizados. "
            f"Sin etiqueta: {ids_sin_etiqueta}. "
            f"Etiquetas sobrantes: {ids_sobrantes}."
        )

    for id_, etiqueta in etiquetas.items():
        if (
            not isinstance(etiqueta, dict)
            or etiqueta.get("categoria") not in CATEGORIAS
        ):
            raise ValueError(f"Etiqueta inválida en {id_}.")

    conteo = Counter(
        etiquetas[c["id"]]["categoria"]
        for c in consultas
    )

    print("\nDISTRIBUCIÓN INICIAL")
    print("-" * 40)

    for categoria in CATEGORIAS:
        print(f"{categoria:<15} {conteo[categoria]:>3}/25")

        if conteo[categoria] > OBJETIVO_POR_CATEGORIA:
            raise ValueError(
                f"{categoria} ya supera el objetivo de "
                f"{OBJETIVO_POR_CATEGORIA}. No se eliminarán consultas."
            )

    textos_existentes = {
        normalizar(c["texto"])
        for c in consultas
    }

    nuevo_numero = siguiente_id(consultas)
    agregadas = Counter()

    # Generar únicamente los ejemplos faltantes.
    for categoria in CATEGORIAS:

        faltantes = OBJETIVO_POR_CATEGORIA - conteo[categoria]

        intentos = 0

        while agregadas[categoria] < faltantes:

            intentos += 1

            if intentos > 2000:
                raise RuntimeError(
                    f"No fue posible generar suficientes consultas únicas "
                    f"para {categoria}."
                )

            escenario = random.choice(ESCENARIOS[categoria])
            texto = generar_texto(escenario)
            clave = normalizar(texto)

            if clave in textos_existentes:
                continue

            id_ = f"OA-{nuevo_numero:03d}"
            nuevo_numero += 1

            consulta_nueva = {
                "id": id_,
                "texto": texto,
                "nota": f"Generada sintéticamente. {escenario['nota']}"
            }

            etiqueta_nueva = {
                "categoria": categoria,
                "regla": escenario["regla"],
                "justificacion": escenario["justificacion"]
            }

            consultas.append(consulta_nueva)
            etiquetas[id_] = etiqueta_nueva

            textos_existentes.add(clave)
            agregadas[categoria] += 1

    # Guardar ambos archivos.
    guardar_json(CONSULTAS_PATH, consultas)
    guardar_json(ETIQUETAS_PATH, etiquetas)

    # Resumen final.
    conteo_final = Counter(
        etiquetas[c["id"]]["categoria"]
        for c in consultas
    )

    print("\nCONSULTAS AGREGADAS")
    print("-" * 40)

    for categoria in CATEGORIAS:
        print(f"{categoria:<15} +{agregadas[categoria]:>3}")

    print("\nDISTRIBUCIÓN FINAL")
    print("-" * 40)

    for categoria in CATEGORIAS:
        print(f"{categoria:<15} {conteo_final[categoria]:>3}/25")

    print(f"\nTotal de consultas: {len(consultas)}")
    print("Archivos JSON actualizados correctamente.")


# --------------------------------------------------
# 7. EJECUCIÓN
# --------------------------------------------------

if __name__ == "__main__":
    completar_dataset()
