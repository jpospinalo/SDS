#!/usr/bin/env python3
# ADVERTENCIA - script heredado (historico, no reproducible tal cual desde el repositorio).
# Fue escrito para una carpeta de trabajo plana (RAIZ = carpeta del script) que contenia un
# eval.csv y otros insumos propios. Ese eval.csv NO es data/processed/eval.csv: era una copia
# antigua de febrero. Se conserva como registro del metodo. Para reproducir la concordancia
# use:  python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv \
#         data/external/eval_2.csv data/external/eval_original.csv
"""
Selección de la submuestra para la validación externa del instrumento (kappa)
============================================================================
Manuscrito : Documentary Quality Assessment of Safety Data Sheets in the
             Colombian Paint Sector Using Data Analytics
Revista    : ACS Chemical Health & Safety — ID hs-2026-00106u

Qué hace este script
--------------------
1. Reconstruye los puntajes por sección y el puntaje global de las 50 FDS a
   partir de la matriz de codificación original (eval.csv).
2. Identifica las configuraciones documentales distintas: dos FDS comparten
   configuración cuando reciben calificación idéntica en los 71 ítems válidos.
3. Reproduce el agrupamiento jerárquico de Ward (k = 3) usado en el artículo.
4. Extrae una submuestra estratificada de 15 FDS para la doble codificación
   externa, maximizando la cobertura de configuraciones distintas.
5. Escribe la submuestra, la tabla de cobertura y las FDS de calibración.

Criterio de selección
---------------------
Un estudio de confiabilidad no busca una muestra representativa del corpus,
sino una que abarque el rango de situaciones de juicio que el instrumento debe
resolver. Incluir FDS con codificación idéntica repite los mismos juicios e
infla el acuerdo sin poner a prueba decisiones adicionales. Por eso la
asignación por celda prioriza configuraciones distintas, y la selección dentro
de cada celda es aleatoria con semilla fija para que sea reproducible y no
arbitraria.

Excepción deliberada: se incluyen dos FDS de F06 (una industrial y una
doméstica) que comparten configuración. Funcionan como prueba embebida de
consistencia intra-evaluador y deben declararse como tales en el manuscrito.

Uso
---
    python3 seleccion_submuestra_kappa.py [ruta/a/eval.csv]

Requiere: pandas, numpy, scipy
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage

SEMILLA = 2026
N_FDS = 50
PUNTOS = {"Confiable": 100, "Conf_CR": 50, "NO_Conf": 0}

# (fabricante, uso, nº de FDS a seleccionar)
PLAN = [
    ("F01", "IND", 2),   # 4 configuraciones disponibles
    ("F02", "HH", 2),    # 4 configuraciones disponibles
    ("F03", "IND", 2),   # 5 configuraciones disponibles
    ("F03", "HH", 2),    # 5 configuraciones disponibles
    ("F04", "IND", 2),   # 2 configuraciones: se toman ambas
    ("F05", "IND", 1),   # 2 configuraciones casi idénticas
    ("F07", "HH", 1),    # 2 configuraciones
    ("F08", "HH", 1),    # 1 sola configuración en 5 FDS
    ("F06", "IND", 1),   # 1 sola configuración en 10 FDS
    ("F06", "HH", 1),    # par deliberado: control intra-evaluador
]


def cargar(ruta: Path) -> pd.DataFrame:
    """Lee las 50 filas de datos de la matriz original."""
    df = pd.read_csv(ruta, sep=";", nrows=N_FDS, encoding="utf-8-sig")
    if len(df) != N_FDS:
        raise ValueError(f"Se esperaban {N_FDS} FDS y se leyeron {len(df)}")
    return df


def identificador(nombre: str) -> str:
    """'PRODUCTO 3 - INDUSTRIAL - FABRICANTE 1' -> 'F01-P03-I'."""
    import re

    prod = re.search(r"PRODUCTO\s*(\d+)", nombre, re.I)
    fab = re.search(r"FABRICANTE\s*(\d+)", nombre, re.I)
    uso = "I" if "INDUSTRIAL" in nombre.upper() else "D"
    return f"F0{fab.group(1)}-P0{prod.group(1)}-{uso}"


def construir_base(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Puntajes por sección, puntaje global, configuración y cluster."""
    # Ítems válidos: se excluyen los que quedan NO_APLICA en las 50 FDS.
    # Son la rama de sustancias puras de la Sección 3 (3_1_1 y subítems), que
    # nunca aplica porque los 50 productos del corpus son mezclas, más la
    # columna residual Calidad_3_5, que no tiene ítem correspondiente.
    calidad = [c for c in df.columns if c.lower().startswith("calidad_")]
    validos = [c for c in calidad if df[c].notna().any()]

    seccion = lambda c: int(c.split("_")[1])  # noqa: E731
    puntajes = {
        f"S{s}": df[[c for c in validos if seccion(c) == s]]
        .replace(PUNTOS)
        .mean(axis=1)
        for s in range(1, 17)
    }
    sec = pd.DataFrame(puntajes)

    base = pd.DataFrame(
        {
            "ID": df["Nombre del Producto"].apply(identificador),
            "FDS": df["FDS"],
            "Fab": df["Nombre del Producto"].str.extract(r"FABRICANTE\s*(\d)")[0].radd("F0"),
            "Uso": df["Uso"].map({"Industrial": "IND", "Domestica": "HH"}),
            "Fecha": df["Fecha Elaboración"],
            "Puntaje": sec.mean(axis=1).round(1),
        }
    )

    # Configuración documental: codificación idéntica en los 71 ítems válidos
    firma = df[validos].astype(str).agg("|".join, axis=1)
    base["Config"] = pd.factorize(firma)[0]

    # Agrupamiento de Ward sobre la matriz 50 x 16, como en el artículo
    enlace = linkage(sec.values, method="ward", metric="euclidean")
    base["Cluster"] = fcluster(enlace, 3, criterion="maxclust")

    return pd.concat([base, sec.round(1)], axis=1), validos


