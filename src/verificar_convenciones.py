"""Control independiente de empates racionales y Wilcoxon. No escribe archivos."""
import csv
import hashlib
import math
from fractions import Fraction as F
from itertools import combinations
import numpy as np
from scipy import stats
import analisis_congelado as ac


def main():
    assert hashlib.sha256(ac.MATRIZ.read_bytes()).hexdigest() == '3e153701b68d96dbab68779d6196c4df34f31eb90be3f2eb087944f6f12d7d83'
    rows = list(csv.DictReader(ac.MATRIZ.open(encoding='utf-8-sig')))
    cols = [c for c in rows[0] if c.startswith('CALIDAD_')]
    section = []
    for row in rows:
        sec = []
        for s in range(1, 17):
            vals = [int(ac.QV[row[c]]) for c in cols if c.startswith(f'CALIDAD_{s}_') and row[c] in ac.QV]
            sec.append(F(sum(vals), len(vals)))
        section.append(sec)
    exact = [sum(s)/16 for s in section]
    _, _, _, df = ac.cargar()
    assert len(set(exact)) == 22
    count = 0

    def ranks_match(fractions, floats):
        nonlocal count
        common = math.lcm(*(x.denominator for x in fractions))
        integer = np.array([int(x*common) for x in fractions])
        np.testing.assert_array_equal(stats.rankdata(integer), stats.rankdata(ac.rangos_estables(floats)))
        np.testing.assert_array_equal(stats.rankdata(abs(integer)), stats.rankdata(abs(ac.rangos_estables(floats))))
        np.testing.assert_array_equal(integer == 0, ac.rangos_estables(floats) == 0)
        count += 1
        return integer

    integer = ranks_match(exact, df['global'])
    mask = np.array([r['USO']=='INDUSTRIAL' for r in rows])
    independent = stats.kruskal(integer[mask], integer[~mask])
    result = ac.kw(df['global'][mask], df['global'][~mask])
    np.testing.assert_allclose(result['H'], independent.statistic, rtol=0, atol=1e-12)
    dom = {g: [sum(s[i-1] for i in ids)/len(ids) for s in section] for g, ids in ac.DOM.items()}
    numeric = ac.dominios(df)
    for g in dom:
        ranks_match(dom[g], numeric[g])
    # Friedman assigns ranks within each SDS, unlike the between-SDS KW tests.
    for i in range(50):
        ranks_match([dom[g][i] for g in dom], [numeric[g][i] for g in dom])
    for a, b in combinations(dom, 2):
        delta = [x-y for x,y in zip(dom[a],dom[b])]
        integers = ranks_match(delta, numeric[a]-numeric[b])
        check = stats.wilcoxon(integers, method='asymptotic', zero_method='wilcox', correction=False)
        out = ac.wilcoxon(numeric[a],numeric[b])
        np.testing.assert_allclose([out['W'],out['p'],out['r']], [check.statistic,check.pvalue,abs(check.zstatistic)/np.sqrt(np.count_nonzero(integers))], rtol=0, atol=1e-12)
    critical = [sum(s[i-1] for i in ac.CRIT)/4 for s in section]
    other = [sum(s[i-1] for i in range(1,17) if i not in ac.CRIT)/12 for s in section]
    c = df[[f'Q{s}' for s in ac.CRIT]].mean(axis=1)
    nc = df[[f'Q{s}' for s in range(1,17) if s not in ac.CRIT]].mean(axis=1)
    integers = ranks_match([x-y for x,y in zip(critical,other)], c-nc)
    for ids in [list(range(50)), list(df.sort_values('FDS').drop_duplicates('cfg').index)]:
        z = stats.wilcoxon(integers[ids], method='asymptotic', zero_method='wilcox', correction=False)
        r = ac.wilcoxon(c.iloc[ids], nc.iloc[ids])
        np.testing.assert_allclose([r['W'],r['p'],r['r']], [z.statistic,z.pvalue,abs(z.zstatistic)/np.sqrt(np.count_nonzero(integers[ids]))], rtol=0, atol=1e-12)
    import resultados_esperados as e
    import json
    errors = e.comparar(json.loads(json.dumps(ac.calcular(), default=str)))
    assert not errors, errors
    print(f'OK: matriz intacta; {count} controles de rangos contra fracciones exactas; Wilcoxon coherente; {len(e.ESPERADO)} valores esperados.')


if __name__ == '__main__':
    main()
