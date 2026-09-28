# Plan ejecutable del bloque metodológico — base v8_7

**Destinataria:** IA que solo puede modificar el manuscrito `.docx`.  
**Fuente:** `ARTICULO ACHS v8_7.docx`, SHA-256 `93faf4397e33f698745df68717b392fab650b261e54eb0b0269e6346bafde812`.  
**Matriz definitiva para este paquete:** `data/processed/eval.csv`, SHA-256 `3e153701b68d96dbab68779d6196c4df34f31eb90be3f2eb087944f6f12d7d83`.  
**Estado:** resultados, figuras y acuerdos de la Tabla 3 recalculados. El paquete está listo para su aplicación editorial controlada, pero el manuscrito no se declara listo para envío hasta superar los controles de la sección 4.

**Paquete que debe recibir la IA implementadora:** el manuscrito `/Users/juan/Downloads/ARTICULO ACHS v8_7.docx`, este plan y acceso de lectura a los cinco PNG de `outputs/bloque_metodologico/figuras/`. Los coeficientes y demás resultados finales ya están consignados aquí: la IA no debe recalcular ni editar CSV o notebooks. Si no puede abrir alguno de los cinco PNG, debe detener solo la sustitución de esa figura y reportarlo, sin inventar una imagen.

## 1. Decisión de datos y reproducibilidad cerradas

Frente a v8_7, la matriz incorpora **21 correcciones nuevas de presencia** (`AUSENTE` → `PRESENTE`) en los ítems 1.2, 1.3, 2.2, 6.2, 8.2 y 11.4. Las cinco correcciones anteriores de 7.2 y 14.5 ya estaban reflejadas en v8_7; no contarlas otra vez. Además, tras verificar la FDS, el equipo confirmó **una corrección nueva de calidad**: en `F03-P03-D`, ítem 1.2, la calificación correcta es 1 (`NO_CONFIABLE`, 0 puntos), no 5 (`CONFIABLE`, 100 puntos). La presencia de ese ítem permanece `AUSENTE`. Se conservó `data/raw/eval.csv` sin reescribir y la corrección quedó documentada en `notebooks/preprocessing.ipynb`.

La matriz final conserva 50 FDS, 71 ítems evaluables por FDS y 24 configuraciones distintas. Hay 29 combinaciones `AUSENTE` + calidad positiva, **todas** en la excepción de confidencialidad de S3. El caso 1.2 ya no es una excepción.

Las evaluaciones externas completas están en `data/external/eval_1.csv` y `data/external/eval_2.csv`; la codificación original de la submuestra está en `data/external/eval_original.csv`. Las tres matrices contienen los mismos **15 ID × 71 ítems = 1.065 registros**, sin claves duplicadas. Frente a `eval_original.csv`, la matriz procesada final corrige **11 presencias** dentro de esa submuestra; la calidad no cambia, pues `F03-P03-D` no pertenece a ella. La comparación entre los dos evaluadores permanece igual, mientras las comparaciones con el consenso cambian.

Huellas SHA-256 de los tres archivos para control de fuente: `eval_1.csv` = `d69c39637bd965700c3924924fe901866b2f1976cc2f2c33b5b8bc97c655dcb7`; `eval_2.csv` = `9b9f4ae8b21c0ec6c16b08026949d0c822f965acf60e6e5952eeab8b25314d4c`; `eval_original.csv` = `ddf015b57a905cc09fd33bd97d6ca32344c7554ca3148ca79a6371320ff8a334`.

**Control metodológico descubierto al reproducir la Tabla 3:** sus coeficientes antiguos solo se reproducen si toda calidad del consenso marcada `AUSENTE` se reemplaza por 0, incluso en la excepción de confidencialidad de S3. Ese reemplazo contradice la regla explícita de Métodos: en la submuestra quedan **13** juicios S3 de ausencia con calidad positiva justificada. Para la tabla final, convertir a 0 las celdas de calidad en blanco de los evaluadores externos cuando estos marcaron ausencia, pero **conservar la calidad positiva real del consenso** en esos 13 juicios. No presentar este ajuste como cambio de las calificaciones originales; corrige el cálculo del acuerdo para hacerlo coherente con ellas. Mantener la advertencia de que el consenso no es un tercer evaluador independiente.

