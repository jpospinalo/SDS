#!/usr/bin/env python3
# ADVERTENCIA - script heredado (historico, no reproducible tal cual desde el repositorio).
# Fue escrito para una carpeta de trabajo plana (RAIZ = carpeta del script) que contenia un
# eval.csv y otros insumos propios. Ese eval.csv NO es data/processed/eval.csv: era una copia
# antigua de febrero. Se conserva como registro del metodo. Para reproducir la concordancia
# use:  python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv \
#         data/external/eval_2.csv data/external/eval_original.csv
"""
Cumplimiento por ítem — insumo para la reestructuración sección por sección
===========================================================================
Manuscrito : ARTICULO ACHS · ACS Chemical Health & Safety · hs-2026-00106u

Para qué sirve
--------------
El Revisor 1 pidió que Resultados y Discusión se organicen por secciones del
SDS y evalúen críticamente qué falla dentro de cada una. Hoy el artículo solo
reporta el puntaje agregado por sección. Este script desagrega los 3 550 juicios
hasta el ítem individual, de modo que la extracción cualitativa sobre los PDF
sepa exactamente qué buscar en lugar de leer los documentos a ciegas.

Se aplica la regla de ítems ausentes fijada en Assessment Instrument (ausente =
no confiable) a los 27 casos ya resueltos; los 29 de la Sección 3 quedan a la
espera de la aclaración sobre secreto industrial y se marcan como tales.

Salidas
-------
  cumplimiento_por_item.csv   una fila por ítem: presencia, distribución de
                              calidad, puntaje medio y déficit
  items_criticos.csv          los 20 ítems con menor puntaje, que son los
                              candidatos naturales a ejemplo textual
  resumen_por_seccion.csv     ítems más y menos cumplidos de cada sección
"""

import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent
PUNTOS = {"Confiable": 100, "Conf_CR": 50, "NO_Conf": 0}
ITEMS_S3_PENDIENTES = {"3_2_1_1", "3_2_1_2", "3_2_1_3"}

SECCIONES = {
    1: "Product identification", 2: "Hazard identification", 3: "Composition / ingredients",
    4: "First-aid measures", 5: "Fire-fighting measures", 6: "Accidental release measures",
    7: "Handling and storage", 8: "Exposure controls / PPE", 9: "Physical and chemical properties",
    10: "Stability and reactivity", 11: "Toxicological information", 12: "Ecological information",
    13: "Disposal considerations", 14: "Transport information", 15: "Regulatory information",
    16: "Other information",
}

HERRAMIENTA = ("Anexo digital No. 1. Herramienta para verificación de los estándares de "
               "comunicación del peligro en las FDS.xlsx")
ALIAS = {f"10_2_{i}": f"10_{i}" for i in range(1, 7)}


def etiquetas() -> dict[str, str]:
    """Nombre de cada ítem, leído de las hojas de sección del instrumento."""
    import openpyxl

    wb = openpyxl.load_workbook(RAIZ / HERRAMIENTA, read_only=True, data_only=True)
    nombres: dict[str, str] = {}
    for hoja in wb.sheetnames:
        m = re.match(r"Secci[oó]n\s*(\d+)", hoja.strip())
        if not m:
            continue
        for orden, nombre in wb[hoja].iter_rows(min_row=7, max_col=2, values_only=True):
            if not isinstance(orden, str) or not nombre:
                continue
            orden = orden.strip().rstrip(".")
            if re.fullmatch(r"\d+(\.\d+)*", orden) and orden.split(".")[0] == m.group(1):
                nombres.setdefault(orden.replace(".", "_"), str(nombre).strip())
    return nombres


def main() -> None:
    df = pd.read_csv(RAIZ / "eval.csv", sep=";", nrows=50, encoding="utf-8-sig")
    nombres = etiquetas()
    codigos = [c.split("_", 1)[1] for c in df.columns
               if c.lower().startswith("calidad_") and df[c].notna().any()]

    filas = []
    for cod in codigos:
        presencia = df[f"Item_{cod}"]
        calidad = df[f"Calidad_{cod}"].copy()
        pendiente = cod in ITEMS_S3_PENDIENTES
        if not pendiente:  # regla de ítems ausentes ya resuelta
            calidad = calidad.mask(presencia == "No Present", "NO_Conf")
        conteo = calidad.value_counts()
        filas.append({
            "Sec": int(cod.split("_")[0]),
            "Item": cod.replace("_", "."),
            "Nombre": nombres.get(ALIAS.get(cod, cod), ""),
            "Presente_%": round((presencia == "Presente").mean() * 100, 1),
            "Confiable_%": round(conteo.get("Confiable", 0) / 50 * 100, 1),
            "ConRestric_%": round(conteo.get("Conf_CR", 0) / 50 * 100, 1),
            "NoConfiable_%": round(conteo.get("NO_Conf", 0) / 50 * 100, 1),
            "Puntaje": round(calidad.map(PUNTOS).mean(), 1),
            "Pendiente_S3": "sí" if pendiente else "",
        })

    items = pd.DataFrame(filas).sort_values(["Sec", "Item"])
    items["Seccion"] = items.Sec.map(SECCIONES)
    items["Brecha"] = (items["Presente_%"] - items["Puntaje"]).round(1)
    cols = ["Sec", "Seccion", "Item", "Nombre", "Presente_%", "Confiable_%", "ConRestric_%",
            "NoConfiable_%", "Puntaje", "Brecha", "Pendiente_S3"]
    items = items[cols]
    items.to_csv(RAIZ / "cumplimiento_por_item.csv", index=False)

    criticos = items.nsmallest(20, "Puntaje")
    criticos.to_csv(RAIZ / "items_criticos.csv", index=False)

    resumen = []
    for s, g in items.groupby("Sec"):
        peor, mejor = g.nsmallest(1, "Puntaje").iloc[0], g.nlargest(1, "Puntaje").iloc[0]
        resumen.append({
            "Sec": f"S{s}", "Seccion": SECCIONES[s], "Items": len(g),
            "Puntaje_seccion": round(g.Puntaje.mean(), 1),
            "Item_mas_deficiente": peor.Item, "Nombre_deficiente": peor.Nombre,
            "Puntaje_peor": peor.Puntaje,
            "Item_mejor": mejor.Item, "Puntaje_mejor": mejor.Puntaje,
            "Dispersion_intra": round(g.Puntaje.std(), 1),
        })
    pd.DataFrame(resumen).to_csv(RAIZ / "resumen_por_seccion.csv", index=False)

    print(f"Ítems evaluados: {len(items)}   FDS: 50   juicios: {len(items) * 50}\n")
    print("LOS 20 ÍTEMS MÁS DEFICIENTES — candidatos a ejemplo textual")
    print(criticos[["Item", "Nombre", "Presente_%", "Puntaje", "NoConfiable_%"]]
          .to_string(index=False, max_colwidth=52))
    print("\n\nPOR SECCIÓN — dónde se concentra el problema dentro de cada una")
    print(pd.DataFrame(resumen)[["Sec", "Puntaje_seccion", "Item_mas_deficiente",
                                 "Nombre_deficiente", "Puntaje_peor", "Dispersion_intra"]]
          .to_string(index=False, max_colwidth=46))


if __name__ == "__main__":
    main()
