#!/usr/bin/env python3
"""Grafico del indice (Table of Contents) del articulo, dibujado solo con matplotlib.

    python3 src/generar_grafico_toc.py            # escribe TOC_graphic.png (600 dpi) y .pdf
    python3 src/generar_grafico_toc.py --tif      # ademas TOC_graphic.tif

Salida: outputs/bloque_metodologico/figuras/. Tamano ACS: 3,25 x 1,75 pulgadas.

Por que existe: la politica de ACS no admite imagenes generadas con IA en el grafico
del indice (no tienen pie de figura donde declararlo). Este grafico se genera con codigo
y el verificador (grupo 7) rechaza imagenes versionadas con marcas de IA generativa.

Los valores de las mancuernas (completitud % y calidad por seccion de S15, S8 y S4) se
leen de outputs/resultados/resultados_congelados.json: si cambian los resultados
congelados, el grafico cambia con ellos. Los recuentos (50 FDS, 8 fabricantes, 75 items,
16 secciones) se comprueban contra la matriz.
"""
import csv, json, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / 'outputs' / 'bloque_metodologico' / 'figuras'
R = json.loads((RAIZ / 'outputs' / 'resultados' / 'resultados_congelados.json').read_text(encoding='utf-8'))
filas = list(csv.DictReader(open(RAIZ / 'data' / 'processed' / 'eval.csv', encoding='utf-8-sig')))
items = [c for c in filas[0] if c.startswith('ITEM_')]
assert len(filas) == 50 and len({f['FABRICANTE'] for f in filas}) == 8 and len(items) == 75, 'recuentos inesperados'
assert len({c[5:].split('_')[0] for c in items}) == 16

plt.rcParams.update({'font.family': 'sans-serif',
                     'font.sans-serif': ['Arial', 'Liberation Sans', 'Helvetica', 'DejaVu Sans'],
                     'pdf.fonttype': 42, 'svg.hashsalt': 'toc'})

W, H = 3.25, 1.75                       # pulgadas, tamano ACS
BLUE, ORANGE, RED, TEAL = '#1f5f99', '#c46a0a', '#b3262d', '#137a6b'
FILL = {BLUE: '#e8f1fa', ORANGE: '#fdf1e2', RED: '#fbe9ea', TEAL: '#e3f4f1'}
INK, GREY = '#1d1d1d', '#6b6b6b'

# (seccion, completitud %, calidad pts) desde los resultados congelados
GAPS = [(s, R['secciones'][s]['completitud'], R['secciones'][s]['calidad']) for s in ('S15', 'S8', 'S4')]

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')

ax.text(W / 2, 1.635, 'Documentary quality of Colombian paint-sector SDSs',
        ha='center', va='center', fontsize=7.6, fontweight='bold', color=INK)

bw, gap, y0, bh = 0.70, 0.123, 0.10, 1.37
xs = [0.06 + i * (bw + gap) for i in range(4)]
cols = [BLUE, ORANGE, RED, TEAL]
for x, c in zip(xs, cols):
    ax.add_patch(FancyBboxPatch((x, y0), bw, bh, boxstyle='round,pad=0,rounding_size=0.06',
                                fc=FILL[c], ec=c, lw=0.9))
for x in xs[:-1]:
    ax.add_patch(FancyArrowPatch((x + bw + 0.012, y0 + bh / 2), (x + bw + gap - 0.012, y0 + bh / 2),
                                 arrowstyle='-|>', mutation_scale=6, lw=0.9, color=GREY))

def label(x, y, s, size, color=INK, bold=False):
    ax.text(x, y, s, ha='center', va='center', fontsize=size, color=color,
            fontweight='bold' if bold else 'normal', linespacing=1.05)

# 1. corpus: stacked documents
cx = xs[0] + bw / 2
for k, (dx, dy) in enumerate([(-0.07, 0.05), (-0.035, 0.025), (0, 0)]):
    ax.add_patch(Rectangle((cx - 0.13 + dx + 0.035, 1.03 + dy), 0.19, 0.25, fc='white', ec=BLUE, lw=0.7))
for j in range(4):
    ax.plot([cx - 0.06, cx + 0.06 - (0.03 if j == 3 else 0)], [1.22 - j * 0.045] * 2, color=BLUE, lw=0.6)
