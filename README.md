# SDS — Calidad documental de fichas de datos de seguridad del sector pinturas (Colombia)

Datos, código y documentación para reconstruir los resultados del manuscrito:

> Montaña-Oviedo, K. y Ospina-Lopez, J. P. *Documentary Gaps in Paint-Sector Safety Data Sheets: Implications for Chemical Hazard Communication.* ACS Chemical Health & Safety, manuscrito hs-2026-00106u (reenvío, octubre de 2026).

| | |
|---|---|
| Versión del manuscrito que respalda | `r2_limpio`, SHA-256 `686d9e92707794e371f0fd36ae98a9fd2d0be494ccbf479a555559cc84b7971b`. El manuscrito **no** se guarda aquí |
| Estado enviado | Etiqueta de git `reenvio-acs-2026-10` |
| Acceso | **Interno, solo los autores.** Ver *Confidencialidad* y `LICENSE` |
| Autores | Katherine Montaña-Oviedo (correspondencia), Juan P. Ospina-Lopez |

Las tablas se citan con su número **en `r2_limpio`**. Si el manuscrito cambia, hay que actualizar el mapa de resultados de este README.

## Confidencialidad

El estudio no revela fabricantes, productos ni composiciones, ni directa ni indirectamente.

- `data/raw/eval.xlsx` es el **único** archivo con nombres comerciales. Nada de su contenido debe salir del equipo ni citarse en ningún material.
- Todos los demás archivos usan los códigos `F01`–`F08`. `src/verificar_correcciones.py` comprueba que ningún archivo versionado contenga nombres comerciales.
- `data/raw/eval.xlsx` está en el historial de git desde febrero de 2026. Si alguna vez el repositorio se hiciera público, **primero** hay que limpiar el historial.

## En cinco minutos

1. **`data/processed/eval.csv` es la matriz**: 50 FDS × 75 ítems, de los que 71 son evaluables. Todos los resultados salen de ella. Identifíquela por su hash, `3e153701…`, **no por su nombre**: `data/raw/eval.csv` se llama igual y es el crudo.
2. `docs/registro_correcciones.md` explica qué cambió del crudo a la matriz (27 celdas) y por qué.
3. `src/verificar_correcciones.py` comprueba que todo cuadra (ver *Instalación*).

## Árbol

```
data/
  raw/           crudo, inmutable: eval.csv, eval.xlsx (con nombres), tool.xlsx (instrumento)
  processed/     LA MATRIZ (eval.csv) y el diccionario de ítems
  external/      codificaciones de los dos evaluadores externos y consenso de los autores
    plantillas/  plantillas EN BLANCO que se entregaron a los evaluadores (no son datos)
src/             verificación, cálculo de indicadores, figuras, concordancia
notebooks/       crudo → matriz, análisis descriptivo, figuras exploratorias
outputs/         resultados derivados; no se editan a mano
evaluation/      el instrumento, documentado por sección (cobertura parcial)
docs/            registro de correcciones, decisiones de datos, notas y prompts de revisión
.githooks/       gancho que ejecuta el verificador antes de cada commit
```

