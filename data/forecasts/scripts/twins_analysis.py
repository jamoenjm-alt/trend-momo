"""Twin-episode test (16 Nov 2026). Dallas Fed IHPD hp2602, 12 countries.
Condition: price-to-income in top decile of own history (expanding window, no look-ahead)
AND real disposable income fell in the prior year. Outcome: next-5y real price change.
Run: python3 twins_analysis.py   (from data/forecasts/scripts)"""
import pandas as pd, numpy as np, json
d = pd.read_csv('../raw/dallasfed_ihpd_annual_q4.csv'); d['yr'] = d.period.str[:4].astype(int); d = d.set_index('yr')
C = ['AUS','NZL','CAN','GBR','IRL','NLD','SWE','NOR','DNK','USA','ESP','JPN']
rows = []
for c in C:
    p, y = d['rhpi_'+c], d['rpdi_'+c]; pi = p / y
    for t in d.index:
        if t < 1985 or pd.isna(pi[t]): continue
        hist = pi.loc[:t].dropna()
        if len(hist) < 10: continue
        rows.append(dict(c=c, t=t, pct=(hist <= pi[t]).mean(), inc1=y[t]/y.get(t-1, np.nan)-1,
                         pr1=p[t]/p.get(t-1, np.nan)-1, f5=p.get(t+5, np.nan)/p[t]-1))
R = pd.DataFrame(rows).dropna(subset=['f5'])
out = {}
for lab, m in [('all', R.pct >= 0), ('top_decile', R.pct >= .9),
               ('top_decile_income_fell', (R.pct >= .9) & (R.inc1 < 0)),
               ('top_decile_prices_falling', (R.pct >= .9) & (R.pr1 < 0))]:
    x = R[m].f5 * 100
    out[lab] = dict(n=int(len(x)), countries=int(R[m].c.nunique()), median=round(x.median(), 1),
                    p10=round(x.quantile(.1), 1), p90=round(x.quantile(.9), 1), p_fall=round((x < 0).mean()*100))
    print(lab, out[lab])
out['cases_top_decile_income_fell'] = R[(R.pct >= .9) & (R.inc1 < 0)][['c','t','f5']].round(3).values.tolist()
json.dump(out, open('../twins_results.json', 'w'), indent=1)
