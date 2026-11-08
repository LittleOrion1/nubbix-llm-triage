import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from M1P1.datos import cargar_consultas, cargar_etiquetas
from M1P1.prompts import CATEGORIAS
from pasos.comun import titulo


def main() -> None:
    consultas = cargar_consultas()
    etiquetas = cargar_etiquetas()

    # 4.1 Categorías
    titulo("4.1 Categorías de clasificación")

    for nombre, descripcion in CATEGORIAS.items():
        print(f"  {nombre:<22} {descripcion}")

    # 4.2 Validación de etiquetas
    titulo("\n4.2 Validación de las etiquetas")

    ids_consultas = {c["id"] for c in consultas}
    ids_etiquetas = set(etiquetas.keys())

    faltan = sorted(ids_consultas - ids_etiquetas)
    sobrantes = sorted(ids_etiquetas - ids_consultas)

    invalidas = [
        id_
        for id_, etiqueta in etiquetas.items()
        if not isinstance(etiqueta, dict)
        or etiqueta.get("categoria") not in CATEGORIAS
    ]

    print(f"  Consultas sin etiqueta: {faltan or 'ninguna'}")
    print(f"  Etiquetas sobrantes: {sobrantes or 'ninguna'}")
    print(f"  Categorías inválidas: {invalidas or 'ninguna'}")

    # 4.3 Dataset etiquetado
    titulo("\n4.3 Dataset etiquetado")

    for consulta in consultas:
        id_ = consulta["id"]
        etiqueta = etiquetas.get(id_)

        if not isinstance(etiqueta, dict):
            print(f"  {id_} [SIN ETIQUETA] {consulta['texto'][:60]}")
            continue

        categoria = etiqueta.get("categoria", "SIN CATEGORÍA")
        regla = etiqueta.get("regla")
        marca = f"[{regla}]" if regla else "    "

        print(
            f"  {id_} {marca} {categoria:<22} "
            f"{consulta['texto'][:60]}"
        )

    # 4.4 Distribución por categoría
    titulo("\n4.4 Distribución por categoría")

    conteo = Counter(
        etiqueta["categoria"]
        for etiqueta in etiquetas.values()
        if isinstance(etiqueta, dict)
        and etiqueta.get("categoria") in CATEGORIAS
        and etiqueta.get("id") is None
    )

    # Contar únicamente las etiquetas correspondientes a consultas existentes.
    conteo = Counter(
        etiquetas[c["id"]]["categoria"]
        for c in consultas
        if c["id"] in etiquetas
        and isinstance(etiquetas[c["id"]], dict)
        and etiquetas[c["id"]].get("categoria") in CATEGORIAS
    )

    total = sum(conteo.values())

    for categoria in CATEGORIAS:
        cantidad = conteo.get(categoria, 0)
        porcentaje = cantidad / total * 100 if total else 0
        print(f"  {categoria:<22} {cantidad:>3} ({porcentaje:5.1f} %)")

    print(f"\n  Total de consultas etiquetadas válidamente: {total}")

    # 4.5 Casos con reglas especiales
    titulo("\n4.5 Casos ambiguos o con reglas especiales")

    encontrados = False

    for consulta in consultas:
        etiqueta = etiquetas.get(consulta["id"])

        if isinstance(etiqueta, dict) and etiqueta.get("regla"):
            encontrados = True
            print(
                f"  {consulta['id']} "
                f"{etiqueta['regla']} → "
                f"{etiqueta.get('categoria')} "
                f"{etiqueta.get('justificacion', '')}"
            )

    if not encontrados:
        print("  No hay casos con reglas especiales registrados.")


if __name__ == "__main__":
    main()