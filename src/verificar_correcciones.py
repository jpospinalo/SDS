#!/usr/bin/env python3
"""Verifica la cadena de datos del repositorio, de principio a fin.

    python3 src/verificar_correcciones.py

Comprueba, sin escribir nada:
  1. Que data/processed/eval.csv tiene el hash declarado en el README.
  2. Que las diferencias entre data/raw y data/processed son exactamente las
     27 del registro: 26 de presencia y 1 de calidad.
  3. Que no queda ninguna decision AUSENTE + calidad positiva fuera de S3.
  4. Que la matriz reproduce los resultados publicados por seccion y globales.
Sale con codigo 1 si alguna comprobacion falla.
"""
import csv, hashlib, sys
from collections import defaultdict, Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CRUDO = RAIZ / 'data' / 'raw' / 'eval.csv'
PROC = RAIZ / 'data' / 'processed' / 'eval.csv'
SHA_PROC = '3e153701b68d96dbab68779d6196c4df34f31eb90be3f2eb087944f6f12d7d83'

QV = {'CONFIABLE': 100.0, 'CONFI_RESTR': 50.0, 'NO_CONFIABLE': 0.0}
MP = {'Presente': 'PRESENTE', 'No Present': 'AUSENTE', '': ''}
MQ = {'Confiable': 'CONFIABLE', 'Conf_CR': 'CONFI_RESTR', 'NO_Conf': 'NO_CONFIABLE', '': ''}
# tabla de calidad y completitud por seccion, tal como se publica
PUB = {1: (66.3, 84.7), 2: (65.9, 72.9), 3: (59.2, 68.4), 4: (62.2, 85.0),
       5: (72.0, 77.0), 6: (55.0, 74.0), 7: (76.0, 78.0), 8: (55.0, 85.5),
       9: (83.5, 100.0), 10: (53.9, 81.4), 11: (46.5, 56.7), 12: (44.5, 71.7),
       13: (65.0, 90.0), 14: (58.9, 72.0), 15: (49.5, 99.0), 16: (72.5, 100.0)}

fallos = []

def check(ok, titulo, detalle=''):
    print(f"  [{'OK ' if ok else 'FALLA'}] {titulo}{'  ' + detalle if detalle else ''}")
    if not ok:
        fallos.append(titulo)

def leer_proc():
    filas = list(csv.DictReader(open(PROC, encoding='utf-8-sig')))
    celdas = {}
    for r in filas:
        for c in r:
            if c.startswith('ITEM_'):
                col = c[5:]
                p = (r[c] or '').strip()
                q = (r.get('CALIDAD_' + col) or '').strip()
                if p == 'NO_APLICA' or q == 'NO_APLICA' or (not p and not q):
                    continue
                celdas[(r['FDS'], col)] = (p, q, r['ID'])
    return filas, celdas

def leer_crudo():
    d = {}
    for r in csv.DictReader(open(CRUDO, encoding='utf-8-sig'), delimiter=';'):
        for c in r:
            if c and c.startswith('Item_'):
                col = c[5:]
                d[(r['FDS'], col)] = ((r[c] or '').strip(), (r.get('Calidad_' + col) or '').strip())
    return d

def main():
    print('1. Integridad de la matriz')
    h = hashlib.sha256(PROC.read_bytes()).hexdigest()
    check(h == SHA_PROC, 'data/processed/eval.csv coincide con el hash declarado', h[:16])

    filas, proc = leer_proc()
    crudo = leer_crudo()
    check(len(filas) == 50, 'la matriz tiene 50 FDS', str(len(filas)))
    check(len(proc) == 3550, 'hay 3.550 decisiones evaluables', str(len(proc)))

    print('\n2. Correcciones frente al crudo')
    pres, cal = [], []
    for k, (p, q, ident) in proc.items():
        if k not in crudo:
            continue
        rp, rq = crudo[k]
        ep, eq = MP.get(rp, rp.upper()), MQ.get(rq, rq.upper())
        if (p, q) == (ep, eq):
            continue
        (pres if p != ep and q == eq else cal if q != eq and p == ep else pres).append((ident, k[1], ep, eq, p, q))
    check(len(pres) == 26, 'hay 26 correcciones de presencia', str(len(pres)))
    check(len(cal) == 1, 'hay 1 correccion de calidad', str(len(cal)))
    esperado = {'1.2': 1, '1.3': 10, '2.2': 1, '6.2': 5, '7.2': 2, '8.2': 2, '11.4': 2, '14.5': 3}
    real = dict(Counter(k[1].replace('_', '.') for k in pres))
    check(real == esperado, 'el reparto por item coincide con el registro', str(real))

    print('\n3. Excepcion de confidencialidad')
    fuera = [k for k, (p, q, _) in proc.items() if p == 'AUSENTE' and QV.get(q, 0) > 0 and not k[1].startswith('3_')]
    dentro = [k for k, (p, q, _) in proc.items() if p == 'AUSENTE' and QV.get(q, 0) > 0 and k[1].startswith('3_')]
    check(len(fuera) == 0, 'ninguna ausencia con calidad positiva fuera de S3', str(len(fuera)))
    check(len(dentro) == 29, 'las 29 excepciones de S3 se conservan', str(len(dentro)))

    print('\n4. Resultados publicados')
    sec = defaultdict(lambda: defaultdict(list))
    punt = []
    for r in filas:
        per = defaultdict(list)
        for c in r:
            if c.startswith('ITEM_'):
                col = c[5:]
                p = (r[c] or '').strip()
                q = (r.get('CALIDAD_' + col) or '').strip()
                if p == 'NO_APLICA' or q == 'NO_APLICA' or (not p and not q):
                    continue
                s = int(col.split('_')[0])
                per[s].append(QV.get(q, 0.0))
                sec[s][col].append((p == 'PRESENTE', QV.get(q, 0.0)))
        punt.append(sum(sum(v) / len(v) for _, v in sorted(per.items())) / len(per))
    mal = []
    for s in range(1, 17):
        it = sec[s]
        q = sum(sum(x[1] for x in v) / len(v) for v in it.values()) / len(it)
        c = sum(100 * sum(1 for x in v if x[0]) / len(v) for v in it.values()) / len(it)
        if abs(round(q, 1) - PUB[s][0]) >= 0.05 or abs(round(c, 1) - PUB[s][1]) >= 0.05:
            mal.append('S%d' % s)
    check(not mal, 'las 16 secciones reproducen la tabla publicada', ','.join(mal))
    media = sum(punt) / len(punt)
    check(round(media, 1) == 61.6, 'la media global es 61,6', f'{media:.4f}')
    cfg = {tuple((r[c] or '').strip() + '|' + (r.get('CALIDAD_' + c[5:]) or '').strip()
                 for c in r if c.startswith('ITEM_')) for r in filas}
    check(len(cfg) == 24, 'hay 24 configuraciones distintas', str(len(cfg)))

    print()
    if fallos:
        print(f'FALLARON {len(fallos)} comprobaciones:')
        for f in fallos:
            print('   -', f)
        return 1
    print('Todas las comprobaciones pasaron.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
