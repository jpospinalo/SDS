# Cierre de convenciones estadísticas

Intervención autorizada por los autores en la conversación del 28 de septiembre de 2026. No modifica la matriz ni las codificaciones externas. Sustituye únicamente las convenciones de cálculo descritas aquí; la etiqueta histórica `analisis-congelado` se conserva.

## Motivo y decisiones

1. Los puntajes globales reconstruidos con fracciones exactas tienen 22 valores distintos; las sumas binarias sin normalizar pueden crear 24. Antes de las pruebas de rangos se normaliza a 10 decimales. El control independiente exige igualdad de rangos, empates y ceros con fracciones exactas para los puntajes globales, dominios y diferencias pareadas. Los descriptivos, ponderaciones y entradas de Ward no se modifican.
2. Wilcoxon bilateral usa explícitamente aproximación asintótica, descarte de diferencias cero y ninguna corrección de continuidad. El efecto r es el valor absoluto del z estandarizado dividido por la raíz del número de diferencias no nulas. Se evita mezclar un p exacto con un z asintótico. El mismo procedimiento se usa para G, los pares de dominios y los evaluadores frente al consenso. Los p son descriptivos en este corpus no probabilístico; la normalidad de la aproximación no elimina la dependencia entre documentos.
3. La fórmula (H-k+1)/(n-k) se denomina eta cuadrado basado en H, no epsilon cuadrado. Se calcula desde H sin redondear.

## Valores de referencia que cambian

| Resultado | Antes | Después | Motivo |
|---|---:|---:|---|
| Uso H | 16.3 | 16.2 | Empates reales |
| Uso eta2_H | 0.318 | 0.317 | Empates reales |
| G con 24 configuraciones p | 0.643 | 0.627 | Wilcoxon asintótico explícito |
| G con 24 configuraciones r | 0.095 | 0.099 | z estandarizado coherente |
| Uso con 24 configuraciones H | 11.49 | 11.30 | Empates reales |
| Uso con 24 configuraciones p | 0.0007 | 0.0008 | Empates reales |
| Uso con 24 configuraciones eta2_H | 0.477 | 0.468 | Empates reales |
| Representantes alternativos eta2_H mínimo | 0.464 | 0.456 | Empates reales |
| Representantes alternativos eta2_H máximo | 0.676 | 0.666 | Empates reales |
| Representantes alternativos p máximo | 0.0008 | 0.0009 | Empates reales |
| Evaluador 2 frente al consenso p | 0.0001 | 0.0007 | Wilcoxon asintótico explícito |

Las decisiones de significación descritas en el manuscrito no cambian. Tampoco cambian los ítems, las 16 secciones, medias descriptivas, categorías, clasificación ponderada, agrupamientos ni coeficientes kappa. Algunos resultados sin redondear de otras pruebas cambian por el tratamiento coherente de empates; la comparación completa se conserva en `outputs/resultados/cambios_convenciones.json`.

## Controles

- `python src/verificar_convenciones.py`: referencia independiente racional y consistencia de Wilcoxon.
- `python src/verificar_correcciones.py`: integridad de datos, registro de correcciones y resultados congelados.
- Los valores esperados se actualizan en las once entradas identificadas; no se regeneran automáticamente para ocultar fallos.
- La aproximación y el efecto se documentan en Methods. No se recalifica ninguna FDS.

Fuentes metodológicas: [SciPy Wilcoxon 1.17](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.wilcoxon.html) y [rstatix Kruskal effect size](https://rpkgs.datanovia.com/rstatix/reference/kruskal_effsize.html).

## Presentación y material gráfico

Las brechas de dominios se muestran con dos decimales en la hoja de referencia y la tabla del manuscrito. G3 es exactamente 16.25; la imagen aprobada lo muestra como 16.3 a un decimal. No se cambia la brecha ni se introduce otro dato. Los valores p inferiores a la precisión de presentación se muestran mediante un límite, no como cero.

La Figura 3 se regenera desde su código conservando tamaño, datos, puntos y geometría: la comparación de píxeles limita las diferencias al recuadro de la etiqueta estadística. La Figura 6 del manuscrito es una variante aprobada sin barras de error, distinta de la que actualmente genera el código del repositorio; no debe sustituirse automáticamente por esa salida. Las demás imágenes aprobadas permanecen byte a byte intactas.

Los intervalos de kappa de referencia en `src/kappa/verificacion_concordancia.py` se sincronizaron con su propio bootstrap, sin modificar estimaciones puntuales ni datos. Los seis intervalos del escenario adoptado se recalcularon y coinciden con los del manuscrito.

Entorno usado en esta verificación: Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, scikit-learn 1.8.0, scikit-posthocs 0.17.0 y diptest 0.11.0. `requirements.txt` conserva el entorno histórico de referencia; no deben mezclarse sus versiones con las de esta corrida al describir un único entorno.
