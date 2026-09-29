#!/usr/bin/env python3
"""Reproduce el bloque de concordancia del manuscrito desde las tres codificaciones.

    python3 verificacion_concordancia.py eval_1.csv eval_2.csv eval_original.csv

Valida los insumos antes de calcular y ABORTA si alguna suposicion no se cumple:
claves duplicadas, claves que no coinciden entre los tres archivos, vocabulario
inesperado en PRESENCIA o CALIDAD, o una calidad vacia en un item que no esta
AUSENTE. Tambien aborta si alguna replica del bootstrap no produce un valor finito.

Calcula, en los dos escenarios de presencia del original:
  - acuerdo y kappa de Cohen (completitud)
  - acuerdo, kappa ponderado lineal y kappa sin ponderar (calidad)
  - razones de desacuerdo direccional
  - alfa de Krippendorff con distancia de intervalo Y ordinal (se reportan ambas)
  - intervalos por bootstrap de conglomerados, remuestreando FDS y no items
"""
import csv, sys, numpy as np

PRES = {'PRESENTE', 'AUSENTE'}
Q = {'NO_CONFIABLE': 0, 'CONFIABLE_CON_RESTRICCIONES': 1, 'CONFIABLE': 2}
VAL = {0: 0.0, 1: 50.0, 2: 100.0}
# Referencia reproducible: 2000 replicas por FDS, default_rng(20260916).
PUB = {'E1-E2':       {'comp': (92.0, 0.775, '0.690-0.833'), 'cal': (84.3, 0.757, '0.694-0.809')},
       'E1-consenso': {'comp': (95.1, 0.854, '0.788-0.897'), 'cal': (90.4, 0.842, '0.781-0.888')},
       'E2-consenso': {'comp': (95.0, 0.853, '0.799-0.892'), 'cal': (89.6, 0.836, '0.789-0.873')}}

def load(path, flip=False):
    d, dup = {}, []
    for i, r in enumerate(csv.DictReader(open(path, encoding='utf-8-sig')), 2):
        pres = (r['PRESENCIA'] or '').strip().upper()
        cal = (r['CALIDAD'] or '').strip().upper()
        sec, key = r['SECCION'].strip(), (r['FDS_ID'].strip(), r['ITEM'].strip())
        if pres not in PRES:
            sys.exit(f'{path}:{i} PRESENCIA no reconocida: {pres!r}')
        if cal == '':
            # unico caso admitido: el item esta AUSENTE, y entonces la calidad es cero
            if pres != 'AUSENTE':
                sys.exit(f'{path}:{i} calidad vacia en un item PRESENTE: {key}')
            cal = 'NO_CONFIABLE'
        if cal not in Q:
            sys.exit(f'{path}:{i} CALIDAD no reconocida: {cal!r}')
        if key in d:
            dup.append(key)
        if flip and pres == 'AUSENTE' and Q[cal] > 0 and sec != 'S3':
            pres = 'PRESENTE'
        d[key] = (pres, Q[cal], sec)
    if dup:
        sys.exit(f'{path}: {len(dup)} claves FDS-item duplicadas, p.ej. {dup[:3]}')
    return d

def coef(a, b, k, weighted):
    M = np.zeros((k, k))
    for x, y in zip(a, b):
        M[x, y] += 1
    n = M.sum()
    w = np.array([[1 - abs(i - j) / (k - 1) for j in range(k)] for i in range(k)]) if weighted else np.eye(k)
    r, c = M.sum(1) / n, M.sum(0) / n
    po = (M * w).sum() / n
    pe = sum(w[i, j] * r[i] * c[j] for i in range(k) for j in range(k))
    return 100 * np.trace(M) / n, (po - pe) / (1 - pe), M

def alpha(mat, metric):
    # mat: codificadores x unidades, con nan para faltantes
    vals = sorted({v for row in mat for v in row if not np.isnan(v)})
    idx = {v: i for i, v in enumerate(vals)}
    n = len(vals)
    coinc = np.zeros((n, n))
    for u in range(mat.shape[1]):
        col = [v for v in mat[:, u] if not np.isnan(v)]
        m = len(col)
        if m < 2:
            continue
        for x in col:
            for y in col:
                if x is not y:
                    coinc[idx[x], idx[y]] += 1 / (m - 1)
    nc = coinc.sum(1)
    N = coinc.sum()
    if metric == 'interval':
        D = np.array([[(a - b) ** 2 for b in vals] for a in vals], float)
    else:  # ordinal
        cum = [nc[k] / 2 + sum(nc[:k]) for k in range(n)]
        D = np.array([[(cum[a] - cum[b]) ** 2 for b in range(n)] for a in range(n)], float)
    do = (coinc * D).sum()
    de = sum(nc[i] * nc[j] * D[i, j] for i in range(n) for j in range(n)) / (N - 1)
    return 1 - do / de