def seleccionar(base: pd.DataFrame) -> pd.DataFrame:
    """Selección estratificada, priorizando configuraciones no usadas."""
    rng = np.random.default_rng(SEMILLA)
    usadas: set[int] = set()
    elegidas: list[pd.Series] = []

    for fab, uso, k in PLAN:
        celda = base[(base.Fab == fab) & (base.Uso == uso)].sort_values("ID")
        disponibles = sorted(celda.Config.unique())

        nuevas = [c for c in disponibles if c not in usadas]
        escogidas = list(rng.choice(nuevas, size=min(k, len(nuevas)), replace=False))
        if len(escogidas) < k:  # celda sin configuraciones nuevas suficientes
            resto = [c for c in disponibles if c not in escogidas]
            faltan = k - len(escogidas)
            escogidas += list(rng.choice(resto, size=min(faltan, len(resto)), replace=False))
            escogidas += [escogidas[-1]] * (k - len(escogidas))

        tomadas: list[str] = []
        for cfg in escogidas[:k]:
            opciones = celda[(celda.Config == cfg) & (~celda.ID.isin(tomadas))].sort_values("ID")
            fila = opciones.iloc[rng.integers(len(opciones))]
            elegidas.append(fila)
            tomadas.append(fila.ID)
            usadas.add(cfg)

    return pd.DataFrame(elegidas).sort_values(["Fab", "Uso", "ID"]).reset_index(drop=True)


