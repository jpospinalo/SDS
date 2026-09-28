# Registro de correcciones de la matriz de evaluación

Documenta todas las diferencias entre `data/raw/eval.csv` y `data/processed/eval.csv`.

**Obtenido por comparación directa de los dos archivos del repositorio**, celda a celda sobre las 3.550 decisiones ficha–ítem evaluables. Reproducible con `src/verificar_correcciones.py`.

| | |
|---|---|
| Crudo | `data/raw/eval.csv` · SHA-256 `7574b0b74bc7b765…` |
| Procesado | `data/processed/eval.csv` · SHA-256 `3e153701b68d96db…` |
| Decisiones comparadas | 3.550 (50 FDS × 71 ítems evaluables) |
| **Diferencias totales** | **27** |

## Resumen

| Tipo | Cantidad | Efecto |
|---|---|---|
| Corrección de **presencia**, `AUSENTE` → `PRESENTE` | **26** | La calidad no cambia |
| Corrección de **calidad**, `CONFIABLE` → `NO_CONFIABLE` | **1** | La presencia no cambia |

Las 26 de presencia corrigen ítems a los que el evaluador había asignado una calificación de calidad positiva mientras la presencia figuraba como ausente. Bajo la regla del instrumento —un ítem es `PRESENTE` cuando se identifica al menos uno de sus elementos requeridos— una calificación positiva implica que hay contenido evaluable, de modo que la presencia estaba desactualizada. **La única ausencia con calidad positiva admitida es la excepción de confidencialidad de la Sección 3**, que se conserva intacta: 29 decisiones en 11 FDS, listadas en `outputs/bloque_metodologico/excepciones_confidencialidad.csv`.

La corrección de calidad es de signo contrario y tiene otro origen: se verificó la FDS y se confirmó que la calificación correcta era `NO_CONFIABLE`. Queda documentada en `docs/PLAN_EDITORIAL_CON_CONTROLES.md`.

## Por ítem

| Ítem | Nombre | Decisiones | Tipo |
|---|---|---|---|
| 1.3 | Uso recomendado del producto y restricciones | 10 | presencia |
| 6.2 | Precauciones relativas al medio ambiente | 5 | presencia |
| 14.5 | Riesgos ambientales | 3 | presencia |
| 7.2 | Condiciones de almacenamiento seguro | 2 | presencia |
| 8.2 | Controles técnicos apropiados | 2 | presencia |
| 11.4 | Efectos inmediatos, retardados y crónicos | 2 | presencia |
| 1.2 | Otros medios de identificación | 1 | presencia |
| 2.2 | Otros peligros no clasificados | 1 | presencia |
| **1.2** | **Otros medios de identificación** | **1** | **calidad** |

## Detalle, decisión por decisión

### Correcciones de presencia (26)

| FDS | Ítem | Antes | Después |
|---|---|---|---|
| F01-P01-I | 6.2 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F01-P01-I | 7.2 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F01-P02-I | 6.2 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F01-P02-I | 7.2 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F01-P03-I | 6.2 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F02-P01-D | 6.2 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P02-D | 2.2 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P02-D | 6.2 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P03-D | 14.5 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P04-D | 8.2 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P04-D | 11.4 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P04-D | 14.5 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P05-D | 8.2 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P05-D | 11.4 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F02-P05-D | 14.5 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F03-P02-I | 1.2 | AUSENTE / CONFI_RESTR | PRESENTE / CONFI_RESTR |
| F06-P01-D | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P01-I | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P02-D | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P02-I | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P03-D | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P03-I | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P04-D | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P04-I | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P05-D | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |
| F06-P05-I | 1.3 | AUSENTE / CONFIABLE | PRESENTE / CONFIABLE |

### Corrección de calidad (1)

| FDS | Ítem | Antes | Después | Fundamento |
|---|---|---|---|---|
| F03-P03-D | 1.2 | AUSENTE / **CONFIABLE** | AUSENTE / **NO_CONFIABLE** | Verificación de la FDS. La presencia permanece `AUSENTE` |

## Efecto en los resultados publicados

Con la matriz procesada se reproducen, sin ninguna transformación adicional:

- Las 16 secciones de la tabla de calidad y completitud por sección.
- Media global 61,6159; desviación 21,6293; mediana 70,1; rango 28,0–92,2.
- 24 configuraciones documentales distintas.
- Las seis filas de la tabla de concordancia, usando `data/external/`.
- Cero decisiones de `AUSENTE` con calidad positiva fuera de la Sección 3.

## Lo que este registro no cubre

Consigna **qué** cambió y **con qué fundamento** cuando está documentado, pero no registra fecha ni responsable de cada decisión individual. Las 26 correcciones de presencia se aplicaron como un solo criterio uniforme, no caso a caso; la corrección de calidad sí tiene fundamento documental propio. Si el equipo necesita atribución nominal por decisión, debe añadirse a mano.