def bootstrap(A, B, keys, k, weighted, seed=20260916, B_=2000):
    fds = sorted({f for f, _ in keys})
    porf = {f: [kk for kk in keys if kk[0] == f] for f in fds}
    rng = np.random.default_rng(seed)
    out, descartadas = [], 0
    for _ in range(B_):
        sel = rng.choice(len(fds), len(fds), replace=True)
        kk = [x for i in sel for x in porf[fds[i]]]
        try:
            v = coef([A[x][1] if k == 3 else (1 if A[x][0] == 'PRESENTE' else 0) for x in kk],
                     [B[x][1] if k == 3 else (1 if B[x][0] == 'PRESENTE' else 0) for x in kk],
                     k, weighted)[1]
        except Exception:
            v = float('nan')
        if np.isfinite(v):
            out.append(v)
        else:
            descartadas += 1
    if descartadas:
        sys.exit(f'bootstrap: {descartadas} de {B_} replicas no dieron un valor finito. '
                 f'Revise los datos antes de informar intervalos.')
    return np.percentile(out, 2.5), np.percentile(out, 97.5)

def bloque(E1, E2, OR, titulo, boot):
    keys = sorted(set(E1) & set(E2) & set(OR))
    for nom, D in (('eval_1', E1), ('eval_2', E2), ('original', OR)):
        sobran = sorted(set(D) - set(keys))
        if sobran:
            sys.exit(f'{nom}: {len(sobran)} claves sin correspondencia en los otros archivos, '
                     f'p.ej. {sobran[:3]}. No se calcula sobre una interseccion parcial.')
    print(f'\n{titulo}   ({len(keys)} juicios)')
    for nom, A, B in [('E1-E2', E1, E2), ('E1-consenso', E1, OR), ('E2-consenso', E2, OR)]:
        pa = [1 if A[x][0] == 'PRESENTE' else 0 for x in keys]
        pb = [1 if B[x][0] == 'PRESENTE' else 0 for x in keys]
        ac, kc, _ = coef(pa, pb, 2, False)
        aq, kq, M = coef([A[x][1] for x in keys], [B[x][1] for x in keys], 3, True)
        _, ku, _ = coef([A[x][1] for x in keys], [B[x][1] for x in keys], 3, False)
        sev, ind = M[0, 1] + M[0, 2] + M[1, 2], M[1, 0] + M[2, 0] + M[2, 1]
        p = PUB[nom]
        print(f'  {nom}')
        print(f'     completitud  {ac:5.1f}% k={kc:.3f}   publicado {p["comp"][0]}% {p["comp"][1]}')
        print(f'     calidad      {aq:5.1f}% kw={kq:.3f} (sin ponderar {ku:.3f})   publicado {p["cal"][0]}% {p["cal"][1]}')
        print(f'     desacuerdo direccional  {sev/ind:.2f}:1  ({int(sev)} vs {int(ind)})')
        if boot:
            lc = bootstrap(A, B, keys, 2, False); lq = bootstrap(A, B, keys, 3, True)
            print(f'     IC95 bootstrap  completitud {lc[0]:.3f}-{lc[1]:.3f} (pub {p["comp"][2]}) | '
                  f'calidad {lq[0]:.3f}-{lq[1]:.3f} (pub {p["cal"][2]})')
    m = np.array([[VAL[D[x][1]] for x in keys] for D in (E1, E2, OR)], float)
    pr = np.array([[1.0 if D[x][0] == 'PRESENTE' else 0.0 for x in keys] for D in (E1, E2, OR)], float)
    print(f'  alfa de Krippendorff, 3 codificaciones (incluye el consenso: es un resumen descriptivo,')
    print(f'     no una tercera estimacion independiente)')
    print(f'     calidad      intervalo {alpha(m, "interval"):.4f}   ordinal {alpha(m, "ordinal"):.4f}   publicado 0.813 (intervalo)')
    print(f'     completitud  intervalo {alpha(pr, "interval"):.4f}                        publicado 0.826')

def main(f1, f2, fo, boot=True):
    E1, E2 = load(f1), load(f2)
    base = load(fo)
    anom = [k for k, v in base.items() if v[0] == 'AUSENTE' and v[1] > 0]
    fuera = [k for k in anom if base[k][2] != 'S3']
    print(f'validacion de insumos: OK')
    print(f'AUSENTE con calidad positiva en el original: {len(anom)}  '
          f'(en S3: {len(anom)-len(fuera)}, fuera de S3: {len(fuera)})')
    bloque(E1, E2, base, 'ESCENARIO 1 - los CSV tal como estan', boot)
    bloque(E1, E2, load(fo, True), 'ESCENARIO 2 - los de fuera de S3 leidos como PRESENTE', boot)
    print('\nEl escenario 2 es el adoptado en el repositorio: aplica a las 11 decisiones')
    print('fuera de S3 la regla de presencia documentada en docs/registro_correcciones.md.')
    print('El escenario 1 se conserva como contraste historico; no es otra matriz final.')

if __name__ == '__main__':
    main(*sys.argv[1:4], boot='--sin-bootstrap' not in sys.argv)
