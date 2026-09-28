#!/usr/bin/env python3
"""Calcula, desde los datos del repositorio, todos los resultados estadisticos congelados.

    python3 src/analisis_congelado.py            # escribe outputs/resultados/
    python3 src/analisis_congelado.py --no-escribir

No depende de ninguna version del manuscrito: los resultados se nombran por su
contenido, nunca por el numero de tabla o figura. Escribe:
  outputs/resultados/resultados_congelados.json   todos los valores, sin redondear
  outputs/resultados/cifras_de_referencia.md      los mismos, redondeados como se reportan

Convenciones fijadas (no cambiar: cambiarlas cambia resultados congelados):
  - Calidad: CONFIABLE 100, CONFI_RESTR 50, NO_CONFIABLE 0. NO_APLICA fuera del denominador.
  - Puntaje de seccion por FDS = media de sus items; puntaje global = media de las 16 secciones.
  - Clasificacion de FDS: >= 66.7 confiable; >= 33.3 con restricciones; < 33.3 no confiable.
  - Kruskal-Wallis con correccion por empates (scipy); tamano de efecto eta2_H = (H - k + 1)/(n - k).
  - Wilcoxon pareado (scipy, bilateral); r = Z/sqrt(n) con Z = isf(p/2).
  - Friedman; W de Kendall = chi2 / (n (k - 1)).
  - Dunn con correccion de Bonferroni (scikit-posthocs).
  - Ward (scipy, euclidea) sobre la matriz 50 x 16 de puntajes de calidad por seccion; k = 3.
  - Configuraciones: vector completo de presencia y calidad de los 75 items. Representante =
    la primera FDS de cada configuracion segun la columna FDS (orden de compilacion).
  - Indice ponderado: peso w en S2, S4, S8, S11 y 1 en las demas.
  - IQR con percentiles de interpolacion lineal (numpy por defecto).
"""
import csv, json, sys, itertools, importlib.util, warnings
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score
import scikit_posthocs as sp
import diptest

warnings.filterwarnings('ignore')
RAIZ = Path(__file__).resolve().parent.parent
MATRIZ = RAIZ / 'data' / 'processed' / 'eval.csv'
EXT = RAIZ / 'data' / 'external'
SALIDA = RAIZ / 'outputs' / 'resultados'
QV = {'CONFIABLE': 100.0, 'CONFI_RESTR': 50.0, 'NO_CONFIABLE': 0.0}
CRIT = [2, 4, 8, 11]
DOM = {'G1': [1, 2, 3], 'G2': [4, 5, 6], 'G3': [7, 8], 'G4': [9, 10, 11, 12], 'G5': [13, 14, 15, 16]}
Q = [f'Q{s}' for s in range(1, 17)]
LO, HI = 33.3, 66.7


def clasif(x, lo=LO, hi=HI):
    return 'R' if x >= hi else ('RR' if x >= lo else 'U')


def cargar():
    rows = list(csv.DictReader(open(MATRIZ, encoding='utf-8-sig')))
    cols = [c[5:] for c in rows[0] if c.startswith('ITEM_')]

    def valida(r, c):
        p = (r['ITEM_' + c] or '').strip(); q = (r['CALIDAD_' + c] or '').strip()
        if p == 'NO_APLICA' or q == 'NO_APLICA' or (not p and not q):
            return None
        return p == 'PRESENTE', QV.get(q, 0.0), q

    recs = []
    for r in rows:
        d = {'ID': r['ID'], 'FDS': int(r['FDS']), 'FAB': r['FABRICANTE'].strip(), 'USO': r['USO'].strip(),
             'ANIO': r['ELABORADA'][:4]}
        sq, sc = defaultdict(list), defaultdict(list)
        for c in cols:
            v = valida(r, c)
            if v is None:
                continue
            s = int(c.split('_')[0]); sq[s].append(v[1]); sc[s].append(100.0 * v[0])
        for s in range(1, 17):
            d[f'Q{s}'] = float(np.mean(sq[s])); d[f'C{s}'] = float(np.mean(sc[s]))
        d['global'] = float(np.mean([d[q] for q in Q]))
        d['cfg'] = tuple((r['ITEM_' + c].strip(), r['CALIDAD_' + c].strip()) for c in cols)
        recs.append(d)
    return rows, cols, valida, pd.DataFrame(recs)