## Instalación y comprobación

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/verificar_correcciones.py     # debe terminar con «Todas las comprobaciones pasaron.»
git config core.hooksPath .githooks                # una vez por clon: activa el gancho
```

El verificador comprueba, sin escribir nada:

1. El hash de la matriz.
2. Las 27 correcciones frente al crudo.
3. La excepción de confidencialidad de la Sección 3.
4. La Tabla 3 y las cifras globales.
5. Las Tablas 1, 2 y 4.
6. Las codificaciones externas y la Tabla 5.
7. Que `notebooks/preprocessing.ipynb` regenera la matriz bit a bit desde el crudo.
8. Que no hay nombres comerciales en lo versionado.

Sale con código 0 si todo cuadra. El gancho lo ejecuta antes de cada commit y rechaza el commit si algo falla.

## De dónde sale cada resultado de `r2_limpio`

| Resultado | Se calcula desde | Lo comprueba el verificador |
|---|---|---|
| Tabla 1 — criterios e ítems por sección y dominio | `data/raw/tool.xlsx`, `evaluation/`; el número de ítems, de la matriz | número de ítems por sección y dominio |
| Tabla 2 — FDS por fabricante y uso | matriz, columnas `FABRICANTE` y `USO` | sí, completa |
| Tabla 3 — calidad, completitud y brecha por sección | matriz | calidad y completitud de las 16 secciones |
| Tabla 4 — contenidos con baja puntuación | matriz, a nivel de ítem (también en `outputs/bloque_metodologico/items_recalculados.csv`) | los 18 ítems citados |
| Tabla 5 — concordancia entre evaluadores | `data/external/` con `src/kappa/verificacion_concordancia.py` | acuerdos y kappas; **no** los IC |
| Texto: media 61,6; DE 21,6; rango 28,0–92,2 | matriz, puntaje global por FDS | sí |
| Texto: 24 configuraciones distintas | matriz | sí |
| Resumen: ítems 4.2 (27), 4.3 (32), 8.1 (48), 15.1 (98 %, 19); 84,3 %, κ = 0,757 | los mismos cálculos de las Tablas 4 y 5 | sí |

`r2_limpio` no incluye figuras en el cuerpo. Ver *Figuras*.

## Glosario

- **FDS**: ficha de datos de seguridad (en inglés, SDS). Las 16 secciones del SGA se abrevian S1–S16.
- **Ítem**: elemento que el instrumento evalúa dentro de una sección. Por ejemplo, `1.2` = «Otros medios de identificación». En la matriz, el ítem `3.2.1.1` es la pareja de columnas `ITEM_3_2_1_1` / `CALIDAD_3_2_1_1`. Los ítems `s.0` (`ITEM_1_0`, …) evalúan el título de cada sección.
- **Presencia**: `PRESENTE` si se identifica al menos un elemento requerido del ítem; `AUSENTE` si no; `NO_APLICA` para la rama de sustancias puras de S3, que no aplica a mezclas.
- **Calidad**: `CONFIABLE` = 100, `CONFI_RESTR` (confiable con restricciones) = 50, `NO_CONFIABLE` = 0. Los documentos del instrumento usan la escala equivalente 5 / 3 / 1 con los códigos `Confiable` / `Conf_CR` / `NO_Conf`.
- **Calidad de un ítem**: media de 100 / 50 / 0 sobre las 50 FDS. **Completitud de un ítem**: porcentaje de FDS en que está `PRESENTE`.
- **Calidad y completitud de una sección**: media, sin ponderar, de sus ítems evaluables.
- **Brecha**: completitud − calidad, en puntos. Una brecha grande indica que el contenido está pero se califica bajo.
- **Dominio**: agrupación de secciones de la Tabla 1. G1 = S1–S3, G2 = S4–S6, G3 = S7–S8, G4 = S9–S12, G5 = S13–S16. Su valor es la media de sus secciones.
- **Sección crítica (★)**: S2, S4, S8 y S11, las de mayor relevancia para la salud ocupacional.
- **Puntaje global de una FDS**: media, sin ponderar, de sus 16 puntajes de calidad por sección.
- **Configuración documental**: el vector completo de presencia y calidad de una FDS. Dos FDS con el mismo vector comparten configuración: es un patrón de puntuaciones, **no** prueba de que los documentos sean idénticos.
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
| `data/external/eval_original.csv` | `ddf015b57a905cc0` | **Consenso de los autores** para esas 15 FDS. Es **anterior a 11 correcciones de presencia** que sí tiene la matriz: 11 ítems fuera de S3 figuran como `AUSENTE` con calidad positiva. La Tabla 5 se reproduce leyéndolos como `PRESENTE`, que es la misma regla aplicada a la matriz (escenario 2 de `src/kappa/verificacion_concordancia.py`) |
| `data/external/plantillas/` | — | Plantillas **en blanco** entregadas a los evaluadores y su instructivo (`LEEME.txt`). **No son datos** |

`data/raw/eval.csv` y `data/processed/eval.csv` se llaman igual y **no** son el mismo archivo. En `data/external/`, «original» no significa «el crudo».

### Columnas de la matriz

| Columna | Contenido |
|---|---|
| `FDS` | Número de fila de la codificación. **No** identifica la FDS |
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

- `docs/registro_correcciones.md`: las **27 diferencias** entre el crudo y la matriz (26 de presencia y 1 de calidad), con FDS, ítem, valor anterior y valor final. Las 27 están programadas en `notebooks/preprocessing.ipynb`. La de calidad comprueba el valor anterior antes de cambiarlo; las 26 de presencia solo comprueban que la FDS exista. El verificador (grupo 2) exige que la diferencia entre crudo y matriz sea exactamente la del registro.
- `docs/PLAN_EDITORIAL_CON_CONTROLES.md`: **pese a su nombre**, es el registro de las decisiones de datos del 16 de septiembre de 2026, con el hash de la matriz y de las codificaciones y la semilla. Es un documento histórico: sus instrucciones de edición se refieren a una versión anterior del manuscrito (v8_7).

## Código

| Ruta | Qué hace |
|---|---|
| `src/verificar_correcciones.py` | Verifica la cadena completa (ver *Instalación*) |
| `src/auditoria_bloque_metodologico.py` | **Cálculo principal** de calidad, completitud y brecha por ítem, sección y dominio; compara dos matrices si se le da `--antes` |
| `src/auditoria_impacto_calidad_1_2.py` | Compara indicadores antes y después de la corrección de calidad de F03-P03-D, ítem 1.2 |
| `src/generar_figuras_completitud_actualizadas.py` | Figuras de las versiones v8 del manuscrito → `outputs/bloque_metodologico/figuras/`. Lo invoca `notebooks/figuras_articulo.ipynb` |
| `src/kappa/verificacion_concordancia.py` | **Reproduce la Tabla 5**: `python3 src/kappa/verificacion_concordancia.py data/external/eval_1.csv data/external/eval_2.csv data/external/eval_original.csv` |
| `src/kappa/` (los otros 5) | Scripts **heredados** de la selección de la submuestra, las plantillas y cálculos previos. Registro del método: **no se ejecutan tal cual** (ver su cabecera) |
| `notebooks/preprocessing.ipynb` | Crudo → matriz y diccionario. Ejecutar desde `notebooks/` |
| `notebooks/EDA.ipynb` | Análisis descriptivo |
| `notebooks/figuras_articulo.ipynb` | Figuras exploratorias → `outputs/figuras_articulo/`, y llamada al generador de figuras v8. Ejecutar desde `notebooks/` |

**Semillas.** Los intervalos de la Tabla 5 usan `20260916`: percentiles 2,5 y 97,5 de 2.000 remuestreos **por FDS completa**, no por ítem. El resto del código conserva las semillas originales: `314159`, `1000+i` y `42` en las figuras; `1496` en `kappa_analysis.py`; `2026` en la selección de la submuestra. **No se unificaron**, porque hacerlo cambiaría figuras ya producidas.

## Salidas

Todo lo de `outputs/` es **derivado** y no se edita a mano.

- `outputs/bloque_metodologico/`: recálculos por ítem, sección y dominio (`*_recalculados.csv`), las 29 excepciones de S3 (`excepciones_confidencialidad.csv`) y las correlaciones (`resumen_auditoria.json`; no se reportan en `r2_limpio`). Se regeneran con `cd notebooks && python ../src/auditoria_bloque_metodologico.py ../data/processed/eval.csv --salida <carpeta>`.
- `outputs/bloque_metodologico/cambios_*.csv` y `impacto_1_2/cambios_*.csv`: el efecto de las correcciones en dos pasos (primero las 21 de presencia, después la de calidad). Cómo se obtuvieron: `docs/salidas_cambios.md`. Los otros cuatro archivos de `impacto_1_2/` son **idénticos** a los de la carpeta madre.

### Figuras

- **`r2_limpio` no tiene figuras en el cuerpo.** Su único gráfico es el del índice (*Table of Contents*), que se preparó fuera del repositorio: **su fuente no está aquí**.
- `outputs/bloque_metodologico/figuras/`: `Figure_1_updated.png` … `Figure_4_updated.png` y `Figure_6_updated.png` son figuras de las versiones v8 del manuscrito. Las cuatro primeras son idénticas a imágenes que el archivo `r2_limpio` conserva sin mostrar. No hay `Figure_5`.
- `outputs/figuras_articulo/`: **pese al nombre**, son figuras exploratorias del cuaderno. Ninguna aparece en `r2_limpio`.

## Instrumento

`evaluation/` documenta el instrumento por sección, con **cobertura parcial**: S1, S2, S3, S9, S10 y S11. `evaluation/meta-instrumento.md` define los criterios con que se evaluó el diseño de esos documentos. Para las demás secciones, la fuente es `data/raw/tool.xlsx` y `data/processed/diccionario_items.csv`.

## Prompts de trabajo

`docs/prompts/` guarda las instrucciones usadas para revisar el inglés, el contenido científico y las figuras del manuscrito. No contienen datos. No consta cuál de las versiones se usó en último lugar.

## Convenciones

- **Un archivo, un nombre, un lugar.** Ninguna plantilla puede llamarse igual que un dato.
- `data/raw/` es inmutable. Toda corrección se programa en el preprocesamiento y se anota en el registro.
- `outputs/` es derivado; no se edita a mano.
- Antes de cada entrega: ejecutar el verificador, comitear y etiquetar el estado entregado.

## Pendiente

- Documentar el instrumento de S4–S8 y S12–S16.
- `notebooks/EDA - SDS/` (ignorada por git): borradores antiguos y artículos de terceros que deben archivarse fuera.
- Renombrar los archivos y carpetas cuyo nombre induce a error (planificado para después del reenvío).