## 2. Regla de edición

Crear `ARTICULO ACHS v8_8.docx` como copia; no sobrescribir v8_7. Modificar únicamente los pasajes y elementos indicados. Los valores numéricos son decimales calculados antes de redondear; aplicar **redondeo decimal convencional**, por ejemplo 16,25 → 16,3. No hacer sustituciones globales de números iguales en contextos distintos.

En `Assessment Instrument`, **ajustar el párrafo existente que define las escalas y la frase posterior que comienza «Where a required element is not present»**, en vez de agregar una regla redundante. Expresar la regla operativa con una sola explicación compacta:

- `PRESENT`: se identifica al menos un elemento requerido del ítem, aunque la FDS no use literalmente el subtítulo sugerido por el SGA; el título de sección se califica por separado. `ABSENT`: no se identifica ninguno.
- Calidad 100: se satisfacen todos los elementos requeridos. Calidad 50: al menos un subelemento requerido está documentado de forma pertinente, pero otro falta o es deficiente. Calidad 0: no hay ningún subelemento documentalmente suficiente —porque el ítem falta o porque lo presente es genérico, incorrecto o inconsistente—. La frase «Where a required element is not present» debe referirse a la **ausencia de todos los subelementos del ítem**, no a la falta de uno entre varios. Presencia y calidad se registran separadamente: un ítem presente puede ser no confiable.
- La única ausencia con calidad positiva que queda en la matriz final es la excepción declarada de confidencialidad de S3 (29 juicios en 11 FDS). No atribuir el subtítulo distinto de SGA del fabricante F06 al ítem 1.3; el título se valora en 1.0. No añadir una regla de desempate inexistente: las discrepancias entre los codificadores originales se resolvieron por consenso.
- Conservar explícita la distinción entre calidad documental y exactitud factual; no inferir peligros reales o cumplimiento legal de los productos.

En `Assessment Design`, retirar los dos `[n]` de años de experiencia y `[dates]`, conforme a la decisión del equipo, sin quitar la condición de evaluadores externos, independientes y pertenecientes al grupo profesional destinatario. No editar la carta al editor.

## 3. Actualizaciones exactas de texto, tablas y figuras

### Tabla 3 y prosa de reproducibilidad

Reemplazar las seis filas de la Tabla 3 por los siguientes valores, calculados sobre los 1.065 ítems con el consenso final. Los IC son percentiles de **2.000 remuestreos por FDS completa** con semilla fija `20260916`; al recalcular con otra semilla pueden variar unas milésimas. Mantener la especificación de κ nominal para completitud y ponderación lineal para calidad.

| Dimensión | Comparación | Acuerdo (%) | κ | IC 95 % |
|---|---|---:|---:|---:|
| Completitud | Evaluador 1–2 | 92,0 | 0,775 | 0,688–0,834 |
| Completitud | Evaluador 1–consenso | **95,1** | **0,854** | **0,792–0,898** |
| Completitud | Evaluador 2–consenso | **95,0** | **0,853** | **0,794–0,892** |
| Calidad | Evaluador 1–2 | 84,3 | 0,757 | 0,690–0,812 |
| Calidad | Evaluador 1–consenso | **90,4** | **0,842** | **0,777–0,891** |
| Calidad | Evaluador 2–consenso | **89,6** | **0,836** | **0,783–0,876** |

En la nota de la tabla y en el primer párrafo de `Agreement Between Evaluators`, cambiar el alfa descriptivo a **0,826 para completitud y 0,813 para calidad** (distancia intervalar para categorías 0/50/100). El par externo, que aporta la evidencia principal de reproducibilidad, conserva κ = 0,775 y 0,757; el Abstract mantiene κ redondeados 0,78 y 0,76. Actualizar también los dos IC del par externo con los valores de la tabla para que las seis filas usen la misma corrida reproducible. La distribución 53,3/20,7/26,0 % de calidad de la submuestra **no cambia**, porque deriva de las categorías originales del consenso, no del reemplazo erróneo de las ausencias durante el cálculo antiguo.