label(cx, 0.80, '50 SDSs', 8, BLUE, True)
label(cx, 0.60, '8 manufacturers', 5.8)
label(cx, 0.46, '2016–2020', 5.8)
label(cx, 0.28, 'industrial and\nhousehold', 5.8, GREY)

# 2. instrument: item grid, presence and quality recorded separately
cx = xs[1] + bw / 2
filled = [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1]
s, g = 0.05, 0.022
for i, f in enumerate(filled):
    r, c = divmod(i, 4)
    ax.add_patch(Rectangle((cx - (4 * s + 3 * g) / 2 + c * (s + g), 1.26 - r * (s + g)), s, s,
                           fc=ORANGE if f else 'white', ec=ORANGE, lw=0.6))
label(cx, 0.80, '75 items', 8, ORANGE, True)
label(cx, 0.60, '16 GHS sections', 5.8)
label(cx, 0.40, 'presence and\ncontent quality', 5.8)
label(cx, 0.22, 'rated separately', 5.8, GREY)

# 3. finding: presence is not quality (dumbbells, frozen values)
x0 = xs[2]
label(x0 + bw / 2, 1.335, 'Presence ≠\nquality', 7, RED, True)
sx0, sx1 = x0 + 0.17, x0 + bw - 0.075           # 0..100 scale
sc = lambda v: sx0 + (sx1 - sx0) * v / 100
for k, (sec, comp, qual) in enumerate(GAPS):
    y = 1.00 - k * 0.19
    ax.plot([sc(0), sc(100)], [y, y], color='#d9c3c4', lw=0.5)
    ax.plot([sc(qual), sc(comp)], [y, y], color=RED, lw=1.4, solid_capstyle='butt')
    ax.add_patch(Circle((sc(comp), y), 0.028, fc='white', ec=INK, lw=0.7, zorder=3))
    ax.add_patch(Circle((sc(qual), y), 0.028, fc=RED, ec=RED, lw=0.7, zorder=3))
    ax.text(x0 + 0.045, y, sec, ha='left', va='center', fontsize=5.8, color=INK, fontweight='bold')
ax.add_patch(Circle((x0 + 0.10, 0.36), 0.024, fc='white', ec=INK, lw=0.6))
ax.text(x0 + 0.14, 0.36, 'present (%)', ha='left', va='center', fontsize=5.4, color=INK)
ax.add_patch(Circle((x0 + 0.10, 0.23), 0.024, fc=RED, ec=RED, lw=0.6))
ax.text(x0 + 0.14, 0.23, 'quality (pts)', ha='left', va='center', fontsize=5.4, color=INK)

# 4. use: item-level review priorities (magnifier over a checklist)
cx = xs[3] + bw / 2
ax.add_patch(Rectangle((cx - 0.12, 1.02), 0.17, 0.26, fc='white', ec=TEAL, lw=0.7))
for j in range(4):
    yy = 1.23 - j * 0.055
    ax.add_patch(Rectangle((cx - 0.10, yy - 0.012), 0.024, 0.024, fc=TEAL if j != 2 else 'white', ec=TEAL, lw=0.5))
    ax.plot([cx - 0.065, cx + 0.03], [yy, yy], color=TEAL, lw=0.6)
ax.add_patch(Circle((cx + 0.075, 1.07), 0.062, fc='white', ec=TEAL, lw=1.1, zorder=4))
ax.plot([cx + 0.118, cx + 0.165], [1.027, 0.98], color=TEAL, lw=1.6, solid_capstyle='round', zorder=4)
label(cx, 0.80, 'Review\npriorities', 7, TEAL, True)
label(cx, 0.55, 'content checks\nat item level', 5.8)
label(cx, 0.30, 'S4 · S8 · S11\nS15', 5.8, GREY, True)

SALIDA.mkdir(parents=True, exist_ok=True)
fig.savefig(SALIDA / 'TOC_graphic.png', dpi=600, metadata={'Software': None})
fig.savefig(SALIDA / 'TOC_graphic.pdf', metadata={'Creator': None, 'Producer': None, 'CreationDate': None})
if '--tif' in sys.argv:
    fig.savefig(SALIDA / 'TOC_graphic.tif', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
print('Grafico del indice escrito en', SALIDA.relative_to(RAIZ))