def kw(*grupos):
    H, p = stats.kruskal(*grupos)
    n = sum(len(g) for g in grupos); k = len(grupos)
    return {'H': float(H), 'p': float(p), 'eta2_H': float((H - k + 1) / (n - k)), 'n': n, 'k': k}


def wilcoxon(a, b):
    r = stats.wilcoxon(a, b); z = stats.norm.isf(r.pvalue / 2)
    return {'W': float(r.statistic), 'p': float(r.pvalue), 'r': float(z / np.sqrt(len(a))), 'n': len(a)}


def dominios(d):
    return pd.DataFrame({g: d[[f'Q{s}' for s in v]].mean(axis=1) for g, v in DOM.items()})


def friedman(d):
    m = dominios(d); f = stats.friedmanchisquare(*[m[g] for g in m])
    return {'chi2': float(f.statistic), 'p': float(f.pvalue), 'W_kendall': float(f.statistic / (len(d) * (len(DOM) - 1))), 'n': len(d)}


def criticas(d):
    c = d[[f'Q{s}' for s in CRIT]].mean(axis=1); nc = d[[f'Q{s}' for s in range(1, 17) if s not in CRIT]].mean(axis=1)
    return {'criticas_media': float(c.mean()), 'criticas_mediana': float(c.median()), 'no_criticas_media': float(nc.mean()),
            'no_criticas_mediana': float(nc.median()), **wilcoxon(c, nc)}


def uso(d):
    i = d[d.USO == 'INDUSTRIAL'].global_; h = d[d.USO == 'DOMESTICA'].global_
    return kw(i, h)