En ese mismo primer párrafo, corregir la sensibilidad que excluye los tres ítems de composición de S3. Con los datos externos, κ de calidad ponderado pasa de **0,757 a 0,751** (cambio −0,006) y κ de completitud de **0,775 a 0,768** (cambio −0,007). Sustituir la afirmación «leaves completeness unchanged» por una formulación breve y exacta, por ejemplo: «Excluding the three Section 3 composition items changed the external-pair kappas by no more than 0.007». No extrapolar este resultado a las comparaciones con el consenso ni añadir una segunda prueba de sensibilidad.

En el párrafo siguiente a la tabla, cambiar los cocientes de discrepancias más severas frente al consenso de **4,0:1 y 5,2:1** a **5,8:1 y 6,9:1**. Cambiar «aproximadamente cuatro puntos menos» por **aproximadamente seis puntos menos**: las diferencias medias por FDS son 5,86 y 5,53 puntos. Bajo el mismo contraste de Wilcoxon aproximado usado para los valores previos, actualizar `p = 0.004` y `p = 0.001` a **`p = 0.002` y `p = 0.001`**, respectivamente. No modificar el acuerdo entre evaluadores, la proporción de 13/16 secciones, la correlación seccional ni los demás resultados basados solo en ellos.

### Resumen y distribución general

- Abstract: `49.5%` de evaluaciones confiables → **`49.4%`**. Las otras dos proporciones son 20,5 % y 30,1 %. La media global sigue redondeando a 61,6, SD a 21,6 y 58 % de FDS alcanzan el umbral. Recontar el resumen: debe seguir ≤250 palabras.
- En `Sectional Completeness and Overall Quality Distribution`, cambiar también 49,5 % → **49,4 %** y **eliminar** la aclaración de que las tres proporciones no suman 100 %: ahora 49,4 + 20,5 + 30,1 = 100,0.
- La menor completitud seccional: S11 **56,7 %** (antes 56,0 %). Reescribir solo la agrupación S6/S12/S14: S12 = 71,7 %, S14 = 72,0 % y S6 = **74,0 %**; S6 ya no pertenece al intervalo 71,5–72,0 %.
- En el párrafo de bimodalidad, la brecha de puntuaciones es **48,7–65,0** (antes 48,7–66,0), y la FDS aislada puntúa **65,0** (antes 66,0). El dip test permanece D = 0,103, p < 0,001; el coeficiente de bimodalidad permanece 0,61. El otro intervalo 28,0–37,1 no cambia. No alterar el pasaje posterior sobre *ocho de las diez FDS que alcanzan 66,0 en el índice ponderado*: se refiere a otra puntuación y sigue correcto.

### Tabla 4: cinco filas (las demás intactas)

| Sección | Calidad nueva | Completitud nueva | Brecha nueva |
|---|---:|---:|---:|
| S1 | **66,3** (antes 66,7) | **84,7** (antes 81,0) | **18,3** (antes 14,3) |
| S2 | 65,9 | **72,9** (antes 72,6) | **7,0** (antes 6,7) |
| S6 | 55,0 | **74,0** (antes 71,5) | **19,0** (antes 16,5) |
| S8 | 55,0 | **85,5** (antes 84,5) | **30,5** (antes 29,5) |
| S11 | 46,5 | **56,7** (antes 56,0) | **10,2** (antes 9,5) |

### Brecha e ítems

- `Completeness–Quality Gap (C)`: ρ seccional **0,442**, p **0,087** (n = 16); ρ por ítems **0,713**, p < 0,001 (n = 71). Conservar la cautela sobre potencia estadística. La afirmación «seis secciones adicionales con brecha >20 puntos» sigue correcta.
- `Section-Level Item Analysis`: ítem 2.2 **86 %** presente (antes 84 %); ítem 8.2 **64 %** presente y **36 %** ausente (antes 60/40). El ítem 11.4 está presente en 32 %; «fewer than a third» sigue siendo exacto. Los puntajes de calidad de 2.2 y 8.2 no cambian.

### Comparaciones, perfiles y sensibilidad

