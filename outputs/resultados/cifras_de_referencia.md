# Cifras de referencia (generado por src/analisis_congelado.py; no editar a mano)

Toda cifra del manuscrito, en cualquier version, debe coincidir con esta hoja.

## Distribucion
- Decisiones evaluables: 3550; confiable 49.4 %, con restricciones 20.5 %, no confiable 30.1 %
- Puntaje global: media 61.6, DE 21.6, mediana 70.1, rango 28.0–92.2, IQR 38.3
- Clasificacion (33.3/66.7): {'R': 29, 'RR': 16, 'U': 5}; cortes 40/70 reclasifican 14; 25/75 reclasifican 21
- Dip de Hartigan 0.103; coeficiente de bimodalidad 0.61; intervalos vacios > 5 pts: [(28.0, 37.1), (37.1, 42.2), (48.7, 65.0), (77.6, 84.0)]

## Brecha completitud–calidad
- Spearman secciones rho 0.442 (p 0.087); items rho 0.713 (n 71)
- Items presentes en >= 90 %: 27 (> 90 %: 26); de ellos con calidad < 50: ['15.1', '16.1', '8.1']
- Secciones con brecha > 20 pts: ['S4', 'S8', 'S10', 'S12', 'S13', 'S15', 'S16']

## Secciones (calidad / completitud / brecha)
- S1: 66.3 / 84.7 / 18.3
- S2: 65.9 / 72.9 / 7.0
- S3: 59.2 / 68.4 / 9.2
- S4: 62.2 / 85.0 / 22.8
- S5: 72.0 / 77.0 / 5.0
- S6: 55.0 / 74.0 / 19.0
- S7: 76.0 / 78.0 / 2.0
- S8: 55.0 / 85.5 / 30.5
- S9: 83.5 / 100.0 / 16.5
- S10: 53.9 / 81.4 / 27.6
- S11: 46.5 / 56.7 / 10.2
- S12: 44.5 / 71.7 / 27.2
- S13: 65.0 / 90.0 / 25.0
- S14: 58.9 / 72.0 / 13.1
- S15: 49.5 / 99.0 / 49.5
- S16: 72.5 / 100.0 / 27.5

## Uso
- Industrial 72.7 (DE 19.5, mediana 75.5); domestico 50.5 (DE 17.9, mediana 47.7); diferencia 22.2
- Kruskal-Wallis H(1) = 16.3, p = 5.5e-05, eta2_H = 0.318

## Fabricante
- H(7) = 46.0, p = 8.9e-08, eta2_H = 0.928; medias {'F01': 85.3, 'F02': 46.3, 'F03': 71.8, 'F04': 75.6, 'F05': 91.3, 'F06': 37.1, 'F07': 71.9, 'F08': 28.0}
- Dunn-Bonferroni significativos: [['F01', 'F06'], ['F01', 'F08'], ['F02', 'F05'], ['F03', 'F08'], ['F04', 'F08'], ['F05', 'F06'], ['F05', 'F08']]

## Secciones criticas
- 50 FDS: 57.4 (mediana 56.5) vs 63.0 (mediana 71.6); W = 364, p = 0.008, r = 0.374
- 24 configuraciones: 67.3 vs 68.9; W = 133, p = 0.643, r = 0.095

## Indice ponderado
- w = 2: media 60.8, reclasificadas 0 {}
- w = 3: media 60.2, reclasificadas 1 {'R->RR': 1}
- w = 4: media 59.8, reclasificadas 20 {'R->RR': 10, 'RR->U': 10}
- w = 5: media 59.5, reclasificadas 20 {'R->RR': 10, 'RR->U': 10}
- Escala alternativa 25: rho con el orden base 0.967; orden identico: False
- Escala alternativa 75: rho con el orden base 0.926; orden identico: False

