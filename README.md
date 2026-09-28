# SDS — Evaluación documental de fichas de datos de seguridad

Repositorio **interno** del estudio de calidad documental de FDS del sector pinturas en Colombia. Contiene los datos, el código y la documentación necesarios para reconstruir los resultados publicados.

> **Uso restringido a los autores.** `data/raw/eval.xlsx` contiene nombres comerciales de fabricantes y productos. Los archivos anonimizados (`data/raw/eval.csv` y todo `data/processed/`) usan códigos `F01`–`F08`. **Nada de `data/raw/eval.xlsx` debe salir del equipo ni citarse en material público.**

## Comprobación rápida

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/verificar_correcciones.py
```

Verifica el hash de la matriz, las 27 correcciones, la excepción de confidencialidad y que los resultados publicados se reproducen. Sale con código 0 si todo cuadra.

## La matriz

**`data/processed/eval.csv` es la única fuente de los resultados.**

```
SHA-256  3e153701b68d96dbab68779d6196c4df34f31eb90be3f2eb087944f6f12d7d83
```

**Cítela siempre por este hash, no por su ruta.** Han existido varias versiones del archivo con el mismo nombre y contenido distinto; el hash es lo único que identifica cuál es.

## Datos

| Archivo | SHA-256 (16) | Qué es |
|---|---|---|
| `data/raw/eval.csv` | `7574b0b74bc7b765` | Codificación original, anonimizada. **No se reescribe nunca** |
| `data/raw/eval.xlsx` | `366bb47d633b9c56` | Igual, **sin anonimizar**. Uso interno |
| `data/raw/tool.xlsx` | `ba0019922c5e7b26` | Instrumento de 75 ítems. Fuente normativa |
| `data/processed/eval.csv` | `3e153701b68d96db` | **La matriz.** 50 FDS × 71 ítems evaluables |
| `data/processed/diccionario_items.csv` | `d513f3d6ba54b640` | Identificador, sección y descripción de cada ítem |
| `data/external/eval_1.csv` | `d69c3963…` | Codificación del evaluador externo 1 |
| `data/external/eval_2.csv` | `9b9f4ae8…` | Codificación del evaluador externo 2 |
| `data/external/eval_original.csv` | `ddf015b5…` | Consenso de la submuestra de 15 FDS |
| `data/external/plantillas/` | — | Plantillas en blanco entregadas a los evaluadores. **No son datos** |

### Estructura de la matriz procesada

`FDS`, `ELABORADA`, `ID`, `FABRICANTE`, `USO`, y después 75 pares `ITEM_s_i` / `CALIDAD_s_i`.

- Presencia: `PRESENTE` · `AUSENTE` · `NO_APLICA`
- Calidad: `CONFIABLE` (100) · `CONFI_RESTR` (50) · `NO_CONFIABLE` (0) · `NO_APLICA`
- Los cuatro ítems de la rama de sustancias de la Sección 3 son `NO_APLICA` en las 50 FDS: los productos son mezclas. **75 − 4 = 71 ítems evaluables.**

### Reglas del dato

1. Un ítem es `PRESENTE` cuando se identifica al menos uno de sus elementos requeridos.
2. Si no se identifica ninguno, es `AUSENTE` y la calidad es `NO_CONFIABLE`.
3. **Única excepción:** la confidencialidad de la Sección 3. Ahí un ítem `AUSENTE` puede llevar calidad positiva, porque se califica el tratamiento de la omisión. Son 29 decisiones en 11 FDS.
4. Fuera de la Sección 3 **no debe existir ninguna** combinación `AUSENTE` + calidad positiva. `src/verificar_correcciones.py` lo comprueba.

## Correcciones

`docs/registro_correcciones.md` documenta las **27 diferencias** entre el crudo y la matriz: 26 correcciones de presencia y 1 de calidad, con su FDS, ítem, valor anterior y final. `docs/PLAN_EDITORIAL_CON_CONTROLES.md` recoge la decisión de datos y su fundamento.

## Código

| Ruta | Qué hace |
|---|---|
| `src/verificar_correcciones.py` | Verifica la cadena completa de datos |
| `src/auditoria_bloque_metodologico.py` | Recalcula ítem, sección y dominio; audita el impacto de las correcciones |
| `src/auditoria_impacto_calidad_1_2.py` | Audita la corrección de calidad del ítem 1.2 |
| `src/generar_figuras_completitud_actualizadas.py` | Figuras del artículo (las invoca `notebooks/figuras_articulo.ipynb`) |
| `src/kappa/verificacion_concordancia.py` | **Reproduce la Tabla 5** desde `data/external/`: `python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv data/external/eval_2.csv data/external/eval_original.csv` |
| `src/kappa/` (resto) | Scripts **heredados** de selección de submuestra, plantillas y cálculo. Registro del método; no se ejecutan tal cual (ver su cabecera) |
| `notebooks/preprocessing.ipynb` | Crudo → procesado. Documenta la corrección del ítem 1.2 |
| `notebooks/EDA.ipynb` | Análisis descriptivo |
| `notebooks/figuras_articulo.ipynb` | Figuras del artículo → `outputs/figuras_articulo/`. Ejecutar desde `notebooks/` |

**Semillas.** Los intervalos de la concordancia externa (Tabla 5, `src/kappa/verificacion_concordancia.py`) usan `20260916`: percentiles 2,5 y 97,5 de 2.000 remuestreos **por FDS completa**, no por ítem. El resto del código conserva las semillas con que se produjeron los resultados y figuras publicados —`314159`, `1000+i` y `42` en las figuras; `1496` en `kappa_analysis.py`; `2026` en la selección de la submuestra—. **No se unificaron**: hacerlo cambiaría los intervalos de las figuras ya publicadas.

## Salidas

`outputs/figuras_articulo/` contiene las figuras del artículo. `outputs/bloque_metodologico/` contiene los recálculos y los registros de cambios por ítem, sección y dominio, más `excepciones_confidencialidad.csv` con las 29 de la Sección 3. Todo es **derivado**: se regenera con el código y no se edita a mano.

## Prompts de trabajo

`docs/prompts/` guarda las instrucciones usadas en las revisiones del texto y las figuras. No contienen datos.

## Instrumento

`evaluation/` documenta el instrumento por sección. **Cobertura parcial:** S1, S2, S3, S9, S10 y S11. Para las demás, la fuente normativa es `data/raw/tool.xlsx` y `data/processed/diccionario_items.csv`.

## Convenciones

- **Un archivo, un nombre, un lugar.** Nada llamado `eval_1.csv` que sea una plantilla si existe un `eval_1.csv` que es un dato. Las plantillas van en `data/external/plantillas/` y se llaman `plantilla_*`.
- `data/raw/` es inmutable. Toda corrección se aplica en el preprocesamiento y queda en el registro.
- `outputs/` es derivado y reproducible; no se edita a mano.
- Antes de cada entrega, ejecutar `src/verificar_correcciones.py` y comitear.