- En la comparación industrial–hogar: hogar **50,5** (antes 50,6); industrial 72,7, H = 16,2, p < 0,001 y ε² = 0,317 sin cambio. La diferencia global es **22,2** puntos (antes 22,1). Dentro de F03: industrial 74,2; hogar **69,5** (antes 69,6); diferencia **4,8** (antes 4,6). F06 sigue 37,1 frente a 37,1. Corregir las dos menciones correspondientes en la Discusión.
- En comparación por fabricante, F03 **71,8** (antes 71,9); F07 sigue 71,9. Los demás fabricantes y la prueba Kruskal–Wallis no cambian. La dispersión de F03 sube de 3,6 a 3,8, pero el texto «below 6 points for all eight manufacturers» continúa válido.
- Clustering de 50 FDS: partición, tamaños y perfiles sin cambio. Silhouette k = 3 **0,576** (antes 0,577); k = 5 (0,609) y k = 6 (0,671) intactos. Cluster 1 conserva n = 30 y mediana 73,5, pero su rango redondeado es **65–92** (antes 66–92); incluye una FDS por debajo del umbral RELIABLE, aunque sigue siendo el perfil relativamente mejor documentado. En las 24 configuraciones, el subgrupo de 12 de F03/F04/F07 tiene media **72,8** (antes 72,9); tamaño, composición y silhouette 0,356 intactos.
- Comparación de secciones críticas en 24 configuraciones: la diferencia baja a **1,6** puntos (antes 1,7); **67,3 vs. 68,9** (antes 67,3 vs. 69,0). W = 133, p = 0,643 y r = 0,099 no cambian. En las 50 FDS la media no crítica aún redondea 63,0 y el contraste 5,6; la prueba original no cambia.
- Índice ponderado: media 59,8, SD 23,0, 20 reclasificaciones y cambio medio de 1,8 puntos sin modificación al redondear. Conservar la Tabla 5 y sus resultados, incluida la referencia a los ocho documentos que puntúan 66,0 *en el índice ponderado*.

### Tabla 6 y dominio G1

La fila G1 cambia en **cuatro** celdas: `Overall (M ± SD)` **63,8 ± 22,6** (antes 63,9 ± 22,5), `HH (M)` **56,7** (antes 56,9), `Δ` **14,3** (antes 14,1), `Gap` **11,5** (antes 10,1); `IND (M)` permanece 70,9. Las brechas de las demás filas: G2 **15,6** (antes 14,7), G3 **16,3** (antes 15,8), G4 **20,4** (antes 20,2), G5 28,8 sin cambio. No modificar las demás medias, desviaciones, pruebas de Friedman ni comparaciones post hoc. En la prosa de `Functional Domain Analysis (I)`, cambiar «ranging from 14.1 points in G1» a **14,3**.

### Tabla 7

- S1: ítem 1.2 **48 %** presente y **34 puntos** (antes 46 % y 36).
- S2: ítem 2.2 **86 %** presente (antes 84 %), 57 puntos intactos.
- S6: ítem 6.2 **66 %** presente (antes 56 %), 36 puntos intactos.
- S8: ingeniería, **36 %** ausente; ítem 8.2 **64 %** presente (antes 40 % y 60 %), 27 puntos intactos. Alinear celda de deficiencia y celda de evidencia.
- S11: completitud seccional **56,7 %** (antes 56 %).
- No cambiar S7/S14: sus correcciones ya estaban en la base v8_7.

### Figuras

Insertar las imágenes listas en `outputs/bloque_metodologico/figuras/` para **Figuras 1, 2, 3, 4 y 6**. La Figura 5 puede conservarse: su única celda afectada (C1/S1) pasa de 69,44 a 68,89 y **ambas se muestran como 69** en el mapa; la partición y su leyenda son idénticas. Si el equipo requiere correspondencia pixel a pixel con la matriz, regenerarla; no es necesario para los valores publicados.