## Dominios
- G1: 63.8 ± 22.6; industrial 70.9, domestico 56.7, diferencia 14.3, brecha 11.5; KW uso H = 9.07, p = 0.003, eta2_H = 0.168
- G2: 63.1 ± 26.8; industrial 75.2, domestico 51.0, diferencia 24.2, brecha 15.6; KW uso H = 9.40, p = 0.002, eta2_H = 0.175
- G3: 65.5 ± 25.7; industrial 73.1, domestico 57.9, diferencia 15.2, brecha 16.2; KW uso H = 5.36, p = 0.021, eta2_H = 0.091
- G4: 57.1 ± 22.4; industrial 68.0, domestico 46.2, diferencia 21.8, brecha 20.4; KW uso H = 9.67, p = 0.002, eta2_H = 0.181
- G5: 61.5 ± 23.5; industrial 76.7, domestico 46.2, diferencia 30.4, brecha 28.8; KW uso H = 19.73, p = 0.000, eta2_H = 0.390
- Friedman 50 FDS: chi2 = 16.87, p = 0.0020, W = 0.084; 24 configuraciones: p = 0.0003, W = 0.221
- Wilcoxon G1-G2: W = 616, p = 0.8391, r = 0.029
- Wilcoxon G1-G3: W = 475, p = 0.1160, r = 0.222
- Wilcoxon G1-G4: W = 427, p = 0.0418, r = 0.288
- Wilcoxon G1-G5: W = 567, p = 0.4951, r = 0.096
- Wilcoxon G2-G3: W = 482, p = 0.3813, r = 0.124
- Wilcoxon G2-G4: W = 347, p = 0.0081, r = 0.374
- Wilcoxon G2-G5: W = 626, p = 0.9076, r = 0.016
- Wilcoxon G3-G4: W = 270, p = 0.0004, r = 0.503
- Wilcoxon G3-G5: W = 584, p = 0.9671, r = 0.006
- Wilcoxon G4-G5: W = 413, p = 0.0299, r = 0.307

## Configuraciones repetidas
- Distintas: 24; uso con 24: H = 11.49, p = 0.0007, eta2_H = 0.477; fabricante con 24: p = 0.0046
- Uso con representantes alternativos: eta2_H 0.464–0.676, p max 0.0008

## Tipologias (Ward, k = 3)
- Silueta: {2: 0.53, 3: 0.576, 4: 0.526, 5: 0.609, 6: 0.671}
- Grupo n = 30: fabricantes {'F01': 5, 'F03': 10, 'F04': 5, 'F05': 5, 'F07': 5}, media 77.96, mediana 73.5, rango 65.0–92.2
- Grupo n = 10: fabricantes {'F02': 5, 'F08': 5}, media 37.12, mediana 35.1, rango 28.0–48.7
- Grupo n = 10: fabricantes {'F06': 10}, media 37.07, mediana 37.1, rango 37.1–37.1
- 24 configuraciones: silueta 0.356
  - n = 6: {'F01': 4, 'F05': 2}, media 87.2
  - n = 12: {'F03': 10, 'F04': 1, 'F07': 1}, media 72.8
  - n = 6: {'F02': 4, 'F06': 1, 'F08': 1}, media 41.3

## Concordancia (complemento de src/kappa/verificacion_concordancia.py)
- Submuestra: {'fds': 15, 'fabricantes': 8, 'configuraciones': 14, 'usos': {'INDUSTRIAL': 8, 'DOMESTICA': 7}}; distribucion del consenso: {'confiable': 53.3, 'con_restricciones': 20.7, 'no_confiable': 26.0}
- Evaluadores frente al consenso: {'E1': (-5.9, 0.0019), 'E2': (-5.5, 0.0001)}
- Secciones con kappa >= 0.60: 13; mas bajas ['S13', 'S4', 'S3']; Spearman con calidad rho = 0.21, p = 0.44
- Cambio de kappa sin los 3 items de confidencialidad de S3: {'calidad': -0.0059, 'completitud': -0.0068}

## Corpus
- Por ano: {'2016': 5, '2018': 23, '2019': 10, '2020': 12}; S15 por ano: {'2016': 50.0, '2018': 56.5, '2019': 45.0, '2020': 39.6}
