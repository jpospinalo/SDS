#!/usr/bin/env python3
"""Verifica la cadena de datos del repositorio, de principio a fin.

    python3 src/verificar_correcciones.py

Comprueba, sin escribir nada:
  1. Que data/processed/eval.csv tiene el hash declarado en el README.
  2. Que las diferencias entre data/raw y data/processed son exactamente las
     27 del registro: 26 de presencia y 1 de calidad.
  3. Que no queda ninguna decision AUSENTE + calidad positiva fuera de S3.
  4. Que la matriz reproduce los resultados de r2_limpio por seccion y globales (Tabla 3 y texto).
  4b. Que reproduce las Tablas 1, 2 y 4 y la dispersion del puntaje global.
  5. Que las codificaciones externas son las declaradas (y las plantillas estan vacias) y que la
     concordancia se reproduce desde ellas.
  6. Que preprocessing.ipynb regenera la matriz desde el crudo bit a bit.
  7. Que ningun archivo versionado contiene nombres de fabricantes o productos.
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
    # Celda a celda contra docs/registro_correcciones.md: FDS, item, valor anterior y final.
    import re
    reg = set()
    for linea in open(RAIZ / 'docs' / 'registro_correcciones.md', encoding='utf-8'):
        m = re.match(r'\|\s*(F\d\d-P\d\d-[ID])\s*\|\s*([\d.]+)\s*\|\s*([^|]+)\|\s*([^|]+)\|', linea)
        if m:
            reg.add((m.group(1), m.group(2), *(re.sub(r'[*\s]', '', g) for g in m.group(3, 4))))
    obs = {(i, c.replace('_', '.'), f'{a_}/{b_}', f'{c_}/{d_}') for i, c, a_, b_, c_, d_ in pres + cal}
    check(obs == reg and len(reg) == 27, 'las 27 celdas cambiadas son exactamente las del registro (FDS, item, antes y despues)',
          '' if obs == reg else f'solo en la matriz: {sorted(obs - reg)[:3]}; solo en el registro: {sorted(reg - obs)[:3]}')
    sin_par = sum(1 for k in proc if k not in crudo)
    check(sin_par == 0, 'toda celda evaluable de la matriz tiene su par en el crudo', str(sin_par))

    print('\n3. Excepcion de confidencialidad')
    fuera = [k for k, (p, q, _) in proc.items() if p == 'AUSENTE' and QV.get(q, 0) > 0 and not k[1].startswith('3_')]
    dentro = [k for k, (p, q, _) in proc.items() if p == 'AUSENTE' and QV.get(q, 0) > 0 and k[1].startswith('3_')]
    check(len(fuera) == 0, 'ninguna ausencia con calidad positiva fuera de S3', str(len(fuera)))
    check(len(dentro) == 29, 'las 29 excepciones de S3 se conservan', str(len(dentro)))

    print('\n4. Resultados reportados en r2_limpio (Tabla 3 y texto)')
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

    print('\n4b. Tablas 1, 2 y 4 y cifras del texto de r2_limpio')
    import statistics
    cab = [c for c in filas[0] if c.startswith('ITEM_')]
    n_sec = Counter(int(c[5:].split('_')[0]) for c in cab)
    esperado_sec = {1: 6, 2: 7, 3: 9, 4: 4, 5: 4, 6: 4, 7: 3, 8: 4, 9: 2, 10: 7, 11: 6, 12: 6, 13: 2, 14: 7, 15: 2, 16: 2}
    check(dict(n_sec) == esperado_sec and len(cab) == 75, 'Tabla 1: 75 items repartidos como en r2_limpio por seccion',
          str(dict(n_sec)) if dict(n_sec) != esperado_sec else '')
    dom = {'G1': range(1, 4), 'G2': range(4, 7), 'G3': range(7, 9), 'G4': range(9, 13), 'G5': range(13, 17)}
    esperado_dom = {'G1': 22, 'G2': 12, 'G3': 7, 'G4': 21, 'G5': 13}
    got_dom = {g: sum(n_sec[s] for s in r) for g, r in dom.items()}
    check(got_dom == esperado_dom, 'Tabla 1: items por dominio G1 22, G2 12, G3 7, G4 21, G5 13', str(got_dom) if got_dom != esperado_dom else '')

    t2 = Counter((r['FABRICANTE'].strip(), r['USO'].strip()) for r in filas)
    esperado_t2 = {('F01', 'INDUSTRIAL'): 5, ('F02', 'DOMESTICA'): 5, ('F03', 'INDUSTRIAL'): 5, ('F03', 'DOMESTICA'): 5,
                   ('F04', 'INDUSTRIAL'): 5, ('F05', 'INDUSTRIAL'): 5, ('F06', 'INDUSTRIAL'): 5, ('F06', 'DOMESTICA'): 5,
                   ('F07', 'DOMESTICA'): 5, ('F08', 'DOMESTICA'): 5}
    check(dict(t2) == esperado_t2 and sum(t2.values()) == 50, 'Tabla 2: FDS por fabricante y uso (25 industrial, 25 domestico)',
          '' if dict(t2) == esperado_t2 else str(sorted(t2.items())))

    def item_stats(col):
        v = []
        for r in filas:
            p_ = (r.get('ITEM_' + col) or '').strip(); q_ = (r.get('CALIDAD_' + col) or '').strip()
            if p_ == 'NO_APLICA' or q_ == 'NO_APLICA' or (not p_ and not q_):
                continue
            v.append((p_ == 'PRESENTE', QV.get(q_, 0.0)))
        if not v:
            return None, None
        return 100 * sum(x[0] for x in v) / len(v), sum(x[1] for x in v) / len(v)
    # item del manuscrito -> (completitud %, calidad pts); None = el manuscrito no lo reporta
    T4 = {'1.2': (48, 34), '2.2': (86, 57), '3.2.1.1': (10, 17), '4.2': (None, 27), '4.3': (None, 32),
          '5.3': (60, 58), '6.2': (66, 36), '7.2': (64, 63), '8.1': (100, 48), '8.2': (64, 27),
          '9.1': (100, 77), '10.2.1': (62, 32), '11.1': (28, 17), '12.2': (54, 33), '13.1': (80, 50),
          '14.6': (48, 48), '15.1': (98, 19), '16.1': (100, 45),
          '2.1': (64, None), '2.1.1': (66, None), '2.1.2': (64, None), '2.1.3': (66, None), '2.1.4': (64, None)}
    malos = []
    for it, (c_pub, q_pub) in T4.items():
        c_, q_ = item_stats(it.replace('.', '_'))
        if c_ is None or (c_pub is not None and int(round(c_)) != c_pub) or (q_pub is not None and int(round(q_)) != q_pub):
            malos.append(f'{it}: {c_ if c_ is None else round(c_, 1)}/{q_ if q_ is None else round(q_, 1)} vs {c_pub}/{q_pub}')
    check(not malos, 'Tabla 4: los 23 valores de items citados coinciden con la matriz', '; '.join(malos))
    cal12 = [item_stats(c[5:])[1] for c in cab if c.startswith('ITEM_12_')]
    check(len(cal12) == 6 and sum(33 <= round(x) <= 54 for x in cal12) == 5,
          'Tabla 4: cinco items de S12 con calidad entre 33 y 54', str([round(x) for x in cal12]))
    sd = statistics.stdev(punt)
    check(round(sd, 1) == 21.6 and round(min(punt), 1) == 28.0 and round(max(punt), 1) == 92.2,
          'texto: DE 21,6, minimo 28,0 y maximo 92,2 del puntaje global por FDS',
          f'DE {sd:.4f}, min {min(punt):.1f}, max {max(punt):.1f}')

    print('\n5. Codificaciones externas')
    EXT = {'eval_1.csv': ('d69c39637bd965700c3924924fe901866b2f1976cc2f2c33b5b8bc97c655dcb7', 823),
           'eval_2.csv': ('9b9f4ae8b21c0ec6c16b08026949d0c822f965acf60e6e5952eeab8b25314d4c', 816),
           'eval_original.csv': ('ddf015b57a905cc09fd33bd97d6ca32344c7554ca3148ca79a6371320ff8a334', 1065)}
    for nombre, (sha, llenas) in EXT.items():
        ruta = RAIZ / 'data' / 'external' / nombre
        ok = ruta.exists() and hashlib.sha256(ruta.read_bytes()).hexdigest() == sha
        n_llenas = -1
        if ok:
            r = list(csv.DictReader(open(ruta, encoding='utf-8-sig')))
            n_llenas = sum(1 for x in r if (x.get('CALIDAD') or '').strip())
            ok = len(r) == 1065 and n_llenas == llenas
        check(ok, f'data/external/{nombre}: hash, 1.065 filas y {llenas} calidades diligenciadas', str(n_llenas))
    for nombre in ('plantilla_evaluador_1.csv', 'plantilla_evaluador_2.csv'):
        ruta = RAIZ / 'data' / 'external' / 'plantillas' / nombre
        r = list(csv.DictReader(open(ruta, encoding='utf-8-sig'))) if ruta.exists() else []
        vacias = len(r) == 1065 and not any((x.get('CALIDAD') or '').strip() for x in r)
        check(vacias, f'plantillas/{nombre}: 1.065 filas con CALIDAD vacia (no es un dato)')
    check(not (RAIZ / 'data' / 'external' / 'plantillas' / 'eval_1.csv').exists(),
          'ninguna plantilla conserva el nombre eval_N.csv')
    import subprocess
    e = [str(RAIZ / 'data' / 'external' / n) for n in EXT]
    rc = subprocess.run([sys.executable, str(RAIZ / 'src' / 'kappa' / 'verificacion_concordancia.py'), *e],
                        capture_output=True, text=True)
    # Se comparan los valores CALCULADOS con los publicados (escenario 2, el de la Tabla 5).
    # El texto 'publicado ...' lo imprime el script como constante: no basta con buscarlo.
    import re
    esc2 = rc.stdout.split('ESCENARIO 2')[-1] if 'ESCENARIO 2' in rc.stdout else ''
    pares = re.findall(r'(\d+\.\d)% kw?=(-?\d\.\d{3}).*?publicado (\d+\.\d)% (\d\.\d{3})', esc2)
    alfas = re.findall(r'intervalo (\d\.\d{4}).*?publicado (\d\.\d{3})', esc2)
    ok_k = len(pares) == 6 and all(a == c and k == p for a, k, c, p in pares)
    ok_a = len(alfas) == 2 and all(f'{float(x):.3f}' == y for x, y in alfas)
    check(rc.returncode == 0 and ok_k and ok_a,
          'Tabla 5 de r2_limpio: 3 acuerdos y 3 kappas por dimension (puntuales; los IC no se comprueban). Ademas 2 alfas de Krippendorff que r2_limpio no reporta, como control del calculo',
          f'{sum(a == c and k == p for a, k, c, p in pares)}/6 filas, {len(alfas)} alfas')

    print('\n6. Reconstruccion de la matriz desde el crudo')
    import json, os, tempfile
    nb = json.load(open(RAIZ / 'notebooks' / 'preprocessing.ipynb', encoding='utf-8'))
    codigo = [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']
    codigo = [c for c in codigo if not c.lstrip().startswith(('!', '%')) and 'pip install' not in c]
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / 'data' / 'raw').mkdir(parents=True); (t / 'data' / 'processed').mkdir(); (t / 'notebooks').mkdir()
        (t / 'data' / 'raw' / 'eval.csv').write_bytes(CRUDO.read_bytes())
        (t / 'notebooks' / '_reconstruir.py').write_text('\n\n'.join(codigo), encoding='utf-8')
        rc = subprocess.run([sys.executable, '_reconstruir.py'], cwd=t / 'notebooks', capture_output=True, text=True,
                            env={**os.environ, 'MPLBACKEND': 'Agg'})
        gen = t / 'data' / 'processed' / 'eval.csv'
        dic = t / 'data' / 'processed' / 'diccionario_items.csv'
        check(rc.returncode == 0, 'preprocessing.ipynb se ejecuta sin errores', rc.stderr.strip()[-200:])
        check(gen.exists() and hashlib.sha256(gen.read_bytes()).hexdigest() == SHA_PROC,
              'el cuaderno regenera data/processed/eval.csv bit a bit desde data/raw/eval.csv')
        check(dic.exists() and hashlib.sha256(dic.read_bytes()).hexdigest().startswith('d513f3d6ba54b640'),
              'el cuaderno regenera diccionario_items.csv bit a bit')

    print('\n7. Ningun nombre comercial en lo versionado')
    # Se comparan huellas, no nombres: este archivo no debe contener lo que vigila.
    HUELLAS = {7: {'857d811fc120597f613b593b8ec6eaca95a4ff2146b2b8d20240dd6e0723d18c',
                   '31589223f4438fead00a992d59c6d8698448b4ecc2f59ef2e0d25db40756f2ea'},
               4: {'c904fc9e9f1289270c3eb451a6af901c80bc8871704cde507e3c62baea993488'},
               6: {'679cf303517c04fb04c35c8ab6caa5fbf3acd9e91f1423810b326737a446affb'},
               12: {'c71292e2fc02470fc96eabd3dcdb146bacde034f51ddb02eb8800f46fd6b5c58'}}
    import re
    try:
        lista = subprocess.run(['git', 'ls-files', '-z'], cwd=RAIZ, capture_output=True, text=True).stdout.split('\0')
    except OSError:
        lista = []
    if not any(lista):
        # Sin git (p. ej., copia descargada): se revisa todo el arbol salvo lo que git ignoraria.
        OMITIR = {'.git', '.venv', '_a_eliminar', 'EDA - SDS', '__pycache__'}
        lista = [str(f.relative_to(RAIZ)) for f in RAIZ.rglob('*')
                 if f.is_file() and not OMITIR.intersection(f.relative_to(RAIZ).parts)]
    EXCEPCION = {'data/raw/eval.xlsx'}   # interno, sin anonimizar; se documenta en el README
    hallazgos = []
    for rel in filter(None, lista):
        if rel in EXCEPCION or rel.lower().endswith(('.png', '.xlsx', '.docx', '.pdf')):
            continue
        f = RAIZ / rel
        if not f.exists():
            continue
        txt = f.read_bytes().decode('utf-8', errors='ignore').lower()
        for tok in set(re.findall(r'[a-z0-9]+', txt)):
            if any(len(tok) >= L and hashlib.sha256(tok[:L].encode()).hexdigest() in H for L, H in HUELLAS.items()):
                hallazgos.append(rel); break
    check(not hallazgos, 'ningun archivo versionado (codigo, salidas de cuadernos, datos) contiene nombres de fabricantes o productos',
          ', '.join(hallazgos))

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