def cobertura(base: pd.DataFrame, sel: pd.DataFrame, validos: list[str], df: pd.DataFrame) -> pd.DataFrame:
    """Tabla de cobertura submuestra vs corpus, para el manuscrito."""
    sub = df.loc[base.ID.isin(sel.ID).values, validos]
    tot = df[validos]
    prop = lambda d, v: round(  # noqa: E731
        (pd.Series(d.values.ravel()).value_counts(normalize=True) * 100).get(v, 0.0), 1
    )

    filas = [
        ("FDS evaluadas", len(sel), N_FDS),
        ("Juicios por evaluador", len(sel) * len(validos), N_FDS * len(validos)),
        ("Fabricantes representados", sel.Fab.nunique(), base.Fab.nunique()),
        ("Configuraciones documentales", sel.Config.nunique(), base.Config.nunique()),
        ("FDS industriales", (sel.Uso == "IND").sum(), (base.Uso == "IND").sum()),
        ("FDS domésticas", (sel.Uso == "HH").sum(), (base.Uso == "HH").sum()),
        ("Cluster 1", (sel.Cluster == 1).sum(), (base.Cluster == 1).sum()),
        ("Cluster 2", (sel.Cluster == 2).sum(), (base.Cluster == 2).sum()),
        ("Cluster 3", (sel.Cluster == 3).sum(), (base.Cluster == 3).sum()),
        ("Puntaje mínimo", sel.Puntaje.min(), base.Puntaje.min()),
        ("Puntaje máximo", sel.Puntaje.max(), base.Puntaje.max()),
        ("Puntaje medio", round(sel.Puntaje.mean(), 1), round(base.Puntaje.mean(), 1)),
        ("% Confiable", prop(sub, "Confiable"), prop(tot, "Confiable")),
        ("% Confiable c/restricciones", prop(sub, "Conf_CR"), prop(tot, "Conf_CR")),
        ("% No confiable", prop(sub, "NO_Conf"), prop(tot, "NO_Conf")),
    ]
    return pd.DataFrame(filas, columns=["Indicador", "Submuestra", "Corpus"])


def calibracion(base: pd.DataFrame, sel: pd.DataFrame) -> pd.DataFrame:
    """Dos FDS fuera de la submuestra y con configuraciones no usadas."""
    resto = base[(~base.ID.isin(sel.ID)) & (~base.Config.isin(sel.Config))].sort_values("Puntaje")
    return resto.iloc[[1, len(resto) - 2]][["ID", "Fab", "Uso", "Puntaje", "Config"]]


def ordenes_de_codificacion(sel: pd.DataFrame, n_evaluadores: int = 2) -> pd.DataFrame:
    """Orden de codificación distinto e independiente para cada evaluador.

    Si ambos evaluadores codifican en la misma secuencia, los efectos de
    aprendizaje y de fatiga se alinean y inflan el acuerdo de forma espuria.
    """
    rng = np.random.default_rng(SEMILLA + 1)
    salida = pd.DataFrame({"Orden": range(1, len(sel) + 1)})
    for i in range(1, n_evaluadores + 1):
        salida[f"Evaluador_{i}"] = rng.permutation(sel.ID.values)
    return salida


def main() -> None:
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "eval.csv")
    df = cargar(ruta)
    base, validos = construir_base(df)

    print(f"Ítems con calificación válida: {len(validos)} de 75")
    print(f"Configuraciones documentales distintas: {base.Config.nunique()} en {N_FDS} FDS\n")

    print("Configuraciones distintas por fabricante")
    print(
        base.groupby("Fab")
        .agg(FDS=("ID", "size"), Configuraciones=("Config", "nunique"), SD=("Puntaje", "std"))
        .round(2)
        .to_string()
    )

    sel = seleccionar(base)
    cob = cobertura(base, sel, validos, df)
    cal = calibracion(base, sel)

    cols = ["ID", "FDS", "Fab", "Uso", "Fecha", "Puntaje", "Cluster", "Config"]
    print("\nSubmuestra seleccionada (semilla %d)" % SEMILLA)
    print(sel[cols].to_string(index=False))
    print("\nCobertura")
    print(cob.to_string(index=False))
    print("\nFDS de calibración (excluidas del cálculo del kappa)")
    print(cal.to_string(index=False))

    ordenes = ordenes_de_codificacion(sel)
    print("\nOrden de codificación por evaluador")
    print(ordenes.to_string(index=False))

    sec_cols = [f"S{i}" for i in range(1, 17)]
    sel[cols + sec_cols].to_csv("submuestra_kappa_15.csv", index=False)
    cob.to_csv("cobertura_submuestra.csv", index=False)
    cal.to_csv("fds_calibracion.csv", index=False)
    ordenes.to_csv("orden_codificacion.csv", index=False)
    base[cols + sec_cols].to_csv("puntajes_50_fds.csv", index=False)
    print("\nArchivos escritos: submuestra_kappa_15.csv, cobertura_submuestra.csv,")
    print("fds_calibracion.csv, orden_codificacion.csv, puntajes_50_fds.csv")


if __name__ == "__main__":
    main()
