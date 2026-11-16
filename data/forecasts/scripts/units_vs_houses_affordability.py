"""Do units catch up with houses when house affordability is stretched? (16 Nov 2026)
Data: ABS Total Value of Dwellings T2 medians by capital (houses/units, 2002Q1-2026Q2), RBA owner-occupier standard
variable rate, ABS 5220 household disposable income per capita by state (x2.5 ~ per household).
Stretch = annual repayment on an 80% LVR 30y loan for the median house / income, as a percentile of the capital's own
history to date (no look-ahead). Outcome: next-5y log change of units minus houses (pp). 8 capitals, overlapping windows.
Run from data/forecasts/raw:  python3 ../scripts/units_vs_houses_affordability.py"""
import pandas as pd, numpy as np
d = pd.read_csv('abs_tvd_t2_median_prices_q.csv').set_index('period')
inc = pd.read_csv('abs_5220_household_gdi_fy.csv').set_index('fy_end_june')
rba = pd.read_csv('rba_macro_q.csv').set_index('period')
ST = {'SYD': 'NSW', 'MEL': 'VIC', 'BRI': 'QLD', 'ADL': 'SA', 'PER': 'WA', 'HOB': 'TAS', 'DAR': 'NT', 'CBR': 'ACT'}
fy = lambda p: int(p[:4]) + (1 if int(p[-1]) >= 3 else 0)
def pay(P, r, n=30): i = r / 1200; return 0.8 * P * i / (1 - (1 + i) ** (-12 * n)) * 12
rows = []
for c, s in ST.items():
    h, u = d['H_' + c], d['U_' + c]; S = []
    for p in d.index:
        r = rba.loc[p, 'oo_std_var'] if p in rba.index else np.nan
        pc = inc.loc[fy(p), 'hgdipc_' + s] if fy(p) in inc.index else inc['hgdipc_' + s].dropna().iloc[-1]
        S.append(pay(h[p] * 1000, r) / (pc * 2.5) if not pd.isna(h[p]) and not pd.isna(r) else np.nan)
    S = pd.Series(S, index=d.index); lr = np.log(h / u)
    print(c, 'repayment/income now %.0f%%, percentile of own history %.0f' % (S.dropna().iloc[-1] * 100, (S.dropna() <= S.dropna().iloc[-1]).mean() * 100))
    for i in range(len(d)):
        if pd.isna(S.iloc[i]) or pd.isna(lr.iloc[i]): continue
        hist = S.iloc[:i + 1].dropna()
        if len(hist) < 12 or i + 20 >= len(d) or pd.isna(lr.iloc[i + 20]): continue
        rows.append(dict(c=c, p=d.index[i], pct=(hist <= S.iloc[i]).mean(), rel5=-(lr.iloc[i + 20] - lr.iloc[i]) * 100))
R = pd.DataFrame(rows)
R['grp'] = pd.cut(R.pct, [0, .5, .8, .9, 1.0], labels=['below median', '50-80th', '80-90th', 'top 10%'], include_lowest=True)
print(R.groupby('grp', observed=True).rel5.agg(n='size', units_minus_houses='mean', units_win_pct=lambda x: (x > 0).mean() * 100).round(1))
print('corr', round(R.pct.corr(R.rel5), 2), '| top-10% origins by year', R[R.pct > .9].p.str[:4].value_counts().sort_index().to_dict())
tr, te = R[R.p < '2012'], R[R.p >= '2012']; b = np.polyfit(tr.pct, tr.rel5, 1)
print('out-of-sample (fit <2012, test 2012-21): MAE %.2f vs mean %.2f vs zero %.2f' % (np.mean(np.abs(te.rel5 - np.polyval(b, te.pct))), np.mean(np.abs(te.rel5 - tr.rel5.mean())), np.mean(np.abs(te.rel5))))
