#!/usr/bin/env python3
# ADVERTENCIA - script heredado (historico, no reproducible tal cual desde el repositorio).
# Fue escrito para una carpeta de trabajo plana (RAIZ = carpeta del script) que contenia un
# eval.csv y otros insumos propios. Ese eval.csv NO es data/processed/eval.csv: era una copia
# antigua de febrero. Se conserva como registro del metodo. Para reproducir la concordancia
# use:  python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv \
#         data/external/eval_2.csv data/external/eval_original.csv
"""Reproducibility analysis for the revised 75-item SDS codebook.

Input: a CSV following coding_matrix_v2_template.csv with one row per
document-item combination and completed independent rater columns.

Outputs:
  - item_agreement.csv: n, agreement, linearly weighted Cohen kappa and CI
  - section_score_agreement.csv: section-level ICC(2,1) and CI
  - overall_score_agreement.csv: overall ICC(2,1) and CI
  - validation_report.txt: reconciliation and missingness checks

Kappa measures inter-rater reproducibility; it does not establish chemical
accuracy, construct validity or regulatory compliance.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

CATEGORIES = {"inadequate": 0, "partially adequate": 1, "adequate": 2}
REQUIRED = {
    "document_id", "manufacturer_code", "section", "item_id", "applicability",
    "adequacy_rater1", "adequacy_rater2",
}


def normalize_rating(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower().replace("_", " ")
    aliases = {
        "0": "inadequate", "50": "partially adequate", "100": "adequate",
        "partial": "partially adequate", "partially_adequate": "partially adequate",
    }
    text = aliases.get(text, text)
    if text not in CATEGORIES:
        raise ValueError(f"Unknown adequacy rating: {value!r}")
    return CATEGORIES[text]


def weighted_kappa(a, b):
    if len(a) == 0:
        return np.nan
    if len(set(a) | set(b)) < 2:
        return np.nan
    matrix = np.zeros((3, 3), dtype=float)
    for left, right in zip(a, b):
        matrix[int(left), int(right)] += 1.0
    matrix /= matrix.sum()
    row = matrix.sum(axis=1)
    col = matrix.sum(axis=0)
    expected = np.outer(row, col)
    weights = 1.0 - np.abs(np.arange(3)[:, None] - np.arange(3)[None, :]) / 2.0
    observed_agreement = float(np.sum(weights * matrix))
    expected_agreement = float(np.sum(weights * expected))
    denom = 1.0 - expected_agreement
    return np.nan if denom == 0 else float((observed_agreement - expected_agreement) / denom)


def bootstrap_kappa(a, b, iterations=2000, seed=1496):
    if len(a) < 2:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(iterations):
        idx = rng.integers(0, len(a), len(a))
        value = weighted_kappa(a[idx], b[idx])
        if np.isfinite(value):
            stats.append(value)
    if not stats:
        return np.nan, np.nan
    return tuple(np.quantile(stats, [0.025, 0.975]))


def icc2_1_from_wide(values):
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2 or arr.shape[0] < 2:
        return np.nan
    n, k = arr.shape
    grand = arr.mean()
    row_means = arr.mean(axis=1)
    col_means = arr.mean(axis=0)
    ss_rows = k * np.sum((row_means - grand) ** 2)
    ss_cols = n * np.sum((col_means - grand) ** 2)
    ss_error = np.sum((arr - row_means[:, None] - col_means[None, :] + grand) ** 2)
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_error = ss_error / ((n - 1) * (k - 1))
    denom = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    return np.nan if denom == 0 else float((ms_rows - ms_error) / denom)


def score_frame(frame, group_cols):
    valid = frame.dropna(subset=["r1", "r2"]).copy()
    scores = valid.groupby(group_cols, as_index=False).agg(r1=("r1", "mean"), r2=("r2", "mean"))
    scores[["r1", "r2"]] *= 50.0
    return scores


def icc_with_bootstrap(scores, iterations, seed):
    point = icc2_1_from_wide(scores[["r1", "r2"]].to_numpy())
    rng = np.random.default_rng(seed)
    vals = []
    if len(scores) >= 2:
        for _ in range(iterations):
            idx = rng.integers(0, len(scores), len(scores))
            val = icc2_1_from_wide(scores.iloc[idx][["r1", "r2"]].to_numpy())
            if np.isfinite(val):
                vals.append(val)
    low, high = (np.nan, np.nan) if not vals else np.quantile(vals, [0.025, 0.975])
    return point, low, high


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1496)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input_csv)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")
    if df.duplicated(["document_id", "item_id"]).any():
        raise SystemExit("Duplicate document_id/item_id combinations detected")

    applicable = df["applicability"].astype(str).str.strip().str.lower().isin({"applicable", "yes", "1", "true"})
    work = df[applicable].copy()
    work["r1"] = work["adequacy_rater1"].map(normalize_rating)
    work["r2"] = work["adequacy_rater2"].map(normalize_rating)

    rows = []
    for item_index, ((section, item_id), part) in enumerate(work.groupby(["section", "item_id"], sort=True)):
        paired = part.dropna(subset=["r1", "r2"])
        a = paired["r1"].astype(int).to_numpy()
        b = paired["r2"].astype(int).to_numpy()
        point = weighted_kappa(a, b)
        low, high = bootstrap_kappa(a, b, args.bootstrap, args.seed + item_index)
        rows.append({
            "section": section, "item_id": item_id, "n_paired": len(paired),
            "percent_agreement": 100 * np.mean(a == b) if len(a) else np.nan,
            "weighted_kappa": point, "kappa_ci95_low": low, "kappa_ci95_high": high,
            "kappa_status": "undefined_constant_distribution" if not np.isfinite(point) else "estimated",
        })
    pd.DataFrame(rows).to_csv(args.output_dir / "item_agreement.csv", index=False)

    section_scores = score_frame(work, ["document_id", "section"])
    section_rows = []
    for section, part in section_scores.groupby("section", sort=True):
        point, low, high = icc_with_bootstrap(part, args.bootstrap, args.seed)
        section_rows.append({"section": section, "n_documents": len(part), "icc2_1": point, "icc_ci95_low": low, "icc_ci95_high": high})
    pd.DataFrame(section_rows).to_csv(args.output_dir / "section_score_agreement.csv", index=False)

    overall = score_frame(work, ["document_id"])
    point, low, high = icc_with_bootstrap(overall, args.bootstrap, args.seed)
    pd.DataFrame([{"n_documents": len(overall), "icc2_1": point, "icc_ci95_low": low, "icc_ci95_high": high}]).to_csv(
        args.output_dir / "overall_score_agreement.csv", index=False
    )

    expected = 50 * 75
    report = [
        f"Rows supplied: {len(df)}",
        f"Expected document-item combinations: {expected}",
        f"Unique documents: {df['document_id'].nunique()}",
        f"Unique items: {df['item_id'].nunique()}",
        f"Applicable rows: {len(work)}",
        f"Rows with paired ratings: {len(work.dropna(subset=['r1', 'r2']))}",
        "Interpretation: kappa/ICC quantify inter-rater agreement only; they do not validate chemical accuracy.",
    ]
    (args.output_dir / "validation_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
