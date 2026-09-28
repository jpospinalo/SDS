#!/usr/bin/env python3
"""Audita el impacto de correcciones de presencia sobre los resultados publicados.

La calidad se mantiene inalterada. El script recalcula completitud por item,
seccion y dominio, las brechas completitud-calidad y las correlaciones de
Spearman usadas en el manuscrito. Tambien comprueba que las combinaciones
AUSENTE + calidad positiva se limiten a la confidencialidad de S3.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


MAP_Q = {
    "NO_CONFIABLE": 0.0,
    "CONFI_RESTR": 1.0,
    "CONFIABLE": 2.0,
    "NO_APLICA": np.nan,
}

DOMINIOS = {
    "G1": [1, 2, 3],
    "G2": [4, 5, 6],
    "G3": [7, 8],
    "G4": [9, 10, 11, 12],
    "G5": [13, 14, 15, 16],
}


def columnas_evaluables(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    items = [c for c in df.columns if c.startswith("ITEM_") and "ITEM_3_1_" not in c]
    calidad = [c for c in df.columns if c.startswith("CALIDAD_") and "CALIDAD_3_1_" not in c]
    return items, calidad


def seccion(columna: str) -> int:
    coincidencia = re.match(r"(?:ITEM|CALIDAD)_(\d+)_", columna)
    if not coincidencia:
        raise ValueError(f"Columna sin seccion reconocible: {columna}")
    return int(coincidencia.group(1))


def calcular(path: Path, validar_excepciones: bool = True) -> dict:
    df = pd.read_csv(path)
    items, calidad = columnas_evaluables(df)
    assert len(df) == 50
    assert len(items) == 71
    assert len(calidad) == 71

    filas_seccion = []
    filas_item = []

    for sec in range(1, 17):
        icols = [c for c in items if seccion(c) == sec]
        qcols = [c for c in calidad if seccion(c) == sec]

        item_values = df[icols]
        denominador = item_values.isin(["PRESENTE", "AUSENTE"]).to_numpy().sum()
        presentes = item_values.eq("PRESENTE").to_numpy().sum()
        completitud = presentes / denominador * 100

        q_num = df[qcols].replace(MAP_Q).apply(pd.to_numeric, errors="coerce")
        calidad_seccion = q_num.mean(axis=1, skipna=True).mean() * 50

        filas_seccion.append(
            {
                "seccion": sec,
                "n_items": len(icols),
                "calidad": calidad_seccion,
                "completitud": completitud,
                "brecha": completitud - calidad_seccion,
            }
        )

    for icol in items:
        sufijo = icol.removeprefix("ITEM_")
        qcol = f"CALIDAD_{sufijo}"
        validos = df[icol].isin(["PRESENTE", "AUSENTE"])
        completitud = df.loc[validos, icol].eq("PRESENTE").mean() * 100
        q_num = pd.to_numeric(df[qcol].replace(MAP_Q), errors="coerce")
        calidad_item = q_num.mean(skipna=True) * 50
        filas_item.append(
            {
                "item": sufijo.replace("_", "."),
                "seccion": int(sufijo.split("_")[0]),
                "calidad": calidad_item,
                "completitud": completitud,
                "brecha": completitud - calidad_item,
            }
        )

    sec_df = pd.DataFrame(filas_seccion)
    item_df = pd.DataFrame(filas_item)
    rho_sec, p_sec = spearmanr(sec_df["completitud"], sec_df["calidad"])
    rho_item, p_item = spearmanr(item_df["completitud"], item_df["calidad"])

    dominios = []
    for codigo, secciones in DOMINIOS.items():
        subconjunto = sec_df[sec_df["seccion"].isin(secciones)]
        calidad_dominio = subconjunto["calidad"].mean()
        completitud_dominio = subconjunto["completitud"].mean()
        dominios.append(
            {
                "dominio": codigo,
                "calidad": calidad_dominio,
                "completitud": completitud_dominio,
                "brecha": completitud_dominio - calidad_dominio,
            }
        )

    excepciones = []
    for icol in items:
        sufijo = icol.removeprefix("ITEM_")
        qcol = f"CALIDAD_{sufijo}"
        mascara = df[icol].eq("AUSENTE") & df[qcol].isin(["CONFI_RESTR", "CONFIABLE"])
        for _, fila in df.loc[mascara, ["ID", icol, qcol]].iterrows():
            excepciones.append(
                {
                    "id": fila["ID"],
                    "item": sufijo.replace("_", "."),
                    "presencia": fila[icol],
                    "calidad": fila[qcol],
                }
            )

    conf = [x for x in excepciones if x["item"] in {"3.2.1.1", "3.2.1.2", "3.2.1.3"}]
    if validar_excepciones:
        assert len(excepciones) == 29
        assert len(conf) == 29
        assert len(conf) == len(excepciones)

    return {
        "archivo": str(path),
        "secciones": sec_df,
        "items": item_df,
        "dominios": pd.DataFrame(dominios),
        "correlaciones": {
            "secciones": {"rho": float(rho_sec), "p": float(p_sec), "n": 16},
            "items": {"rho": float(rho_item), "p": float(p_item), "n": 71},
        },
        "excepciones": excepciones,
    }


def diferencias(antes: dict, despues: dict, clave: str, llave: str) -> pd.DataFrame:
    a = antes[clave].set_index(llave)
    d = despues[clave].set_index(llave)
    filas = []
    for indice in a.index:
        for metrica in ["calidad", "completitud", "brecha"]:
            va = float(a.loc[indice, metrica])
            vd = float(d.loc[indice, metrica])
            if not np.isclose(va, vd, atol=1e-12):
                filas.append(
                    {
                        llave: indice,
                        "metrica": metrica,
                        "antes": va,
                        "despues": vd,
                        "cambio": vd - va,
                    }
                )
    return pd.DataFrame(filas)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("actual", type=Path)
    parser.add_argument("--antes", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()

    args.salida.mkdir(parents=True, exist_ok=True)
    actual = calcular(args.actual)

    actual["secciones"].to_csv(args.salida / "secciones_recalculadas.csv", index=False)
    actual["items"].to_csv(args.salida / "items_recalculados.csv", index=False)
    actual["dominios"].to_csv(args.salida / "dominios_recalculados.csv", index=False)
    pd.DataFrame(actual["excepciones"]).to_csv(args.salida / "excepciones_confidencialidad.csv", index=False)

    resumen = {
        "archivo": actual["archivo"],
        "correlaciones": actual["correlaciones"],
        "excepciones": {
            "total": len(actual["excepciones"]),
            "confidencialidad_s3": 29,
        },
    }

    if args.antes:
        antes = calcular(args.antes, validar_excepciones=False)
        dif_sec = diferencias(antes, actual, "secciones", "seccion")
        dif_item = diferencias(antes, actual, "items", "item")
        dif_dom = diferencias(antes, actual, "dominios", "dominio")
        dif_sec.to_csv(args.salida / "cambios_secciones.csv", index=False)
        dif_item.to_csv(args.salida / "cambios_items.csv", index=False)
        dif_dom.to_csv(args.salida / "cambios_dominios.csv", index=False)
        resumen["correlaciones_antes"] = antes["correlaciones"]
        resumen["cambios"] = {
            "secciones": len(dif_sec),
            "items": len(dif_item),
            "dominios": len(dif_dom),
        }

    with (args.salida / "resumen_auditoria.json").open("w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=2)

    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
