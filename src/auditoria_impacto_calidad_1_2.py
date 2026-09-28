#!/usr/bin/env python3
"""Compara los indicadores de calidad antes/después de corregir F03-P03-D/1.2.

No reemplaza los datos individuales de los dos evaluadores externos.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import friedmanchisquare, kruskal, wilcoxon
from sklearn.metrics import adjusted_rand_score, silhouette_score


MAP_Q = {"NO_CONFIABLE": 0.0, "CONFI_RESTR": 50.0, "CONFIABLE": 100.0, "NO_APLICA": np.nan}
DOMINIOS = {"G1": [1, 2, 3], "G2": [4, 5, 6], "G3": [7, 8], "G4": [9, 10, 11, 12], "G5": [13, 14, 15, 16]}
CRITICAS = [2, 4, 8, 11]


def resumen(path: Path):
    df = pd.read_csv(path)
    sec = []
    for n in range(1, 17):
        cols = [c for c in df if re.fullmatch(rf"CALIDAD_{n}_.*", c) and "CALIDAD_3_1_" not in c]
        q = df[cols].replace(MAP_Q).apply(pd.to_numeric, errors="coerce")
        df[f"S{n}"] = q.mean(axis=1)
        sec.append(f"S{n}")
    df["overall"] = df[sec].mean(axis=1)
    df["critical"] = df[[f"S{s}" for s in CRITICAS]].mean(axis=1)
    df["other"] = df[[c for c in sec if c not in [f"S{s}" for s in CRITICAS]]].mean(axis=1)
    df["weighted"] = (4 * df[[f"S{s}" for s in CRITICAS]].sum(axis=1) + df[[c for c in sec if c not in [f"S{s}" for s in CRITICAS]]].sum(axis=1)) / 28
    for nombre, secs in DOMINIOS.items():
        df[nombre] = df[[f"S{s}" for s in secs]].mean(axis=1)

    item_cols = [c for c in df if c.startswith("ITEM_") and "ITEM_3_1_" not in c]
    quality_cols = [c for c in df if c.startswith("CALIDAD_") and "CALIDAD_3_1_" not in c]
    config_cols = [x for pair in zip(item_cols,quality_cols) for x in pair]
    assert len(item_cols) == len(quality_cols) == 71
    x = df[sec].to_numpy(dtype=float)
    z = linkage(x, method="ward", metric="euclidean")
    labels = fcluster(z, 3, criterion="maxclust")
    df["cluster"] = labels

    h_use,p_use = kruskal(*(g["overall"].to_numpy() for _,g in df.groupby("USO")))
    h_man,p_man = kruskal(*(g["overall"].to_numpy() for _,g in df.groupby("FABRICANTE")))
    w_crit,p_crit = wilcoxon(df["critical"],df["other"])
    fr,p_fr = friedmanchisquare(*(df[d].to_numpy() for d in DOMINIOS))

    conf = df.drop_duplicates(subset=config_cols,keep="first")
    hc,pc = kruskal(*(g["overall"].to_numpy() for _,g in conf.groupby("USO")))
    wc,pwc = wilcoxon(conf["critical"],conf["other"])
    fconf,pfconf = friedmanchisquare(*(conf[d].to_numpy() for d in DOMINIOS))

    record = df.loc[df.ID.eq("F03-P03-D")].iloc[0]
    categories = pd.cut(df.overall,[-np.inf,33.3,66.7,np.inf],labels=["UNRELIABLE","RESTRICTED","RELIABLE"],right=False)
    weighted_categories = pd.cut(df.weighted,[-np.inf,33.3,66.7,np.inf],labels=["UNRELIABLE","RESTRICTED","RELIABLE"],right=False)
    out = {
        "path":str(path),
        "n":len(df),"configurations":len(conf),
        "quality_item_counts":df[quality_cols].stack().value_counts().to_dict(),
        "overall":{"mean":float(df.overall.mean()),"sd":float(df.overall.std(ddof=1)),"median":float(df.overall.median()),"min":float(df.overall.min()),"max":float(df.overall.max()),"iqr":float(df.overall.quantile(.75)-df.overall.quantile(.25)),"categories":categories.value_counts().to_dict()},
        "F03_P03_D":{"S1":float(record.S1),"overall":float(record.overall),"weighted":float(record.weighted),"cluster":int(record.cluster)},
        "section_means":{s:float(df[s].mean()) for s in sec},
        "use":{k:{"mean":float(g.overall.mean()),"sd":float(g.overall.std(ddof=1)),"median":float(g.overall.median())} for k,g in df.groupby("USO")},
        "use_test":{"H":float(h_use),"p":float(p_use),"epsilon_sq":float((h_use-1)/48)},
        "manufacturer":{k:{"mean":float(g.overall.mean()),"sd":float(g.overall.std(ddof=1))} for k,g in df.groupby("FABRICANTE")},
        "manufacturer_test":{"H":float(h_man),"p":float(p_man),"epsilon_sq":float((h_man-7)/42)},
        "critical":{"mean":float(df.critical.mean()),"other_mean":float(df.other.mean()),"W":float(w_crit),"p":float(p_crit)},
        "weighted":{"mean":float(df.weighted.mean()),"sd":float(df.weighted.std(ddof=1)),"reclassified":int((categories!=weighted_categories).sum())},
        "domains":{d:{"mean":float(df[d].mean()),"sd":float(df[d].std(ddof=1)),"industrial":float(df.loc[df.USO.eq("INDUSTRIAL"),d].mean()),"household":float(df.loc[df.USO.eq("DOMESTICA"),d].mean())} for d in DOMINIOS},
        "friedman":{"chi2":float(fr),"p":float(p_fr),"kendall_W":float(fr/(len(df)*4))},
        "cluster":{"labels_by_id":dict(zip(df.ID,labels.astype(int))),"sizes":pd.Series(labels).value_counts().sort_index().to_dict(),"silhouette":float(silhouette_score(x,labels))},
        "configuration_sensitivity":{"use_H":float(hc),"use_p":float(pc),"critical_W":float(wc),"critical_p":float(pwc),"friedman_chi2":float(fconf),"friedman_p":float(pfconf)},
    }
    return out


def main():
    old = resumen(Path(sys.argv[1]))
    new = resumen(Path(sys.argv[2]))
    print("ARI_cluster",adjusted_rand_score(list(old["cluster"]["labels_by_id"].values()),list(new["cluster"]["labels_by_id"].values())))
    print("changed_cluster_ids",[id for id in old["cluster"]["labels_by_id"] if old["cluster"]["labels_by_id"][id]!=new["cluster"]["labels_by_id"][id]])
    for key in ["quality_item_counts","overall","F03_P03_D","section_means","use","use_test","manufacturer","manufacturer_test","critical","weighted","domains","friedman","cluster","configuration_sensitivity"]:
        if key=="cluster":
            for sub in ["sizes","silhouette"]:
                if old[key][sub]!=new[key][sub]: print(f"{key}.{sub}",old[key][sub],"=>",new[key][sub])
            continue
        if old[key]!=new[key]: print(key,json.dumps(old[key],ensure_ascii=False),"=>",json.dumps(new[key],ensure_ascii=False))


if __name__=="__main__":
    main()