- [Figura 1](figuras/Figure_1_updated.png): corregidas ambas dimensiones y despejado el 70 %. Su nota ahora describe el orden correcto: calidad media de mayor a menor. En el pie del DOCX cambiar «highest to lowest deficiency rate» por **«highest to lowest mean quality score»**.
- [Figura 2](figuras/Figure_2_updated.png): posiciones según completitud y calidad finales.
- [Figura 3](figuras/Figure_3_updated.png): puntos individuales y perfil de S1 por uso actualizados.
- [Figura 4](figuras/Figure_4_updated.png): F03 = 71,8, puntos y orden de fabricantes actualizados. En el pie del DOCX cambiar «ordered from lowest to highest score» por **«ordered from highest to lowest score»**, que es el orden visual real.
- [Figura 6](figuras/Figure_6_updated.png): G1 y brechas revisados; línea de referencia Δ global = **22,2**. Cambiar también el dato en el pie del DOCX.

Todas las imágenes son PNG a 300 dpi, con títulos y leyendas revisados visualmente. Mantener tamaño y anclaje; comprobarlas de nuevo en el PDF renderizado, sin filas ni pies partidos.

## 4. Controles de no regresión y entrega

1. Verificar los SHA de fuente y matriz. Crear nueva versión sin sobrescribir v8_7. La IA editorial **no edita** CSV, notebooks, figuras ni material suplementario.
2. Comparar cada cambio contra esta lista y los archivos de auditoría. El único cambio de calidad de la matriz es `F03-P03-D / CALIDAD_1_2: CONFIABLE → NO_CONFIABLE`; todos los otros puntajes de calidad permanecen. El único conjunto nuevo de cambios de presencia es el de 21 celdas descrito arriba.
3. Comprobar coherencia entre Abstract, Métodos, prosa de Resultados/Discusión, Tablas 4/6/7 y Figuras 1/2/3/4/6. Evitar búsquedas-reemplazos globales: `66.0` designa dos medidas diferentes y solo cambia en el párrafo de distribución global.
4. Invariantes: 50 FDS, 71 ítems evaluables, 24 configuraciones; 29 juicios positivos de calidad con ausencia por confidencialidad de S3 (13 en la submuestra); 58 % de FDS fiables; dos fabricantes con dispersión cero; H/ε² y las comparaciones inferenciales de rango comprobadas siguen iguales al redondear. Comprobar expresamente que **los κ puntuales y los acuerdos porcentuales del par externo** y el Abstract permanecen iguales; sus dos IC cambian levemente por la nueva corrida bootstrap, y las filas contra el consenso, los alfa y la frase de sensibilidad se actualizan según la sección 3.
5. Recontar resumen (≤250 palabras), comprobar 58 referencias consecutivas, Tablas 1–7 y Figuras 1–6 presentes/citadas, sin marcadores `[n]`/`[dates]` en el cuerpo ni entidades HTML. Conciliar Tabla 3, su nota, Métodos y los dos párrafos vecinos; no dejar coeficientes anteriores aislados.
6. Renderizar el DOCX final a PDF. Examinar páginas completas, con especial atención a Tabla 3, las tablas actualizadas, las cinco figuras sustituidas, pies, leyendas y saltos de página. No dar por válida una sustitución solo porque el archivo abre.
7. Entregar un informe que cite pasaje/celda, valor previo, valor final, resultados del control y SHA de la nueva versión. **No declarar listo para envío** si falla algún control o si las seis filas de la Tabla 3 no concuerdan con el consenso corregido.

**Nota fuera del alcance de esta IA:** la Tabla S2 del material suplementario también debe sincronizarse con los ítems modificados antes del envío; las Tablas S3/S4 deben contrastarse con la codificación final de la submuestra. No encargar esos archivos a quien solo puede editar el manuscrito.

## 5. Evidencias disponibles

- `secciones_recalculadas.csv`, `items_recalculados.csv`, `dominios_recalculados.csv` y `resumen_auditoria.json`: valores finales.
- `cambios_secciones.csv`, `cambios_items.csv`, `cambios_dominios.csv`: efecto de las 21 correcciones de presencia respecto a la base de v8_7.
- `impacto_1_2/`: efecto aislado de la corrección adicional de calidad, con comparación antes/después.
- `excepciones_confidencialidad.csv`: los 29 casos justificables de S3.
- `src/auditoria_bloque_metodologico.py`, `src/auditoria_impacto_calidad_1_2.py` y `src/generar_figuras_completitud_actualizadas.py`: procedimiento reproducible; las figuras destinadas al DOCX están en `figuras/`.
