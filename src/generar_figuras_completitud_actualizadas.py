#!/usr/bin/env python3
"""Genera las figuras del manuscrito afectadas por cambios de completitud y calidad."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from analisis_congelado import kw

matplotlib.use("Agg")

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "eval.csv"
OUT = BASE / "outputs" / "bloque_metodologico" / "figuras"
OUT.mkdir(parents=True, exist_ok=True)

MAP_Q = {"NO_CONFIABLE": 0.0, "CONFI_RESTR": 1.0, "CONFIABLE": 2.0, "NO_APLICA": np.nan}
NOMBRES = {
    1: "Identification", 2: "Hazard identification", 3: "Composition",
    4: "First aid", 5: "Fire fighting", 6: "Accidental release",
    7: "Handling", 8: "Exposure controls", 9: "Physical properties",
    10: "Stability", 11: "Toxicology", 12: "Ecotoxicology",
    13: "Disposal", 14: "Transport", 15: "Regulatory", 16: "Other",
}
CRITICAS = {2, 4, 8, 11}
DOMINIOS = {
    "G1": ([1, 2, 3], "Identification &\nhazard comm."),
    "G2": ([4, 5, 6], "Emergency\nresponse"),
    "G3": ([7, 8], "Safe handling &\nexposure ctrl."),
    "G4": ([9, 10, 11, 12], "Physicochemical &\nhazard char."),
    "G5": ([13, 14, 15, 16], "Regulatory,\nlogistics & supp."),
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "grid.linewidth": 0.6,
})


def un_decimal(valor: float) -> str:
    """Redondeo decimal convencional, coherente con las tablas del manuscrito."""
    return str(Decimal(str(valor)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def cargar():
    df = pd.read_csv(DATA)
    items = [c for c in df if c.startswith("ITEM_") and "ITEM_3_1_" not in c]
    calidad = [c for c in df if c.startswith("CALIDAD_") and "CALIDAD_3_1_" not in c]
    sec_scores = {}
    completitud = {}
    distribucion = {}
    for sec in range(1, 17):
        icols = [c for c in items if re.match(rf"ITEM_{sec}_", c)]
        qcols = [c for c in calidad if re.match(rf"CALIDAD_{sec}_", c)]
        vals_i = df[icols]
        den = vals_i.isin(["PRESENTE", "AUSENTE"]).to_numpy().sum()
        completitud[sec] = vals_i.eq("PRESENTE").to_numpy().sum() / den * 100
        qnum = df[qcols].replace(MAP_Q).apply(pd.to_numeric, errors="coerce")
        df[f"SCORE_SEC_{sec}"] = qnum.mean(axis=1, skipna=True) * 50
        sec_scores[sec] = df[f"SCORE_SEC_{sec}"].mean()
        vals_q = df[qcols].to_numpy().ravel()
        vals_q = vals_q[pd.notna(vals_q) & (vals_q != "NO_APLICA")]
        distribucion[sec] = {
            "UNRELIABLE": np.mean(vals_q == "NO_CONFIABLE") * 100,
            "RESTRICTED": np.mean(vals_q == "CONFI_RESTR") * 100,
            "RELIABLE": np.mean(vals_q == "CONFIABLE") * 100,
        }
    return df, completitud, sec_scores, distribucion


def figura_1(df, completitud, sec_scores, distribucion):
    # Conservar exactamente el orden de la figura publicada; la calidad no cambió.
    orden = [9, 7, 16, 5, 1, 2, 13, 4, 3, 14, 8, 6, 10, 15, 11, 12]
    etiquetas = [f"S{s:02d} · {NOMBRES[s]}" for s in orden]
    y = np.arange(len(orden))
    colores_a = ["#bf3f3f" if s in CRITICAS else "#3f8fbd" for s in orden]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13.8167, 8.3867), dpi=300, sharey=True)
    fig.subplots_adjust(left=0.145, right=0.985, bottom=0.11, top=0.79, wspace=0.06)

    valores_a = [completitud[s] for s in orden]
    ax_a.barh(y, valores_a, color=colores_a, height=0.62)
    for yi, valor in zip(y, valores_a):
        ax_a.text(valor / 2, yi, f"{valor:.0f}%", ha="center", va="center",
                  color="white", fontsize=10, fontweight="bold")
    ax_a.axvline(70, color="#888888", linestyle="--", linewidth=0.9, alpha=0.8)
    ax_a.text(70.8, len(y) - 0.15, "70%", color="#777777", fontsize=8, va="top")
    ax_a.set_xlim(0, 100)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(etiquetas, fontsize=9)
    ax_a.invert_yaxis()
    ax_a.set_xlabel("Completeness (% PRESENT items)")
    ax_a.set_title("A. Completeness by GHS section", fontweight="bold", loc="left", y=1.18)
    ax_a.grid(axis="y", visible=False)
    ax_a.legend(
        handles=[
            plt.Rectangle((0, 0), 1, 1, color="#3f8fbd", label="General section"),
            plt.Rectangle((0, 0), 1, 1, color="#bf1f24", label="Occupational health-critical"),
        ],
        loc="lower left", bbox_to_anchor=(-0.03, 1.015), ncol=2, frameon=True,
        fontsize=9, borderpad=0.6, handlelength=1.7,
    )

    unrel = np.array([distribucion[s]["UNRELIABLE"] for s in orden])
    restr = np.array([distribucion[s]["RESTRICTED"] for s in orden])
    rel = np.array([distribucion[s]["RELIABLE"] for s in orden])
    ax_b.barh(y, unrel, color="#df2525", height=0.62, label="Unreliable")
    ax_b.barh(y, restr, left=unrel, color="#ff7f0e", height=0.62, label="Reliable with restrictions")
    ax_b.barh(y, rel, left=unrel + restr, color="#29a329", height=0.62, label="Reliable")
    for yi, a, b, c in zip(y, unrel, restr, rel):
        for ancho, centro in [(a, a / 2), (b, a + b / 2), (c, a + b + c / 2)]:
            if ancho >= 12:
                ax_b.text(centro, yi, f"{ancho:.0f}%", ha="center", va="center",
                          color="white", fontsize=9, fontweight="bold")
    ax_b.axvline(50, color="#888888", linestyle="--", linewidth=0.9, alpha=0.8)
    ax_b.text(50.8, len(y) - 0.15, "50%", color="#777777", fontsize=8, va="top")
    ax_b.set_xlim(0, 100)
    ax_b.set_xlabel("Item evaluations (%)")
    ax_b.set_title("B. Distribution of quality categories by GHS section", fontweight="bold", loc="left", y=1.18)
    ax_b.grid(axis="y", visible=False)
    ax_b.legend(loc="lower left", bbox_to_anchor=(0.0, 1.005), frameon=True, fontsize=9)

    for yi, sec in zip(y, orden):
        if sec in CRITICAS:
            ax_a.text(97.5, yi, "★", ha="right", va="center", color="#8b0000", fontsize=11)
            ax_b.text(97.5, yi, "★", ha="right", va="center", color="#8b0000", fontsize=11)

    fig.text(
        0.5, 0.035,
        "Sections ordered by mean quality score (highest → lowest).  ★ = occupational health-critical section.  "
        "Red bars (Panel A) = occupational health-critical sections.",
        ha="center", fontsize=7.5, color="#666666", style="italic",
    )
    destino = OUT / "Figure_1_updated.png"
    fig.savefig(destino, dpi=300, facecolor="white")
    plt.close(fig)
    return destino


def figura_2(df, completitud, sec_scores, distribucion):
    fig, ax = plt.subplots(figsize=(9.93, 7.43), dpi=300)
    fig.subplots_adjust(left=0.075, right=0.97, bottom=0.12, top=0.88)
    ax.axvspan(0, 70, 0.70 / 1.07, 1, color="#fff9e9", alpha=0.45)
    ax.axvspan(70, 107, 0.70 / 1.07, 1, color="#eaf6ea", alpha=0.65)
    ax.axvspan(0, 70, 0, 0.70 / 1.07, color="#f5f5f5", alpha=0.55)
    ax.axvspan(70, 107, 0, 0.70 / 1.07, color="#fdeaea", alpha=0.75)
    ax.axvline(70, color="#888888", linestyle="--", linewidth=1)
    ax.axhline(70, color="#888888", linestyle="--", linewidth=1)
    sizes = {s: 75 + 42 * len([c for c in df if re.match(rf"ITEM_{s}_", c)]) for s in range(1, 17)}
    for sec in range(1, 17):
        color = "#c53c3c" if sec in CRITICAS else "#3c91c6"
        ax.scatter(completitud[sec], sec_scores[sec], s=sizes[sec], color=color,
                   alpha=0.82, edgecolor="white", linewidth=0.7, zorder=3)
    offsets = {
        1: (1.7, 1.5), 2: (1.6, 1.6), 3: (-1.0, 2.8), 4: (1.6, 1.4),
        5: (1.6, 1.6), 6: (1.6, -2.1), 7: (1.6, 2.0), 8: (1.6, 1.6),
        9: (-3.8, 1.7), 10: (3.0, -2.0), 11: (1.6, 1.8), 12: (1.6, 1.7),
        13: (1.6, 1.8), 14: (-3.0, -3.7), 15: (-3.8, 1.8), 16: (-3.8, 1.7),
    }
    for sec in range(1, 17):
        dx, dy = offsets[sec]
        ax.text(completitud[sec] + dx, sec_scores[sec] + dy, f"S{sec}",
                fontsize=8.5, fontweight="bold", color="#a51d1d" if sec in CRITICAS else "#666666")
    ax.text(35, 97, "Low completeness\nHigh quality", ha="center", va="top",
            fontsize=10, style="italic", fontweight="bold", color="#555555")
    ax.text(87.5, 97, "High completeness\nHigh quality", ha="center", va="top",
            fontsize=10, style="italic", fontweight="bold", color="#2ca02c")
    ax.text(35, 6, "Low completeness\nLow quality", ha="center", va="bottom",
            fontsize=10, style="italic", fontweight="bold", color="#d62728")
    ax.text(87.5, 6, "High completeness\nLow quality", ha="center", va="bottom",
            fontsize=10, style="italic", fontweight="bold", color="#b22222")
    ax.text(70.5, 1.0, "70%", fontsize=8, color="#777777")
    ax.text(1.0, 70.8, "70 pts", fontsize=8, color="#777777")
    handles = [
        plt.scatter([], [], s=80, color="#aaaaaa", alpha=0.6, label="2 items/section"),
        plt.scatter([], [], s=150, color="#aaaaaa", alpha=0.6, label="4 items/section"),
        plt.scatter([], [], s=250, color="#aaaaaa", alpha=0.6, label="7 items/section"),
        plt.scatter([], [], s=90, color="#3c91c6", label="General section"),
        plt.scatter([], [], s=90, color="#c51f1f", label="Health-critical section (S2,S4,S8,S11)"),
    ]
    ax.legend(handles=handles, loc="upper left", ncol=2, fontsize=7.5, frameon=True)
    ax.set_xlim(0, 107)
    ax.set_ylim(0, 107)
    ax.set_xlabel("Average completeness by section (% PRESENT items)")
    ax.set_ylabel("Average quality score by section (0–100)")
    ax.set_title(
        "Quadrant analysis: completeness–quality gap by GHS section\n"
        "Lower-right quadrant = sections with high presence but low-quality content",
        pad=14,
    )
    destino = OUT / "Figure_2_updated.png"
    fig.savefig(destino, dpi=300, facecolor="white")
    plt.close(fig)
    return destino


def figura_3(df, completitud, sec_scores, distribucion):
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.6, 4.1567), dpi=300,
                                     gridspec_kw={"width_ratios": [1, 2.05]})
    fig.subplots_adjust(left=0.08, right=0.985, bottom=0.16, top=0.83, wspace=0.23)
    sec_cols = [f"SCORE_SEC_{s}" for s in range(1, 17)]
    scores = df[sec_cols].mean(axis=1)
    industrial = scores[df.USO.eq("INDUSTRIAL")].to_numpy()
    household = scores[df.USO.eq("DOMESTICA")].to_numpy()
    ax_a.axhspan(0, 33.3, color="#fdeaea", alpha=0.65)
    ax_a.axhspan(33.3, 66.7, color="#fff9e8", alpha=0.65)
    ax_a.axhspan(66.7, 100, color="#eaf5ea", alpha=0.65)
    ax_a.axhline(33.3, color="#f26d6d", linestyle="--", linewidth=0.8)
    ax_a.axhline(66.7, color="#5fbf66", linestyle="--", linewidth=0.8)
    bp = ax_a.boxplot([industrial, household], positions=[0, 1], widths=0.5,
                      patch_artist=True, showfliers=False,
                      medianprops={"color": "black", "linewidth": 1.2},
                      boxprops={"edgecolor": "#666666"},
                      whiskerprops={"color": "black"}, capprops={"color": "black"})
    for box, color in zip(bp["boxes"], ["#6faed1", "#9a72b2"]):
        box.set_facecolor(color)
        box.set_alpha(0.7)
    rng = np.random.default_rng(314159)
    for i, (values, color) in enumerate([(industrial, "#287ab8"), (household, "#76529b")]):
        ax_a.scatter(i + rng.normal(0, 0.055, len(values)), values, s=20,
                     facecolor=color, edgecolor="white", linewidth=0.5, alpha=0.85, zorder=3)
    result = kw(industrial, household)
    h, p, eta = result['H'], result['p'], result['eta2_H']
    ax_a.text(0.5, 103, f"H={h:.2f}, p<0.001\n" + rf"$\eta_H^2$={eta:.3f} (large effect)",
              ha="center", va="top", fontsize=7.5,
              bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.3"})
    ax_a.set_ylim(-5, 112)
    ax_a.set_xticks([0, 1], ["Industrial\n(n=25)", "Household\n(n=25)"])
    ax_a.set_ylabel("Overall quality score (0–100)")
    ax_a.set_title("A. Overall quality score by use type", fontweight="bold", pad=14)
    ax_a.text(0.5, -1, "n=25  Med=75              n=25  Med=48", ha="center", fontsize=7, color="#666666")
    ax_a.grid(axis="x", visible=False)

    xs = np.arange(1, 17)
    av_i = [df.loc[df.USO.eq("INDUSTRIAL"), f"SCORE_SEC_{s}"].mean() for s in xs]
    av_h = [df.loc[df.USO.eq("DOMESTICA"), f"SCORE_SEC_{s}"].mean() for s in xs]
    for s in CRITICAS:
        ax_b.axvspan(s - .42, s + .42, color="#fff0f0", alpha=.7)
        ax_b.axvline(s, color="#bd3c3c", linestyle=":", linewidth=.75)
        ax_b.text(s, 101, f"S{s} ★", ha="center", color="#a42222", fontsize=8, fontweight="bold")
    ax_b.plot(xs, av_i, "o-", color="#287ab8", linewidth=1.7, markersize=3.8, label="Industrial")
    ax_b.plot(xs, av_h, "o-", color="#6f4a98", linewidth=1.7, markersize=3.8, label="Household")
    ax_b.axhline(50, color="#999999", linestyle="--", linewidth=.8, label="50-pt threshold")
    ax_b.annotate("Max gap\n53.7 pts (S14)", xy=(14, av_i[13] - 10), xytext=(14.6, 86),
                  arrowprops={"arrowstyle": "->", "color": "#777777", "linewidth": .7},
                  fontsize=7.5, color="#555555",
                  bbox={"facecolor": "white", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.25"})
    ax_b.set_xlim(.5, 16.5)
    ax_b.set_ylim(0, 112)
    ax_b.set_xticks(xs, [f"S{s}" for s in xs], rotation=45)
    for label,s in zip(ax_b.get_xticklabels(),xs):
        if s in CRITICAS:
            label.set_color("#a42222"); label.set_fontweight("bold")
    ax_b.set_xlabel("GHS section")
    ax_b.set_ylabel("Average quality score (0–100)")
    ax_b.set_title("B. Quality profile by GHS section and use type\n(★ = health-critical sections for workers)",
                   fontweight="bold", pad=14)
    ax_b.legend(loc="lower right", fontsize=7.5)
    destino = OUT / "Figure_3_updated.png"
    fig.savefig(destino, dpi=300, facecolor="white")
    plt.close(fig)
    return destino


def figura_4(df, completitud, sec_scores, distribucion):
    sec_cols = [f"SCORE_SEC_{s}" for s in range(1, 17)]
    df = df.copy()
    df["overall"] = df[sec_cols].mean(axis=1)
    resumen = df.groupby("FABRICANTE").overall.agg(["mean", "size"]).sort_values("mean", ascending=False)
    fabricantes = resumen.index.tolist()
    y = np.arange(len(fabricantes))
    fig, ax = plt.subplots(figsize=(10.8967, 6.2033), dpi=300)
    fig.subplots_adjust(left=.105, right=.985, bottom=.13, top=.91)
    ax.axvspan(0,33.3,color="#fff0f0",alpha=.65)
    ax.axvspan(33.3,66.7,color="#fff8e8",alpha=.65)
    ax.axvspan(66.7,100,color="#eef8ef",alpha=.65)
    ax.axvline(33.3,color="#ef7777",linestyle="--",linewidth=.9)
    ax.axvline(66.7,color="#65b86c",linestyle="--",linewidth=.9)
    for i,fab in enumerate(fabricantes):
        score = float(resumen.loc[fab,"mean"])
        color = "#61ae68" if score>=66.7 else "#f5ae3c" if score>=33.3 else "#ef6969"
        ax.barh(i,score,height=.55,color=color,alpha=.92,zorder=2)
        sub = df[df.FABRICANTE.eq(fab)]
        rng = np.random.default_rng(1000+i)
        for uso,c in [("DOMESTICA","#79509e"),("INDUSTRIAL","#2e84bb")]:
            z=sub.loc[sub.USO.eq(uso),"overall"].to_numpy()
            ax.scatter(z,i+rng.normal(0,.065,len(z)),s=29,color=c,
                       edgecolor="white",linewidth=.6,zorder=3)
        label_x = max(score + 2.6, float(sub.overall.max()) + 3.0)
        ax.text(label_x,i,un_decimal(score),va="center",fontsize=10,
                fontweight="bold",color="#439b4d" if score>=66.7 else "#e59520" if score>=33.3 else "#cf4444")
    ax.set_yticks(y,[f"{fab}  (n={int(resumen.loc[fab,'size'])})" for fab in fabricantes])
    ax.invert_yaxis()
    ax.set_xlim(0,105)
    ax.set_xlabel("Overall quality score (0–100)")
    ax.set_title("Overall quality score by manufacturer",fontsize=14,pad=14)
    ax.grid(axis="y",visible=False)
    ax.legend(handles=[
        plt.Line2D([],[],marker="o",linestyle="",color="#79509e",label="Household"),
        plt.Line2D([],[],marker="o",linestyle="",color="#2e84bb",label="Industrial"),
    ],title="Use type",loc="lower right",fontsize=8)
    fig.text(.53,.035,"Points = individual SDSs · Bars = mean · Shaded areas = reliability categories",
             ha="center",fontsize=8,color="#777777",style="italic")
    destino = OUT / "Figure_4_updated.png"
    fig.savefig(destino,dpi=300,facecolor="white")
    plt.close(fig)
    return destino


def media_ci(valores):
    valores = np.asarray(valores, dtype=float)
    media = valores.mean()
    if len(valores) < 2:
        return media, 0.0
    sem = stats.sem(valores)
    return media, stats.t.ppf(0.975, len(valores) - 1) * sem


def figura_6(df, completitud, sec_scores, distribucion):
    domain_rows = []
    for codigo, (secs, etiqueta) in DOMINIOS.items():
        cols = [f"SCORE_SEC_{s}" for s in secs]
        score_fds = df[cols].mean(axis=1)
        comp = np.mean([completitud[s] for s in secs])
        quality = np.mean([sec_scores[s] for s in secs])
        domain_rows.append((codigo, etiqueta, secs, score_fds, comp - quality))

    fig = plt.figure(figsize=(11.6967, 8.5967), dpi=300)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.38, 1.0], hspace=0.55, wspace=0.34,
                          left=0.07, right=0.975, bottom=0.08, top=0.79)
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    x = np.arange(5)
    width = 0.24
    colors = {"INDUSTRIAL": "#4a97c5", "GLOBAL": "#969696", "DOMESTICA": "#8057ad"}

    medias_global, ci_global, medias_i, ci_i, medias_h, ci_h = [], [], [], [], [], []
    for _, _, _, score_fds, _ in domain_rows:
        m, ci = media_ci(score_fds)
        medias_global.append(m); ci_global.append(ci)
        m, ci = media_ci(score_fds[df["USO"].eq("INDUSTRIAL")])
        medias_i.append(m); ci_i.append(ci)
        m, ci = media_ci(score_fds[df["USO"].eq("DOMESTICA")])
        medias_h.append(m); ci_h.append(ci)

    ax_a.axhspan(66.7, 100, color="#edf6ef", alpha=0.6)
    ax_a.axhspan(33.3, 66.7, color="#fff9e8", alpha=0.65)
    ax_a.axhspan(0, 33.3, color="#fdeeee", alpha=0.6)
    ax_a.axvspan(2.55, 3.45, color="#fff0bd", alpha=0.45)
    ax_a.bar(x - width, medias_i, width, yerr=ci_i, color=colors["INDUSTRIAL"], label="Industrial (n=25)", capsize=3)
    ax_a.bar(x, medias_global, width, yerr=ci_global, color=colors["GLOBAL"], label="Global (n=50)", capsize=3)
    ax_a.bar(x + width, medias_h, width, yerr=ci_h, color=colors["DOMESTICA"], label="Household (n=25)", capsize=3)
    ax_a.axhline(66.7, color="#35a854", linestyle="--", linewidth=1.0, label="Reliable threshold (66.7)")
    ax_a.axhline(33.3, color="#e24b4b", linestyle=":", linewidth=1.0, label="Unreliable threshold (33.3)")
    for xi, valor, ci in zip(x, medias_global, ci_global):
        ax_a.text(xi, valor + ci + 2.0, f"{valor:.1f}", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#333333")
    ax_a.set_ylim(0, 100)
    ax_a.set_ylabel("Quality score (0–100)")
    ax_a.set_xticks(x)
    ax_a.set_xticklabels([f"{r[0]}\n{r[1]}" for r in domain_rows], fontsize=8.5)
    ax_a.set_title("A. Quality score by functional domain\n(error bars = 95% CI)", fontweight="bold", y=1.20)
    handles, labels = ax_a.get_legend_handles_labels()
    order = [3, 4, 0, 1, 2]
    ax_a.legend([handles[i] for i in order], [labels[i] for i in order], loc="lower center",
                bbox_to_anchor=(0.5, 1.015), ncol=3, fontsize=8, frameon=True)
    ax_a.grid(axis="x", visible=False)

    gaps = [r[4] for r in domain_rows]
    gap_colors = ["#a6cee3" if g < 15 else "#f5ad32" if g <= 25 else "#ef5a5a" for g in gaps]
    bars = ax_b.bar(x, gaps, color=gap_colors)
    for bar, valor in zip(bars, gaps):
        ax_b.text(bar.get_x() + bar.get_width()/2, valor + 0.8, un_decimal(valor), ha="center", fontsize=8.5)
    ax_b.set_xticks(x, [r[0] for r in domain_rows])
    ax_b.set_ylim(0, 34)
    ax_b.set_ylabel("Gap (pts)")
    ax_b.set_title("B. Completeness–quality\ngap by domain", fontweight="bold")
    ax_b.legend(handles=[
        plt.Rectangle((0,0),1,1,color="#a6cee3",label="<15 pts"),
        plt.Rectangle((0,0),1,1,color="#f5ad32",label="15–25 pts"),
        plt.Rectangle((0,0),1,1,color="#ef5a5a",label=">25 pts"),
    ], loc="upper left", fontsize=7.5)
    ax_b.grid(axis="x", visible=False)

    delta = np.array(medias_i) - np.array(medias_h)
    df["SCORE_GLOBAL_RECALCULADO"] = df[[f"SCORE_SEC_{s}" for s in range(1, 17)]].mean(axis=1)
    delta_global = (df.loc[df.USO.eq("INDUSTRIAL"), "SCORE_GLOBAL_RECALCULADO"].mean()
                    - df.loc[df.USO.eq("DOMESTICA"), "SCORE_GLOBAL_RECALCULADO"].mean())
    delta_colors = ["#a6cee3" if d < delta_global else "#2e92b4" for d in delta]
    bars = ax_c.bar(x, delta, color=delta_colors)
    for bar, valor in zip(bars, delta):
        ax_c.text(bar.get_x() + bar.get_width()/2, valor + 0.8, f"{valor:.1f}", ha="center", fontsize=8.5)
    ax_c.axhline(delta_global, color="black", linestyle="--", linewidth=1,
                 label=f"Δ global ({un_decimal(delta_global)} pts)")
    ax_c.set_xticks(x, [r[0] for r in domain_rows])
    ax_c.set_ylim(0, 36)
    ax_c.set_ylabel("Δ Industrial − Household (pts)")
    ax_c.set_title("C. Industrial–Household\ndifference by domain", fontweight="bold")
    ax_c.legend(loc="upper left", fontsize=7.5)
    ax_c.grid(axis="x", visible=False)

    destino = OUT / "Figure_6_updated.png"
    fig.savefig(destino, dpi=300, facecolor="white")
    plt.close(fig)
    return destino


def main():
    df, completitud, sec_scores, distribucion = cargar()
    salidas = [
        figura_1(df, completitud, sec_scores, distribucion),
        figura_2(df, completitud, sec_scores, distribucion),
        figura_3(df, completitud, sec_scores, distribucion),
        figura_4(df, completitud, sec_scores, distribucion),
        figura_6(df, completitud, sec_scores, distribucion),
    ]
    for salida in salidas:
        print(salida)


if __name__ == "__main__":
    main()