def calcular():
    rows, cols, valida, df = cargar()
    df = df.rename(columns={'global': 'global_'})
    R = {}
    # items
    it = {}
    for c in cols:
        v = [valida(r, c) for r in rows]; v = [x for x in v if x]
        if not v:
            continue
        it[c.replace('_', '.')] = {'completitud': 100 * float(np.mean([x[0] for x in v])), 'calidad': float(np.mean([x[1] for x in v])),
                                   'no_confiable_pct': 100 * float(np.mean([x[2] == 'NO_CONFIABLE' for x in v])), 'n': len(v)}
    R['items'] = it
    cat = Counter(x[2] for r in rows for c in cols for x in [valida(r, c)] if x)
    n = sum(cat.values())
    # --- A y B: presencia y distribucion
    o = df.global_.values
    vacios = [(float(a), float(b)) for a, b in zip(np.sort(np.round(o, 1)), np.sort(np.round(o, 1))[1:]) if b - a > 5]
    R['distribucion'] = {
        'decisiones_evaluables': n, 'pct_confiable': 100 * cat['CONFIABLE'] / n, 'pct_con_restricciones': 100 * cat['CONFI_RESTR'] / n,
        'pct_no_confiable': 100 * cat['NO_CONFIABLE'] / n,
        'fds_con_16_encabezados': int(sum(all(r['ITEM_%d_0' % s].strip() == 'PRESENTE' for s in range(1, 17)) for r in rows)),
        'media': float(o.mean()), 'de': float(o.std(ddof=1)), 'mediana': float(np.median(o)), 'minimo': float(o.min()),
        'maximo': float(o.max()), 'iqr': float(np.percentile(o, 75) - np.percentile(o, 25)),
        'clasificacion': dict(Counter(clasif(x) for x in o)),
        'intervalos_vacios_mayores_5': vacios,
        'reclasificadas_cortes_40_70': int(sum(clasif(x, 40, 70) != clasif(x) for x in o)),
        'reclasificadas_cortes_25_75': int(sum(clasif(x, 25, 75) != clasif(x) for x in o)),
        'dip_hartigan': float(diptest.dipstat(o)),
    }
    g1 = stats.skew(o, bias=False); g2 = stats.kurtosis(o, bias=False); N = len(o)
    R['distribucion']['coef_bimodalidad_sarle'] = float((g1 ** 2 + 1) / (g2 + 3 * (N - 1) ** 2 / ((N - 2) * (N - 3))))
    # --- secciones
    R['secciones'] = {f'S{s}': {'calidad': float(np.mean([v['calidad'] for k, v in it.items() if int(k.split('.')[0]) == s])),
                                'completitud': float(np.mean([v['completitud'] for k, v in it.items() if int(k.split('.')[0]) == s]))}
                      for s in range(1, 17)}
    for s, v in R['secciones'].items():
        v['brecha'] = v['completitud'] - v['calidad']
    # --- C: brecha
    sc = [R['secciones'][f'S{s}'] for s in range(1, 17)]
    rs = stats.spearmanr([v['completitud'] for v in sc], [v['calidad'] for v in sc])
    ri = stats.spearmanr([v['completitud'] for v in it.values()], [v['calidad'] for v in it.values()])
    R['brecha'] = {'spearman_secciones': {'rho': float(rs.statistic), 'p': float(rs.pvalue), 'n': 16},
                   'spearman_items': {'rho': float(ri.statistic), 'p': float(ri.pvalue), 'n': len(it)},
                   'items_presencia_ge_90': sum(v['completitud'] >= 90 for v in it.values()),
                   'items_presencia_gt_90': sum(v['completitud'] > 90 for v in it.values()),
                   'items_presencia_ge_90_calidad_lt_50': sorted(k for k, v in it.items() if v['completitud'] >= 90 and v['calidad'] < 50),
                   'secciones_brecha_gt_20': sorted((k for k, v in R['secciones'].items() if v['brecha'] > 20), key=lambda k: int(k[1:])),
                   'item_mas_debil_por_seccion': {f'S{s}': min(((v['calidad'], k) for k, v in it.items()
                                                                 if int(k.split('.')[0]) == s and k != f'{s}.0'))[1] for s in range(1, 17)}}
    R['S2_por_fabricante'] = df.groupby('FAB').Q2.mean().to_dict()
    R['S2_por_uso'] = df.groupby('USO').Q2.mean().to_dict()
    # --- D: uso
    ind = df[df.USO == 'INDUSTRIAL']; hh = df[df.USO == 'DOMESTICA']
    R['uso'] = {'shapiro_p_industrial': float(stats.shapiro(ind.global_).pvalue), 'shapiro_p_domestico': float(stats.shapiro(hh.global_).pvalue),
                'industrial': {'media': float(ind.global_.mean()), 'de': float(ind.global_.std()), 'mediana': float(ind.global_.median())},
                'domestico': {'media': float(hh.global_.mean()), 'de': float(hh.global_.std()), 'mediana': float(hh.global_.median())},
                'diferencia': float(ind.global_.mean() - hh.global_.mean()), **uso(df),
                'diferencia_por_seccion': {f'S{s}': float(ind[f'Q{s}'].mean() - hh[f'Q{s}'].mean()) for s in range(1, 17)},
                'fabricantes_con_ambos_usos': {f: df[df.FAB == f].groupby('USO').global_.mean().to_dict()
                                               for f in sorted(df.FAB.unique()) if df[df.FAB == f].USO.nunique() == 2}}
    # --- E: fabricante
    grupos = [df[df.FAB == f].global_ for f in sorted(df.FAB.unique())]
    dn = sp.posthoc_dunn(df, val_col='global_', group_col='FAB', p_adjust='bonferroni')
    R['fabricante'] = {**kw(*grupos), 'media': df.groupby('FAB').global_.mean().to_dict(), 'de': df.groupby('FAB').global_.std().to_dict(),
                       'dunn_bonferroni_pares_p_lt_05': [[a, b] for i, a in enumerate(dn.index) for b in dn.columns[i + 1:] if dn.loc[a, b] < 0.05]}
    # --- F: tipologias
    X = df[Q].values; Z = linkage(X, 'ward')
    R['tipologias'] = {'silueta': {k: float(silhouette_score(X, fcluster(Z, k, 'maxclust'))) for k in range(2, 7)}}
    lab = fcluster(Z, 3, 'maxclust')

    def perfil(d, lab):
        out = []
        for c in sorted(set(lab)):
            x = d[lab == c]
            out.append({'n': len(x), 'fabricantes': dict(sorted(Counter(x.FAB).items())), 'usos': dict(sorted(Counter(x.USO).items())),
                        'media': float(x.global_.mean()), 'mediana': float(x.global_.median()), 'minimo': float(x.global_.min()),
                        'maximo': float(x.global_.max()), 'secciones': {q.replace('Q', 'S'): float(x[q].mean()) for q in Q}})
        return sorted(out, key=lambda p: -p['media'])
    R['tipologias']['k3_50_fds'] = perfil(df, lab)
    d24 = df.sort_values('FDS').drop_duplicates('cfg')
    X2 = d24[Q].values; l2 = fcluster(linkage(X2, 'ward'), 3, 'maxclust')
    R['tipologias']['k3_24_configuraciones'] = {'silueta': float(silhouette_score(X2, l2)), 'grupos': perfil(d24, l2)}
    # --- G: secciones criticas
    R['criticas'] = {'50_fds': criticas(df), '24_configuraciones': criticas(d24)}
    # --- H: indice ponderado
    base = [clasif(x) for x in o]; H = {}
    for w in (2, 3, 4, 5):
        wi = (sum(df[f'Q{s}'] * (w if s in CRIT else 1) for s in range(1, 17)) / (12 + 4 * w)).values
        nue = [clasif(x) for x in wi]
        H[str(w)] = {'media': float(wi.mean()), 'de': float(wi.std(ddof=1)), 'reclasificadas': int(sum(a != b for a, b in zip(base, nue))),
                     'transiciones': {f'{a}->{b}': c for (a, b), c in Counter((a, b) for a, b in zip(base, nue) if a != b).items()},
                     'valores_reclasificadas': sorted(round(float(y), 1) for y, a, b in zip(wi, base, nue) if a != b)}
    R['ponderado'] = H
    esc = {}
    base_sec = [R['secciones'][f'S{s}']['calidad'] for s in range(1, 17)]
    for alt in (25, 75):
        qv = {'CONFIABLE': 100.0, 'CONFI_RESTR': float(alt), 'NO_CONFIABLE': 0.0}
        sec = []
        for s in range(1, 17):
            per = [np.mean([qv.get(r['CALIDAD_' + c].strip(), 0.0) for c in cols if int(c.split('_')[0]) == s and valida(r, c)]) for r in rows]
            sec.append(float(np.mean(per)))
        esc[str(alt)] = {'spearman_con_orden_base': float(stats.spearmanr(sec, base_sec).statistic),
                         'orden_identico': [int(i) for i in np.argsort(sec)] == [int(i) for i in np.argsort(base_sec)]}
    R['escala_alternativa'] = esc
    # --- I: dominios
    m = dominios(df); dom = {}
    for g, v in DOM.items():
        comp = float(np.mean([R['secciones'][f'S{s}']['completitud'] for s in v]))
        dom[g] = {'media': float(m[g].mean()), 'de': float(m[g].std()), 'industrial': float(m[g][df.USO == 'INDUSTRIAL'].mean()),
                  'domestico': float(m[g][df.USO == 'DOMESTICA'].mean()), 'brecha': comp - float(m[g].mean()),
                  **{f'kw_uso_{k}': v2 for k, v2 in kw(m[g][df.USO == 'INDUSTRIAL'], m[g][df.USO == 'DOMESTICA']).items()}}
        dom[g]['diferencia'] = dom[g]['industrial'] - dom[g]['domestico']
    R['dominios'] = {'por_dominio': dom, 'friedman_50_fds': friedman(df), 'friedman_24_configuraciones': friedman(d24),
                     'wilcoxon_pares': {f'{a}-{b}': wilcoxon(m[a], m[b]) for a, b in itertools.combinations(DOM, 2)}}
    # --- sensibilidad a configuraciones repetidas
    multi = df.groupby('cfg').filter(lambda x: x.FAB.nunique() > 1 or x.USO.nunique() > 1)
    grupos_m = [list(x.index) for _, x in multi.groupby('cfg')]
    resto = df.drop(index=multi.index).drop_duplicates('cfg')
    alts = [uso(pd.concat([resto, df.loc[list(c)]])) for c in itertools.product(*grupos_m)]
    R['configuraciones'] = {'distintas': int(df.cfg.nunique()),
                            'que_mezclan_fabricante_o_uso': [{'n': len(g), 'fabricantes': sorted(df.loc[g].FAB.unique()), 'usos': sorted(df.loc[g].USO.unique())} for g in grupos_m],
                            'uso_24': uso(d24), 'fabricante_24': kw(*[x.global_ for _, x in d24.groupby('FAB')]),
                            'uso_representantes_alternativos': {'eta2_H_min': min(a['eta2_H'] for a in alts), 'eta2_H_max': max(a['eta2_H'] for a in alts),
                                                                'p_max': max(a['p'] for a in alts), 'n_combinaciones': len(alts)}}
    # --- corpus por ano
    R['corpus'] = {'por_ano': dict(sorted(Counter(df.ANIO).items())), 'fabricantes_por_ano': {a: sorted(x.FAB.unique()) for a, x in df.groupby('ANIO')},
                   'max_anos_por_fabricante': int(df.groupby('FAB').ANIO.nunique().max()), 'S15_por_ano': df.groupby('ANIO').Q15.mean().to_dict(),
                   'por_fabricante_y_uso': {f'{a}|{b}': int(c) for (a, b), c in Counter(zip(df.FAB, df.USO)).items()}}
    # --- concordancia: lo que no cubre src/kappa/verificacion_concordancia.py
    spec = importlib.util.spec_from_file_location('vc', RAIZ / 'src' / 'kappa' / 'verificacion_concordancia.py')
    vc = importlib.util.module_from_spec(spec); spec.loader.exec_module(vc)
    e1, e2, co = (vc.load(str(EXT / f), True) for f in ('eval_1.csv', 'eval_2.csv', 'eval_original.csv'))
    keys = sorted(e1); ids = sorted({k[0] for k in keys}); sub = df[df.ID.isin(ids)]

    def puntaje(d):
        out = {}
        for i in ids:
            sec = defaultdict(list)
            for k in keys:
                if k[0] == i:
                    sec[d[k][2]].append(d[k][1] * 50.0)
            out[i] = float(np.mean([np.mean(v) for v in sec.values()]))
        return out
    pc, p1, p2 = puntaje(co), puntaje(e1), puntaje(e2)
    secs = sorted({e1[k][2] for k in keys}, key=lambda s: int(s[1:]))
    ksec = {s: float(vc.coef([e1[k][1] for k in keys if e1[k][2] == s], [e2[k][1] for k in keys if e1[k][2] == s], 3, True)[1]) for s in secs}
    rk = stats.spearmanr(list(ksec.values()), [R['secciones'][s]['calidad'] for s in secs])
    sin3 = [k for k in keys if k[1] not in ('3.2.1.1', '3.2.1.2', '3.2.1.3')]

    def kap(ks, calidad):
        f = (lambda d, k: d[k][1]) if calidad else (lambda d, k: 1 if d[k][0] == 'PRESENTE' else 0)
        return float(vc.coef([f(e1, k) for k in ks], [f(e2, k) for k in ks], 3 if calidad else 2, calidad)[1])
    dist = Counter(co[k][1] for k in keys)
    R['concordancia'] = {
        'submuestra': {'fds': len(ids), 'fabricantes': int(sub.FAB.nunique()), 'configuraciones': int(sub.cfg.nunique()), 'usos': dict(Counter(sub.USO))},
        'distribucion_consenso_pct': {'confiable': 100 * dist[2] / len(keys), 'con_restricciones': 100 * dist[1] / len(keys), 'no_confiable': 100 * dist[0] / len(keys)},
        'evaluador_menos_consenso': {e: {'diferencia_media': float(np.mean([p[i] - pc[i] for i in ids])), 'wilcoxon_p': float(stats.wilcoxon([p[i] for i in ids], [pc[i] for i in ids]).pvalue)}
                                     for e, p in (('E1', p1), ('E2', p2))},
        'kappa_calidad_por_seccion': ksec, 'secciones_kappa_ge_060': sum(v >= 0.60 for v in ksec.values()),
        'tres_secciones_kappa_mas_bajo': sorted(ksec, key=ksec.get)[:3],
        'spearman_kappa_vs_calidad_seccion': {'rho': float(rk.statistic), 'p': float(rk.pvalue)},
        'cambio_kappa_sin_3_items_confidencialidad_S3': {'calidad': kap(sin3, True) - kap(keys, True), 'completitud': kap(sin3, False) - kap(keys, False)},
    }
    return R


