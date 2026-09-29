# SDS — Calidad documental de fichas de datos de seguridad del sector pinturas (Colombia)

Datos, código y documentación que respaldan los resultados del estudio de calidad documental de 50 fichas de datos de seguridad (FDS) de fabricantes colombianos de pinturas. Autores: Katherine Montaña-Oviedo (correspondencia) y Juan P. Ospina-Lopez. **Repositorio interno, solo para los autores**: ver *Confidencialidad* y `LICENSE`.

## Qué está congelado y qué no

| Componente | Estado |
|---|---|
| Datos (`data/`) | **Congelados.** Cada archivo se identifica por su SHA-256 (ver *Datos*) |
| Análisis estadísticos y sus resultados | **Congelados.** `src/analisis_congelado.py` los calcula desde los datos; `src/resultados_esperados.py` fija sus valores; el verificador exige que coincidan |
| Manuscrito | **No está en el repositorio ni anclado a él.** Su redacción, estilo, diagramación y numeración de tablas y figuras cambian entre el equipo |

**Regla para el manuscrito:** cualquier cifra de cualquier versión debe coincidir con `outputs/resultados/cifras_de_referencia.md`. Si no coincide, se corrige el manuscrito, no el repositorio. Por eso este README nombra los resultados por su contenido y nunca por el número de tabla o figura.

**Cambiar un análisis o un resultado** es una decisión del equipo, no una edición. Exige un commit que modifique `src/resultados_esperados.py` y explique en su mensaje qué cambió y por qué. El estado congelado actual lleva la etiqueta de git `analisis-congelado`.

## Confidencialidad

El estudio no revela fabricantes, productos ni composiciones, ni directa ni indirectamente.

- `data/raw/eval.xlsx` es el **único** archivo con nombres comerciales. Nada de su contenido debe salir del equipo ni citarse en ningún material.
- Todos los demás archivos usan los códigos `F01`–`F08`. `src/verificar_correcciones.py` comprueba que ningún archivo versionado contenga nombres comerciales.
- `data/raw/eval.xlsx` está en el historial de git desde febrero de 2026. Si alguna vez el repositorio se hiciera público, **primero** hay que limpiar el historial.

## En cinco minutos

1. **`data/processed/eval.csv` es la matriz**: 50 FDS × 75 ítems, de los que 71 son evaluables. Todos los resultados salen de ella. Identifíquela por su hash, `3e153701…`, **no por su nombre**: `data/raw/eval.csv` se llama igual y es el crudo.
2. `docs/registro_correcciones.md` explica qué cambió del crudo a la matriz (27 celdas) y por qué.
3. `outputs/resultados/cifras_de_referencia.md` reúne todas las cifras del estudio, redondeadas como se reportan. Es la hoja que hay que consultar al redactar.
4. `src/verificar_correcciones.py` comprueba que todo cuadra (ver *Instalación*).

## Árbol

```
data/
  raw/           crudo, inmutable: eval.csv, eval.xlsx (con nombres), tool.xlsx (instrumento)
  processed/     LA MATRIZ (eval.csv) y el diccionario de ítems
  external/      codificaciones de los dos evaluadores externos y consenso de los autores
    plantillas/  plantillas EN BLANCO que se entregaron a los evaluadores (no son datos)
src/             análisis congelados, valores esperados, verificación, figuras, concordancia
notebooks/       crudo → matriz, análisis descriptivo, figuras exploratorias
outputs/         resultados derivados; no se editan a mano
  resultados/    todas las cifras del estudio (JSON completo y hoja de cifras)
evaluation/      el instrumento, documentado por sección (cobertura parcial)
docs/            registro de correcciones, decisiones de datos, notas y prompts de revisión
.githooks/       gancho que ejecuta el verificador antes de cada commit
```

## Instalación y comprobación

