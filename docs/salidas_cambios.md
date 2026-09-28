# Cómo se obtuvieron los archivos cambios_*.csv

Los `cambios_*.csv` descomponen el efecto de las correcciones en **dos pasos encadenados**, y cada uno compara dos estados intermedios que no se guardan como archivo:

1. `outputs/bloque_metodologico/cambios_*.csv` — efecto de las **21 correcciones de presencia** posteriores a la versión v8_7. *Antes*: la matriz final con esas 21 celdas devueltas a `AUSENTE` y la calidad de F03-P03-D/1.2 devuelta a `CONFIABLE`. *Después*: la matriz final con solo esa calidad devuelta a `CONFIABLE`. Por eso su columna «después» para la brecha de 1.2, S1 y G1 no coincide con `items_recalculados.csv`: todavía no incluye la corrección de calidad.
2. `outputs/bloque_metodologico/impacto_1_2/cambios_*.csv` — efecto aislado de la **corrección de calidad**. *Antes*: el «después» del paso 1. *Después*: la matriz final.

Ambos pasos se verificaron reconstruyendo esos estados desde `data/processed/eval.csv` y `docs/registro_correcciones.md`: los seis archivos se reproducen byte a byte. El paso 1 requiere llamar a `calcular(..., validar_excepciones=False)`, porque su estado «después» tiene 30 ausencias con calidad positiva (las 29 de S3 más F03-P03-D/1.2).
