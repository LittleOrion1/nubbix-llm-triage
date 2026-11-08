
#misma idea que paso8 

import sys 
import json 
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score 


#--------------------------------------------------
# 1. RUTAS Y CONFIGURACIÓN
#--------------------------------------------------

RUTA_PREDICCIONES = BASE_DIR / "data" / "predicciones_v2FewShot.json"
RUTA_ETIQUETAS = BASE_DIR /"data" / "etiquetas.json"

CATEGORIAS = [
    
    "billing",
    "technical",
    "account",
    "other"
]

#--------------------------------------
#2 . CARGA DE DATOS 
#--------------------------------------

def cargar_json(ruta):
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


#--------------------------------------
# 3. PREPARACION DE DATOS 
#--------------------------------------

def preparar_evaluacion(predicciones, etiquetas):

    y_true = []
    y_pred = []

    errores = []

    for prediccion in predicciones:

        id_consulta = prediccion["id"]

        # Ignoramos registros que no se procesaron correctamente.
        if prediccion.get("estado") != "ok":
            errores.append(id_consulta)
            continue

        # Recuperamos la etiqueta humana.
        categoria_real = etiquetas[id_consulta]["categoria"]

        # Recuperamos la predicción del modelo.
        categoria_predicha = prediccion["categoria_predicha"]

        y_true.append(categoria_real)
        y_pred.append(categoria_predicha)

    return y_true, y_pred, errores


# --------------------------------------------------
# 4. CÁLCULO DE MÉTRICAS
# --------------------------------------------------

def main():

    predicciones = cargar_json(RUTA_PREDICCIONES)
    etiquetas = cargar_json(RUTA_ETIQUETAS)

    y_true, y_pred, errores = preparar_evaluacion(
        predicciones,
        etiquetas
    )

    if not y_true:
        print("No hay predicciones válidas para evaluar.")
        return

    accuracy = accuracy_score(y_true, y_pred)

    matriz = confusion_matrix(
        y_true,
        y_pred,
        labels=CATEGORIAS
    )

    reporte = classification_report(
        y_true,
        y_pred,
        labels=CATEGORIAS,
        target_names=CATEGORIAS,
        zero_division=0
    )

    # --------------------------------------------------
    # 5. RESULTADOS
    # --------------------------------------------------

    print("=" * 60)
    print("EVALUACIÓN FEW-SHOT")
    print("=" * 60)

    print(f"\nConsultas evaluadas: {len(y_true)}")
    print(f"Registros con errores: {len(errores)}")

    print(f"\nAccuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    print("\nREPORTE DE CLASIFICACIÓN")
    print(reporte)

    print("MATRIZ DE CONFUSIÓN")
    print("Orden de categorías:", CATEGORIAS)
    print(matriz)

    if errores:
        print("\nCONSULTAS NO EVALUADAS:")
        print(errores)


if __name__ == "__main__":
    main()
