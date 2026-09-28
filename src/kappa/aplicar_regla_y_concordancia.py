#!/usr/bin/env python3
# ADVERTENCIA - script heredado (historico, no reproducible tal cual desde el repositorio).
# Fue escrito para una carpeta de trabajo plana (RAIZ = carpeta del script) que contenia un
# eval.csv y otros insumos propios. Ese eval.csv NO es data/processed/eval.csv: era una copia
# antigua de febrero. Se conserva como registro del metodo. Para reproducir la concordancia
# use:  python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv \
#         data/external/eval_2.csv data/external/eval_original.csv
"""
Regla de ítems ausentes y análisis de concordancia
==================================================
Manuscrito : Documentary Quality Assessment of Safety Data Sheets in the
             Colombian Paint Sector Using Data Analytics
Revista    : ACS Chemical Health & Safety — ID hs-2026-00106u

REGLA FIJADA
------------
Cuando un elemento requerido no está presente, la completitud se registra como
AUSENTE y la calidad como NO CONFIABLE. Ambas dimensiones se registran siempre.
Es la regla que el manuscrito ya enuncia al definir UNRELIABLE ("section absent
or content not aligned with minimum GHS documentary requirements"), pero que el
instructivo del instrumento no explicitaba. Los dos evaluadores externos
llegaron por su cuenta a una regla distinta —dejar la calidad en blanco—, lo que
confirma que la omisión era real.

EXCEPCIÓN PENDIENTE (Sección 3)
-------------------------------
29 de los 56 casos afectados están en los ítems 3.2.1.1 a 3.2.1.3 (sinónimos,
CAS y rangos de concentración de la mezcla), concentrados en 11 FDS. La
hipótesis es que el codificador original los marcó AUSENTE pero CONFIABLE
porque la ficha declaraba secreto industrial conforme al GHS. Si se confirma,
el error está en la dimensión de presencia, no en la de calidad, y la
corrección es distinta.

Mientras se resuelve, el script informa dos escenarios:
  A  Sección 3 sin tocar (hipótesis de secreto industrial correcto).
  B  Sección 3 recodificada como los demás (hipótesis de error de codificación).
La diferencia entre A y B acota cuánto importa la respuesta pendiente.

SALIDAS
-------
  matriz_corregida.csv        eval.csv con la regla aplicada (escenario A)
  puntajes_50_corregidos.csv  puntajes por sección y global, escenarios A y B
  concordancia.csv            kappa y acuerdo por par y dimensión
  concordancia_por_seccion.csv
  matrices_confusion.txt
  casos_pendientes_s3.csv     los 29 casos a verificar contra los PDF

Uso
---
    python3 aplicar_regla_y_concordancia.py

Requiere: pandas, numpy, scikit-learn, krippendorff
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

RAIZ = Path(__file__).resolve().parent
KAPPA = RAIZ / "kappa"
SEMILLA = 2026
N_BOOT = 2000

ORDEN = ["NO_CONFIABLE", "CONFIABLE_CON_RESTRICCIONES", "CONFIABLE"]
PRESENTES = ["AUSENTE", "PRESENTE"]
CATEGORIAS = {"P": PRESENTES, "C": ORDEN}
CORTO = {"NO_CONFIABLE": "NoConf", "CONFIABLE_CON_RESTRICCIONES": "ConfCR", "CONFIABLE": "Conf"}
PUNTOS = {"Confiable": 100, "Conf_CR": 50, "NO_Conf": 0}
ITEMS_S3 = {"3_2_1_1", "3_2_1_2", "3_2_1_3"}


# --------------------------------------------------------------------------- #
# 1. Aplicación de la regla sobre la matriz original
# --------------------------------------------------------------------------- #
def identificador(nombre: str) -> str:
    return "F0{}-P0{}-{}".format(
        re.search(r"FABRICANTE\s*(\d+)", nombre, re.I).group(1),
        re.search(r"PRODUCTO\s*(\d+)", nombre, re.I).group(1),
        "I" if "INDUSTRIAL" in nombre.upper() else "D",
    )


def items_validos(df: pd.DataFrame) -> list[str]:
    """Códigos de ítem con calificación en al menos una FDS (71 de 75)."""
    return [
        c.split("_", 1)[1]
        for c in df.columns
        if c.lower().startswith("calidad_") and df[c].notna().any()
    ]


def casos_afectados(df: pd.DataFrame, codigos: list[str], ids: pd.Series) -> pd.DataFrame:
    """Ítems marcados ausentes pero calificados como algo distinto de NO_Conf."""
    filas = []
    for cod in codigos:
        marca = (df[f"Item_{cod}"] == "No Present") & (df[f"Calidad_{cod}"] != "NO_Conf")
        for i in df.index[marca]:
            filas.append(
                {
                    "FDS_ID": ids[i],
                    "SECCION": f"S{cod.split('_')[0]}",
                    "ITEM": cod.replace("_", "."),
                    "CALIDAD_ORIGINAL": df.loc[i, f"Calidad_{cod}"],
                    "GRUPO": "S3_PENDIENTE" if cod in ITEMS_S3 else "REGLA_DIRECTA",
                }
            )
    return pd.DataFrame(filas)


def aplicar_regla(df: pd.DataFrame, codigos: list[str], incluir_s3: bool) -> pd.DataFrame:
    d = df.copy()
    for cod in codigos:
        if cod in ITEMS_S3 and not incluir_s3:
            continue
        marca = d[f"Item_{cod}"] == "No Present"
        d.loc[marca, f"Calidad_{cod}"] = "NO_Conf"
    return d


def puntajes(df: pd.DataFrame, codigos: list[str]) -> tuple[pd.DataFrame, pd.Series]:
    sec = pd.DataFrame(
        {
            f"S{s}": df[[f"Calidad_{c}" for c in codigos if int(c.split("_")[0]) == s]]
            .replace(PUNTOS)
            .mean(axis=1)
            for s in range(1, 17)
        }
    )
    return sec, sec.mean(axis=1)


def categoria(x: pd.Series) -> pd.Series:
    return pd.cut(x, [-0.01, 33.3, 66.7, 100], labels=["NO_CONFIABLE", "CON_RESTR", "CONFIABLE"])


# --------------------------------------------------------------------------- #
# 2. Concordancia entre codificaciones
# --------------------------------------------------------------------------- #
def normalizar(d: pd.DataFrame, sufijo: str) -> pd.DataFrame:
    """Aplica la regla a una codificación en formato largo."""
    d = d[["FDS_ID", "ITEM", "PRESENCIA", "CALIDAD"]].copy()
    d.loc[d.PRESENCIA == "AUSENTE", "CALIDAD"] = "NO_CONFIABLE"
    return d.rename(columns={"PRESENCIA": f"P{sufijo}", "CALIDAD": f"C{sufijo}"})


def ic_bootstrap(datos: pd.DataFrame, a: str, b: str, ordinal: bool, cats: list[str]) -> tuple[float, float]:
    """IC 95 % por bootstrap de conglomerados: se remuestrean FDS, no ítems.

    Los ítems de una misma FDS no son independientes entre sí, así que
    remuestrear ítems subestimaría la incertidumbre.
    """
    rng = np.random.default_rng(SEMILLA)
    fds = datos.FDS_ID.unique()
    grupos = {f: datos[datos.FDS_ID == f] for f in fds}
    valores = []
    for _ in range(N_BOOT):
        muestra = pd.concat([grupos[f] for f in rng.choice(fds, len(fds), replace=True)])
        x = pd.Categorical(muestra[a], cats).codes
        y = pd.Categorical(muestra[b], cats).codes
        if len(set(x) | set(y)) < 2:
            continue
        valores.append(cohen_kappa_score(x, y, weights="linear" if ordinal else None))
    return (np.percentile(valores, 2.5), np.percentile(valores, 97.5)) if valores else (np.nan, np.nan)


def tabla_concordancia(m: pd.DataFrame) -> pd.DataFrame:
    pares = [("_1", "_2", "Evaluador 1 – Evaluador 2"),
             ("_1", "_O", "Evaluador 1 – Original"),
             ("_2", "_O", "Evaluador 2 – Original")]
    filas = []
    for dim, pref, ordinal in [("Completitud", "P", False), ("Calidad", "C", True)]:
        for s1, s2, nombre in pares:
            a, b = f"{pref}{s1}", f"{pref}{s2}"
            cats = CATEGORIAS[pref]
            x = pd.Categorical(m[a], cats).codes
            y = pd.Categorical(m[b], cats).codes
            lo, hi = ic_bootstrap(m, a, b, ordinal, cats)
            filas.append(
                {
                    "Dimension": dim,
                    "Par": nombre,
                    "n": len(m),
                    "Acuerdo_%": round(float(np.mean(np.asarray(x) == np.asarray(y)) * 100), 1),
                    "Kappa": round(cohen_kappa_score(x, y), 3),
                    "Kappa_ponderado": round(cohen_kappa_score(x, y, weights="linear"), 3) if ordinal else "",
                    "IC95_inf": round(lo, 3),
                    "IC95_sup": round(hi, 3),
                }
            )
    return pd.DataFrame(filas)


def tabla_por_seccion(m: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for s in [f"S{i}" for i in range(1, 17)]:
        g = m[m.SECCION == s]
        fila = {"Seccion": s, "n": len(g)}
        for s1, s2, et in [("_1", "_2", "E1_E2"), ("_1", "_O", "E1_Orig"), ("_2", "_O", "E2_Orig")]:
            x = pd.Categorical(g[f"C{s1}"], ORDEN).codes
            y = pd.Categorical(g[f"C{s2}"], ORDEN).codes
            fila[f"acuerdo_{et}_%"] = round(float((x == y).mean() * 100), 1)
            fila[f"kappa_{et}"] = (
                round(cohen_kappa_score(x, y, weights="linear"), 3)
                if len(set(x) | set(y)) > 1
                else np.nan
            )
        filas.append(fila)
    return pd.DataFrame(filas)


def alfa_krippendorff(m: pd.DataFrame, pref: str) -> float:
    import krippendorff

    datos = np.array(
        [pd.Categorical(m[f"{pref}{s}"], CATEGORIAS[pref]).codes for s in ("_O", "_1", "_2")],
        dtype=float,
    )
    nivel = "ordinal" if pref == "C" else "nominal"
    return float(krippendorff.alpha(reliability_data=datos, level_of_measurement=nivel))


def control_intrarater(cods: dict[str, pd.DataFrame], a: str, b: str) -> pd.DataFrame:
    """Par de F06: dos FDS con codificación original idéntica en los 71 ítems."""
    filas = []
    for nombre, d in cods.items():
        # Se aplica la regla antes de comparar: si no, los ítems que el
        # evaluador dejó en blanco cuentan como desacuerdo (NaN != NaN).
        d = d.copy()
        d.loc[d.PRESENCIA == "AUSENTE", "CALIDAD"] = "NO_CONFIABLE"
        x = d[d.FDS_ID == a].set_index("ITEM").sort_index()
        y = d[d.FDS_ID == b].set_index("ITEM").sort_index()
        filas.append(
            {
                "Codificacion": nombre,
                "Coincidencia_completitud_%": round(float((x.PRESENCIA == y.PRESENCIA).mean() * 100), 1),
                "Coincidencia_calidad_%": round(float((x.CALIDAD == y.CALIDAD).mean() * 100), 1),
            }
        )
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
def main() -> None:
    df = pd.read_csv(RAIZ / "eval.csv", sep=";", nrows=50, encoding="utf-8-sig")
    cods = items_validos(df)
    ids = df["Nombre del Producto"].apply(identificador)

    # --- Regla sobre la matriz -------------------------------------------- #
    afectados = casos_afectados(df, cods, ids)
    directos = (afectados.GRUPO == "REGLA_DIRECTA").sum()
    pendientes = (afectados.GRUPO == "S3_PENDIENTE").sum()

    print("REGLA DE ÍTEMS AUSENTES")
    print("=" * 70)
    print(f"Juicios evaluables            : {len(df) * len(cods)} ({len(df)} FDS x {len(cods)} ítems)")
    print(f"Casos afectados por la regla  : {len(afectados)} ({100*len(afectados)/(len(df)*len(cods)):.1f} %)")
    print(f"  recodificados ahora         : {directos}")
    print(f"  pendientes (Sección 3)      : {pendientes} en {afectados[afectados.GRUPO=='S3_PENDIENTE'].FDS_ID.nunique()} FDS")

    sec_orig, tot_orig = puntajes(df, cods)
    sec_a, tot_a = puntajes(aplicar_regla(df, cods, incluir_s3=False), cods)
    sec_b, tot_b = puntajes(aplicar_regla(df, cods, incluir_s3=True), cods)

    resumen = pd.DataFrame(
        {
            "Publicado": [tot_orig.mean(), tot_orig.std(), tot_orig.median(), tot_orig.min(), tot_orig.max()],
            "Escenario_A": [tot_a.mean(), tot_a.std(), tot_a.median(), tot_a.min(), tot_a.max()],
            "Escenario_B": [tot_b.mean(), tot_b.std(), tot_b.median(), tot_b.min(), tot_b.max()],
        },
        index=["Media", "SD", "Mediana", "Mínimo", "Máximo"],
    ).round(2)
    print("\nPuntaje global de las 50 FDS")
    print(resumen.to_string())

    cat = pd.DataFrame(
        {k: categoria(v).value_counts() for k, v in
         [("Publicado", tot_orig), ("Escenario_A", tot_a), ("Escenario_B", tot_b)]}
    )
    print("\nClasificación de las FDS")
    print(cat.to_string())
    print(f"\nFDS que cambian de categoría — A: {(categoria(tot_orig) != categoria(tot_a)).sum()}"
          f"   B: {(categoria(tot_orig) != categoria(tot_b)).sum()}")

    # --- Concordancia ------------------------------------------------------ #
    orig = pd.read_csv(KAPPA / "eval_original.csv")
    e1 = pd.read_csv(RAIZ / "ret_e1.csv")
    e2 = pd.read_csv(RAIZ / "ret_e2.csv")

    m = (
        normalizar(orig, "_O")
        .merge(normalizar(e1, "_1"), on=["FDS_ID", "ITEM"])
        .merge(normalizar(e2, "_2"), on=["FDS_ID", "ITEM"])
        .merge(orig[["FDS_ID", "ITEM", "SECCION"]], on=["FDS_ID", "ITEM"])
    )

    conc = tabla_concordancia(m)
    print("\n\nCONCORDANCIA ENTRE CODIFICACIONES (regla aplicada, n = %d)" % len(m))
    print("=" * 70)
    print(conc.to_string(index=False))
    print(f"\nAlfa de Krippendorff, 3 codificaciones — completitud (nominal): {alfa_krippendorff(m, 'P'):.3f}")
    print(f"Alfa de Krippendorff, 3 codificaciones — calidad (ordinal)   : {alfa_krippendorff(m, 'C'):.3f}")

    por_sec = tabla_por_seccion(m)
    print("\nCalidad por sección")
    print(por_sec.to_string(index=False))

    ctrl = control_intrarater(
        {"Original": orig, "Evaluador 1": e1, "Evaluador 2": e2}, "F06-P01-I", "F06-P05-D"
    )
    print("\nControl intra-evaluador — par F06 (codificación original idéntica)")
    print(ctrl.to_string(index=False))

    # --- Matrices de confusión -------------------------------------------- #
    lineas = ["MATRICES DE CONFUSIÓN — dimensión calidad", "=" * 70, ""]
    for s1, s2, nombre in [("_1", "_2", "Evaluador 1 (filas) x Evaluador 2 (columnas)"),
                           ("_1", "_O", "Evaluador 1 (filas) x Original (columnas)"),
                           ("_2", "_O", "Evaluador 2 (filas) x Original (columnas)")]:
        cm = confusion_matrix(m[f"C{s1}"], m[f"C{s2}"], labels=ORDEN)
        etiquetas = [CORTO[o] for o in ORDEN]
        lineas += [nombre, pd.DataFrame(cm, index=etiquetas, columns=etiquetas).to_string(), ""]
    (RAIZ / "matrices_confusion.txt").write_text("\n".join(lineas), encoding="utf-8")

    # --- Escritura --------------------------------------------------------- #
    corregida = aplicar_regla(df, cods, incluir_s3=False)
    corregida.insert(0, "FDS_ID", ids)
    corregida.to_csv(RAIZ / "matriz_corregida.csv", index=False, sep=";")

    pd.concat(
        [
            pd.DataFrame({"FDS_ID": ids, "Publicado": tot_orig.round(2),
                          "Escenario_A": tot_a.round(2), "Escenario_B": tot_b.round(2)}),
            sec_a.round(2).add_suffix("_A"),
        ],
        axis=1,
    ).to_csv(RAIZ / "puntajes_50_corregidos.csv", index=False)

    conc.to_csv(RAIZ / "concordancia.csv", index=False)
    por_sec.to_csv(RAIZ / "concordancia_por_seccion.csv", index=False)
    afectados[afectados.GRUPO == "S3_PENDIENTE"].to_csv(RAIZ / "casos_pendientes_s3.csv", index=False)

    print("\n\nArchivos escritos: matriz_corregida.csv, puntajes_50_corregidos.csv,")
    print("concordancia.csv, concordancia_por_seccion.csv, matrices_confusion.txt,")
    print("casos_pendientes_s3.csv")


if __name__ == "__main__":
    main()