def r(x, d=1):
    return f'{x:.{d}f}'


def cifras(R):
    """Hoja de cifras redondeadas como se reportan. Nombres por contenido, no por numero de tabla."""
    D, U, F, G, I, C = R['distribucion'], R['uso'], R['fabricante'], R['criticas'], R['dominios'], R['concordancia']
    L = ['# Cifras de referencia (generado por src/analisis_congelado.py; no editar a mano)', '',
         'Toda cifra del manuscrito, en cualquier version, debe coincidir con esta hoja.', '',
         '## Distribucion', f"- Decisiones evaluables: {D['decisiones_evaluables']}; confiable {r(D['pct_confiable'])} %, con restricciones {r(D['pct_con_restricciones'])} %, no confiable {r(D['pct_no_confiable'])} %",
         f"- Puntaje global: media {r(D['media'])}, DE {r(D['de'])}, mediana {r(D['mediana'])}, rango {r(D['minimo'])}–{r(D['maximo'])}, IQR {r(D['iqr'])}",
         f"- Clasificacion (33.3/66.7): {D['clasificacion']}; cortes 40/70 reclasifican {D['reclasificadas_cortes_40_70']}; 25/75 reclasifican {D['reclasificadas_cortes_25_75']}",
         f"- Dip de Hartigan {r(D['dip_hartigan'],3)}; coeficiente de bimodalidad {r(D['coef_bimodalidad_sarle'],2)}; intervalos vacios > 5 pts: {D['intervalos_vacios_mayores_5']}",
         '', '## Brecha completitud–calidad',
         f"- Spearman secciones rho {r(R['brecha']['spearman_secciones']['rho'],3)} (p {r(R['brecha']['spearman_secciones']['p'],3)}); items rho {r(R['brecha']['spearman_items']['rho'],3)} (n {R['brecha']['spearman_items']['n']})",
         f"- Items presentes en >= 90 %: {R['brecha']['items_presencia_ge_90']} (> 90 %: {R['brecha']['items_presencia_gt_90']}); de ellos con calidad < 50: {R['brecha']['items_presencia_ge_90_calidad_lt_50']}",
         f"- Secciones con brecha > 20 pts: {R['brecha']['secciones_brecha_gt_20']}", '', '## Secciones (calidad / completitud / brecha)']
    L += [f"- {s}: {r(v['calidad'])} / {r(v['completitud'])} / {r(v['brecha'])}" for s, v in R['secciones'].items()]
    L += ['', '## Uso', f"- Industrial {r(U['industrial']['media'])} (DE {r(U['industrial']['de'])}, mediana {r(U['industrial']['mediana'])}); domestico {r(U['domestico']['media'])} (DE {r(U['domestico']['de'])}, mediana {r(U['domestico']['mediana'])}); diferencia {r(U['diferencia'])}",
          f"- Kruskal-Wallis H(1) = {r(U['H'])}, p = {U['p']:.1e}, eta2_H = {r(U['eta2_H'],3)}",
          '', '## Fabricante', f"- H(7) = {r(F['H'])}, p = {F['p']:.1e}, eta2_H = {r(F['eta2_H'],3)}; medias {({k: round(v, 1) for k, v in F['media'].items()})}",
          f"- Dunn-Bonferroni significativos: {F['dunn_bonferroni_pares_p_lt_05']}", '', '## Secciones criticas',
          f"- 50 FDS: {r(G['50_fds']['criticas_media'])} (mediana {r(G['50_fds']['criticas_mediana'])}) vs {r(G['50_fds']['no_criticas_media'])} (mediana {r(G['50_fds']['no_criticas_mediana'])}); W = {r(G['50_fds']['W'],0)}, p = {r(G['50_fds']['p'],3)}, r = {r(G['50_fds']['r'],3)}",
          f"- 24 configuraciones: {r(G['24_configuraciones']['criticas_media'])} vs {r(G['24_configuraciones']['no_criticas_media'])}; W = {r(G['24_configuraciones']['W'],0)}, p = {r(G['24_configuraciones']['p'],3)}, r = {r(G['24_configuraciones']['r'],3)}",
          '', '## Indice ponderado'] + [f"- w = {w}: media {r(v['media'])}, reclasificadas {v['reclasificadas']} {v['transiciones']}" for w, v in R['ponderado'].items()]
    L += [f"- Escala alternativa {k}: rho con el orden base {r(v['spearman_con_orden_base'],3)}; orden identico: {v['orden_identico']}" for k, v in R['escala_alternativa'].items()]
    L += ['', '## Dominios'] + [f"- {g}: {r(v['media'])} ± {r(v['de'])}; industrial {r(v['industrial'])}, domestico {r(v['domestico'])}, diferencia {r(v['diferencia'])}, brecha {r(v['brecha'])}; KW uso H = {r(v['kw_uso_H'],2)}, p = {r(v['kw_uso_p'],3)}, eta2_H = {r(v['kw_uso_eta2_H'],3)}" for g, v in I['por_dominio'].items()]
    L += [f"- Friedman 50 FDS: chi2 = {r(I['friedman_50_fds']['chi2'],2)}, p = {r(I['friedman_50_fds']['p'],4)}, W = {r(I['friedman_50_fds']['W_kendall'],3)}; 24 configuraciones: p = {r(I['friedman_24_configuraciones']['p'],4)}, W = {r(I['friedman_24_configuraciones']['W_kendall'],3)}"]
    L += [f"- Wilcoxon {k}: W = {r(v['W'],0)}, p = {r(v['p'],4)}, r = {r(v['r'],3)}" for k, v in I['wilcoxon_pares'].items()]
    K = R['configuraciones']
    L += ['', '## Configuraciones repetidas', f"- Distintas: {K['distintas']}; uso con 24: H = {r(K['uso_24']['H'],2)}, p = {r(K['uso_24']['p'],4)}, eta2_H = {r(K['uso_24']['eta2_H'],3)}; fabricante con 24: p = {r(K['fabricante_24']['p'],4)}",
          f"- Uso con representantes alternativos: eta2_H {r(K['uso_representantes_alternativos']['eta2_H_min'],3)}–{r(K['uso_representantes_alternativos']['eta2_H_max'],3)}, p max {r(K['uso_representantes_alternativos']['p_max'],4)}",
          '', '## Tipologias (Ward, k = 3)', f"- Silueta: {({k: round(v, 3) for k, v in R['tipologias']['silueta'].items()})}"]
    L += [f"- Grupo n = {p['n']}: fabricantes {p['fabricantes']}, media {r(p['media'],2)}, mediana {r(p['mediana'])}, rango {r(p['minimo'])}–{r(p['maximo'])}" for p in R['tipologias']['k3_50_fds']]
    L += [f"- 24 configuraciones: silueta {r(R['tipologias']['k3_24_configuraciones']['silueta'],3)}"] + [f"  - n = {p['n']}: {p['fabricantes']}, media {r(p['media'])}" for p in R['tipologias']['k3_24_configuraciones']['grupos']]
    L += ['', '## Concordancia (complemento de src/kappa/verificacion_concordancia.py)',
          f"- Submuestra: {C['submuestra']}; distribucion del consenso: {({k: round(v, 1) for k, v in C['distribucion_consenso_pct'].items()})}",
          f"- Evaluadores frente al consenso: {({e: (round(v['diferencia_media'], 1), round(v['wilcoxon_p'], 4)) for e, v in C['evaluador_menos_consenso'].items()})}",
          f"- Secciones con kappa >= 0.60: {C['secciones_kappa_ge_060']}; mas bajas {C['tres_secciones_kappa_mas_bajo']}; Spearman con calidad rho = {r(C['spearman_kappa_vs_calidad_seccion']['rho'],2)}, p = {r(C['spearman_kappa_vs_calidad_seccion']['p'],2)}",
          f"- Cambio de kappa sin los 3 items de confidencialidad de S3: {({k: round(v, 4) for k, v in C['cambio_kappa_sin_3_items_confidencialidad_S3'].items()})}",
          '', '## Corpus', f"- Por ano: {R['corpus']['por_ano']}; S15 por ano: {({k: round(v, 1) for k, v in R['corpus']['S15_por_ano'].items()})}"]
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    R = calcular()
    if '--no-escribir' not in sys.argv:
        SALIDA.mkdir(parents=True, exist_ok=True)
        (SALIDA / 'resultados_congelados.json').write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str), encoding='utf-8')
        (SALIDA / 'cifras_de_referencia.md').write_text(cifras(R), encoding='utf-8')
    print(cifras(R))