Requiere Python 3.11 o superior (el entorno de referencia es 3.13); con Python 3.10 la instalación de pandas 3.0.1 falla.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/verificar_correcciones.py     # debe terminar con «Todas las comprobaciones pasaron.»
.venv/bin/python src/analisis_congelado.py         # regenera outputs/resultados/
git config core.hooksPath .githooks                # una vez por clon: activa el gancho
```

El verificador comprueba, sin escribir nada:

1. El hash de la matriz.
2. Las 27 correcciones frente al crudo, celda por celda.
3. La excepción de confidencialidad de la Sección 3.
4. La calidad y la completitud de las 16 secciones y las cifras globales.
4b. El número de ítems por sección y dominio, la distribución por fabricante y uso, los valores de ítem citados y la dispersión del puntaje global.
5. Las codificaciones externas y la concordancia entre evaluadores.
6. Que `notebooks/preprocessing.ipynb` regenera la matriz bit a bit desde el crudo.
7. Que no hay nombres comerciales en lo versionado, ni imágenes con marcas de IA generativa (C2PA).
8. Que `src/analisis_congelado.py` reproduce todos los valores de `src/resultados_esperados.py`.

La numeración coincide con los grupos que imprime el verificador. Sale con código 0 si todo cuadra, y el gancho rechaza cualquier commit que lo rompa.

## Resultados y dónde se calculan

| Resultado | Se calcula en | Lo protege el grupo |
|---|---|---|
| Calidad, completitud y brecha por sección | `src/analisis_congelado.py` (`secciones`); también `src/auditoria_bloque_metodologico.py` | 4 y 8 |
| Calidad y completitud por ítem; ítem más débil de cada sección | `analisis_congelado` (`items`, `brecha`) | 4b y 8 |
| Distribución de decisiones, puntaje global, clasificación de FDS, bimodalidad y sensibilidad a los puntos de corte | `analisis_congelado` (`distribucion`) | 4, 4b y 8 |
| Asociación entre completitud y calidad (Spearman) | `analisis_congelado` (`brecha`) | 8 |
| Diferencias entre FDS industriales y domésticas | `analisis_congelado` (`uso`) | 8 |
| Diferencias entre fabricantes y comparaciones por pares | `analisis_congelado` (`fabricante`) | 8 |
| Tipologías documentales (Ward) | `analisis_congelado` (`tipologias`) | 8 |
| Secciones críticas frente a no críticas | `analisis_congelado` (`criticas`) | 8 |
| Índice ponderado por criticidad y escala alternativa | `analisis_congelado` (`ponderado`, `escala_alternativa`) | 8 |
| Dominios funcionales | `analisis_congelado` (`dominios`) | 8 |
| Sensibilidad a las configuraciones repetidas | `analisis_congelado` (`configuraciones`) | 8 |
| Concordancia entre evaluadores: acuerdos, kappas e IC | `src/kappa/verificacion_concordancia.py` | 5 |
| Concordancia: submuestra, sesgo frente al consenso, kappas por sección | `analisis_congelado` (`concordancia`) | 8 |
| Criterios e ítems por sección y dominio | `data/raw/tool.xlsx`, `evaluation/`; recuento de ítems desde la matriz | 4b |
| Corpus por año de elaboración y fabricante | `analisis_congelado` (`corpus`) | 8 |

### Convenciones estadísticas fijadas

Cambiar cualquiera de estas cambia resultados congelados. El detalle está en la cabecera de `src/analisis_congelado.py`.

- **Empates:** entradas de pruebas de rangos normalizadas a 10 decimales; comprobación independiente contra fracciones exactas con `src/verificar_convenciones.py`. No se redondean los descriptivos ni las entradas de Ward.
- **Kruskal–Wallis** con corrección por empates. Tamaño del efecto **η²_H = (H − k + 1)/(n − k)**; no es ε².
- **Wilcoxon** pareado, bilateral y asintótico, `zero_method='wilcox'`, sin corrección de continuidad; r = |z|/√n_no_cero, usando el z estandarizado del mismo cálculo.
- **Friedman** con W de Kendall = χ²/(n(k − 1)). **Dunn** con corrección de Bonferroni.
- **Ward** (distancia euclidiana) sobre los puntajes de calidad por sección de las 50 FDS, con k = 3.
- **Configuraciones repetidas:** se toma como representante la primera FDS de cada configuración según la columna `FDS`.
- **Clasificación de FDS:** ≥ 66,7 confiable; ≥ 33,3 con restricciones; < 33,3 no confiable.
- **IQR** con interpolación lineal.

El ajuste autorizado del 28 de septiembre conserva todas las matrices y queda explicado en `docs/convenciones_estadisticas_20260928.md`. La etiqueta `analisis-congelado` identifica el estado anterior y no se mueve. Ejecutar también `python src/verificar_convenciones.py` antes de una entrega. Las once revisiones de valores esperados tienen justificación individual; no son ajustes de datos para coincidir con un manuscrito.

## Glosario

- **FDS**: ficha de datos de seguridad (en inglés, SDS). Las 16 secciones del SGA se abrevian S1–S16.
- **Ítem**: elemento que el instrumento evalúa dentro de una sección. Por ejemplo, `1.2` = «Otros medios de identificación». En la matriz, el ítem `3.2.1.1` es la pareja de columnas `ITEM_3_2_1_1` / `CALIDAD_3_2_1_1`. Los ítems `s.0` (`ITEM_1_0`, …) evalúan el título de cada sección.
- **Presencia**: `PRESENTE` si se identifica al menos un elemento requerido del ítem; `AUSENTE` si no; `NO_APLICA` para la rama de sustancias puras de S3, que no aplica a mezclas.
- **Calidad**: `CONFIABLE` = 100, `CONFI_RESTR` (confiable con restricciones) = 50, `NO_CONFIABLE` = 0. Los documentos del instrumento usan la escala equivalente 5 / 3 / 1 con los códigos `Confiable` / `Conf_CR` / `NO_Conf`.
- **Calidad de un ítem**: media de 100 / 50 / 0 sobre las 50 FDS. **Completitud de un ítem**: porcentaje de FDS en que está `PRESENTE`.
- **Calidad y completitud de una sección**: media, sin ponderar, de sus ítems evaluables.
- **Brecha**: completitud − calidad, en puntos. Una brecha grande indica que el contenido está pero se califica bajo.
- **Dominio**: agrupación analítica de secciones. G1 = S1–S3, G2 = S4–S6, G3 = S7–S8, G4 = S9–S12, G5 = S13–S16. Su valor es la media de sus secciones.
- **Sección crítica**: S2, S4, S8 y S11, las de mayor relevancia para la salud ocupacional.
- **Puntaje global de una FDS**: media, sin ponderar, de sus 16 puntajes de calidad por sección.
- **Configuración documental**: el vector completo de presencia y calidad de una FDS. Las 50 FDS tienen 24 configuraciones distintas. Dos FDS con el mismo vector comparten configuración: es un patrón de puntuaciones, **no** prueba de que los documentos sean idénticos.
- **Excepción de confidencialidad**: en S3, un ítem `AUSENTE` puede tener calidad positiva porque se califica cómo se trata la información reservada. Son 29 decisiones en 11 FDS. Fuera de S3 esa combinación no existe.
- **Submuestra de concordancia**: 15 FDS × 71 ítems = 1.065 juicios por codificación.

## Datos

| Archivo | SHA-256 (16) | Qué es |
|---|---|---|
| `data/raw/eval.csv` | `7574b0b74bc7b765` | Codificación de los autores **antes** de las correcciones, anonimizada. Separador `;`. **No se reescribe nunca** |
| `data/raw/eval.xlsx` | `366bb47d633b9c56` | Libro de trabajo de la codificación, **sin anonimizar** (8 hojas). No se ha verificado que equivalga a `eval.csv`. Uso interno |
| `data/raw/tool.xlsx` | `ba0019922c5e7b26` | El instrumento de 75 ítems: criterios y glosario. Fuente normativa |
| `data/processed/eval.csv` | `3e153701b68d96db` | **La matriz**: 50 FDS × 75 ítems (71 evaluables), con las 27 correcciones |
| `data/processed/diccionario_items.csv` | `d513f3d6ba54b640` | Identificador, sección y descripción de los 71 ítems evaluables |
| `data/external/eval_1.csv` | `d69c39637bd96570` | Codificación del evaluador externo 1 (15 FDS) |
| `data/external/eval_2.csv` | `9b9f4ae8b21c0ec6` | Codificación del evaluador externo 2 (15 FDS) |
| `data/external/eval_original.csv` | `ddf015b57a905cc0` | **Consenso de los autores** para esas 15 FDS. Es **anterior a 11 correcciones de presencia** que sí tiene la matriz: 11 ítems fuera de S3 figuran como `AUSENTE` con calidad positiva. La concordancia se reproduce leyéndolos como `PRESENTE`, que es la misma regla aplicada a la matriz (escenario 2 de `src/kappa/verificacion_concordancia.py`) |
| `data/external/plantillas/` | — | Plantillas **en blanco** entregadas a los evaluadores y su instructivo (`LEEME.txt`). **No son datos** |

`data/raw/eval.csv` y `data/processed/eval.csv` se llaman igual y **no** son el mismo archivo. En `data/external/`, «original» no significa «el crudo».

### Columnas de la matriz

| Columna | Contenido |
|---|---|
| `FDS` | Número de fila de la codificación; también define el orden de compilación. **No** identifica la FDS |
| `ELABORADA` | Fecha de elaboración de la FDS (2016–2020) |
| `ID` | **Identificador de la FDS**: `F01-P01-I` = fabricante 01, producto 01, uso industrial (`-D` = doméstico) |
| `FABRICANTE` | `F01`–`F08` |
| `USO` | `INDUSTRIAL` o `DOMESTICA` (25 y 25) |
| `ITEM_…` / `CALIDAD_…` | 75 pares: presencia y calidad de cada ítem |

### Reglas del dato

1. Un ítem es `PRESENTE` cuando se identifica al menos uno de sus elementos requeridos.
2. Si no se identifica ninguno, es `AUSENTE` y su calidad es `NO_CONFIABLE`.
3. **Única excepción:** la confidencialidad de S3 (ver *Glosario*).
4. Fuera de S3 **no debe existir** ninguna combinación `AUSENTE` + calidad positiva. El verificador lo comprueba.

## Correcciones y decisiones

- `docs/registro_correcciones.md`: las **27 diferencias** entre el crudo y la matriz (26 de presencia y 1 de calidad), con FDS, ítem, valor anterior y valor final. Las 27 están programadas en `notebooks/preprocessing.ipynb`. La de calidad comprueba el valor anterior antes de cambiarlo; las 26 de presencia solo comprueban que la FDS exista. El verificador (grupo 2) exige que las celdas que difieren entre crudo y matriz sean exactamente las 27 del registro, con sus valores anterior y final.
- `docs/PLAN_EDITORIAL_CON_CONTROLES.md`: **pese a su nombre**, es el registro de las decisiones de datos del 16 de septiembre de 2026, con el hash de la matriz y de las codificaciones y la semilla. Es un documento histórico: sus instrucciones de edición se refieren a una versión anterior del manuscrito.

## Código

| Ruta | Qué hace |
|---|---|
| `src/analisis_congelado.py` | **Calcula todos los resultados estadísticos** desde los datos y escribe `outputs/resultados/` |
| `src/resultados_esperados.py` | **Fija los valores congelados** (unos 300). Solo cambia por decisión explícita del equipo |
| `src/verificar_correcciones.py` | Verifica la cadena completa (ver *Instalación*) |
| `src/auditoria_bloque_metodologico.py` | Calidad, completitud y brecha por ítem, sección y dominio, con correlaciones; compara dos matrices si se le da `--antes` |
| `src/auditoria_impacto_calidad_1_2.py` | Compara indicadores antes y después de la corrección de calidad de F03-P03-D, ítem 1.2 |
| `src/generar_figuras_completitud_actualizadas.py` | Genera las figuras de `outputs/bloque_metodologico/figuras/` (ver *Figuras*). Lo invoca `notebooks/figuras_articulo.ipynb` |
| `src/generar_grafico_toc.py` | Genera el gráfico del índice (*Table of Contents*) en `outputs/bloque_metodologico/figuras/` (ver *Figuras*) |
| `src/kappa/verificacion_concordancia.py` | **Reproduce la concordancia entre evaluadores**: `python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv data/external/eval_2.csv data/external/eval_original.csv` |
| `src/kappa/` (los otros 5) | Scripts **heredados** de la selección de la submuestra, las plantillas y cálculos previos. Registro del método: **no se ejecutan tal cual** (ver su cabecera) |
| `notebooks/preprocessing.ipynb` | Crudo → matriz y diccionario. Ejecutar desde `notebooks/` |
| `notebooks/EDA.ipynb` | Análisis descriptivo exploratorio |
| `notebooks/figuras_articulo.ipynb` | Figuras exploratorias → `outputs/figuras_articulo/`, y llamada al generador de figuras. Ejecutar desde `notebooks/` |

**Semillas.** Los intervalos de confianza de la concordancia usan `20260916`: percentiles 2,5 y 97,5 de 2.000 remuestreos **por FDS completa**, no por ítem. El resto del código conserva las semillas originales: `314159`, `1000+i` y `42` en las figuras; `1496` en `kappa_analysis.py`; `2026` en la selección de la submuestra. **No se unificaron**, porque hacerlo cambiaría figuras ya producidas. `src/analisis_congelado.py` no usa azar.

## Salidas

Todo lo de `outputs/` es **derivado** y no se edita a mano.

- `outputs/resultados/`: `resultados_congelados.json`, con todos los valores sin redondear, y `cifras_de_referencia.md`, con los mismos valores redondeados como se reportan. Se regeneran con `src/analisis_congelado.py`.
- `outputs/bloque_metodologico/`: recálculos por ítem, sección y dominio (`*_recalculados.csv`), las 29 excepciones de S3 (`excepciones_confidencialidad.csv`) y las correlaciones de Spearman (`resumen_auditoria.json`). Se regeneran con `cd notebooks && python ../src/auditoria_bloque_metodologico.py ../data/processed/eval.csv --salida <carpeta>`.
- `outputs/bloque_metodologico/cambios_*.csv` y `impacto_1_2/cambios_*.csv`: el efecto de las correcciones en dos pasos (primero las 21 de presencia, después la de calidad). Cómo se obtuvieron: `docs/salidas_cambios.md`. Los otros cuatro archivos de `impacto_1_2/` son **idénticos** a los de la carpeta madre.

### Figuras

Las figuras muestran resultados congelados, pero su diseño puede cambiar con el manuscrito. Los nombres de archivo son históricos: **el número que llevan no es el de la figura en el manuscrito vigente**.

- `outputs/bloque_metodologico/figuras/`, generadas por `src/generar_figuras_completitud_actualizadas.py`:
  - `Figure_1_updated.png`: completitud y categorías de calidad por sección;
  - `Figure_2_updated.png`: cuadrantes completitud–calidad por sección;
  - `Figure_3_updated.png`: calidad por tipo de uso;
  - `Figure_4_updated.png`: puntaje global por fabricante;
  - `Figure_6_updated.png`: versión anterior de la figura de dominios funcionales.
- `outputs/bloque_metodologico/figuras/TOC_graphic.png` y `.pdf`: gráfico del índice (*Table of Contents*), 3,25 × 1,75 pulgadas, generado por `src/generar_grafico_toc.py` (`--tif` añade la versión TIFF). Lee sus valores de `outputs/resultados/resultados_congelados.json`. **Debe hacerse con código, no con IA generativa:** ACS no admite imágenes generadas con IA en este gráfico, y el verificador (grupo 7) rechaza imágenes con marcas C2PA. En otra máquina la fuente puede ser Arial en lugar de Liberation Sans, con la misma métrica.
- **Sin fuente en el repositorio:** la figura de tipologías (mapa de calor por grupo de Ward) y la versión actual de la figura de dominios funcionales.
- `outputs/figuras_articulo/`: **pese al nombre**, son figuras exploratorias del cuaderno.

## Instrumento

`evaluation/` documenta el instrumento por sección, con **cobertura parcial**: S1, S2, S3, S9, S10 y S11. `evaluation/meta-instrumento.md` define los criterios con que se evaluó el diseño de esos documentos. Para las demás secciones, la fuente es `data/raw/tool.xlsx` y `data/processed/diccionario_items.csv`.

## Prompts de trabajo

`docs/prompts/` guarda las instrucciones usadas para revisar el inglés, el contenido científico y las figuras del manuscrito. No contienen datos. No consta cuál de las versiones se usó en último lugar.

## Convenciones

- **El manuscrito se ajusta al repositorio, no al revés.** Toda cifra citada sale de `outputs/resultados/cifras_de_referencia.md`.
- **Un archivo, un nombre, un lugar.** Ninguna plantilla puede llamarse igual que un dato.
- `data/raw/` es inmutable. Toda corrección se programa en el preprocesamiento y se anota en el registro.
- `outputs/` es derivado; no se edita a mano.
- Antes de cada entrega del manuscrito: ejecutar el verificador y regenerar la hoja de cifras.

## Pendiente

- Aportar el código de las figuras que no tienen fuente en el repositorio (ver *Figuras*).
- Documentar el instrumento de S4–S8 y S12–S16.
- `notebooks/EDA - SDS/` (ignorada por git): borradores antiguos y artículos de terceros que deben archivarse fuera.
- Renombrar los archivos y carpetas cuyo nombre induce a error.
