"""Phase 2 — international analogues. Inputs: Dallas Fed IHPD (raw/). Outputs printed + analogues_results.json"""
import pandas as pd, numpy as np, json, os
B=os.path.join(os.path.dirname(__file__),'..')
q=pd.read_csv(f'{B}/raw/dallasfed_ihpd_quarterly_AUS_NZL_CAN_GBR_2014_2026.csv').set_index('period')
a=pd.read_csv(f'{B}/raw/dallasfed_ihpd_annual_q4.csv').set_index('period')
out={}
# ---- 1. NZ policy episode vs comparators (real prices) ----
def idx(col,base): return (q[col]/q.loc[base,col]*100).round(1)
ep={}
for c in ['NZL','AUS','CAN','GBR']:
    s=q['rhpi_'+c]
    pk=s.loc['2020:Q4':'2022:Q4'].idxmax()
    tr=s.loc[pk:].idxmin()
    ep[c]=dict(ann_2021Q1_to_2023Q4=round((s['2023:Q4']/s['2021:Q1']-1)*100,1),
               ann_2021Q1_to_2026Q2=round((s['2026:Q2']/s['2021:Q1']-1)*100,1),
               peak=pk, trough=tr, peak_to_trough=round((s[tr]/s[pk]-1)*100,1),
               reversal_2024Q1_to_2026Q2=round((s['2026:Q2']/s['2024:Q1']-1)*100,1))
out['nz_episode_real']=ep
ctl=['AUS','CAN']
did1=ep['NZL']['ann_2021Q1_to_2023Q4']-np.mean([ep[c]['ann_2021Q1_to_2023Q4'] for c in ctl])
did2=ep['NZL']['reversal_2024Q1_to_2026Q2']-np.mean([ep[c]['reversal_2024Q1_to_2026Q2'] for c in ctl])
out['nz_did_vs_AUS_CAN']={'removal_window_2021Q1_2023Q4_pp':round(did1,1),'reversal_window_2024Q1_2026Q2_pp':round(did2,1)}
# ---- 2. Base-rate panel: valuation-conditioned 10y real outcomes ----
cs=['AUS','NZL','CAN','GBR','IRL','NLD','SWE','NOR','DNK','USA','ESP','JPN']
yrs=[p for p in a.index if p.endswith('Q4')]
rows=[]
for c in cs:
    pti=(a['rhpi_'+c]/a['rpdi_'+c]).loc[yrs]
    rh=a['rhpi_'+c].loc[yrs]
    for i in range(len(yrs)-10):
        hist=pti.iloc[:i+1]
        if len(hist)<10: continue                    # need 10y of history -> no lookahead
        pct=(hist<=hist.iloc[-1]).mean()            # expanding-window percentile
        mom5=rh.iloc[i]/rh.iloc[i-5]-1
        fwd=rh.iloc[i+10]/rh.iloc[i]-1
        rows.append(dict(c=c,yr=int(yrs[i][:4]),pti_pct=pct,mom5=mom5,fwd10=fwd))
P=pd.DataFrame(rows)
def cls(x):
    if x<=-0.25: return 'crash (<=-25% real)'
    if x<0.05:   return 'stagnation (-25% to +5% real)'
    if x<0.30:   return 'soft landing / moderate growth (+5% to +30% real)'
    return 'continued boom (>=+30% real)'
P['outcome']=P.fwd10.apply(cls)
cond=P[(P.pti_pct>=0.9)]            # at/near own-history valuation high (top decile, expanding)
out['panel_all_n']=len(P); out['panel_cond_n']=len(cond)
out['panel_cond_countries']=sorted(cond.c.unique().tolist())
out['outcomes_all']=P.outcome.value_counts(normalize=True).round(3).to_dict()
out['outcomes_cond_top_decile_valuation']=cond.outcome.value_counts(normalize=True).round(3).to_dict()
out['fwd10_real_cond_quantiles']=cond.fwd10.quantile([.1,.25,.5,.75,.9]).round(3).to_dict()
out['fwd10_real_all_quantiles']=P.fwd10.quantile([.1,.25,.5,.75,.9]).round(3).to_dict()
# independent-episode count (one obs per country per 10y block) to show effective sample size
out['cond_effective_episodes']=int(cond.assign(blk=cond.yr//10).drop_duplicates(['c','blk']).shape[0])
# Australia now
pti_aus=(a['rhpi_AUS']/a['rpdi_AUS'])
out['AUS_pti_now_vs_history']={'now_2026Q2':round(pti_aus['2026:Q2'],3),'max':round(pti_aus.max(),3),'max_at':pti_aus.idxmax(),
                               'pct_of_history':round((pti_aus<=pti_aus['2026:Q2']).mean(),3)}
json.dump(out,open(f'{B}/analogues_results.json','w'),indent=1,default=str)
print(json.dumps(out,indent=1,default=str))
