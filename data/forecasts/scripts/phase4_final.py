"""Phase 4/5: validate shipping blend, NZ policy-break test, calibrated bands, scenarios, per-state JSON."""
import pandas as pd, numpy as np, json, os, datetime
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); R=f'{B}/raw'
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'phase3_models.py')).read().split('# ---------- models ----------')[0])
BT=pd.read_csv(f'{B}/backtest_predictions.csv'); out={}
def rmse(x): x=x.dropna(); return float(np.sqrt((x**2).mean()))
# 1) Pre-specified (a priori, NOT tuned) shipping blend: 50% no-change + 50% base-rate
BT['SHIP']=0.5*BT.B1+0.5*BT.M2
out['ship_blend_rmse']={w:{m:round(rmse(d[d.h==10].act-d[d.h==10][m]),3) for m in ['B1','M2','SHIP']} for w,d in BT.groupby('win')}
out['ship_blend_rmse_allh']={w:{m:round(rmse(d.act-d[m]),3) for m in ['B1','M2','SHIP']} for w,d in BT.groupby('win')}
# 2) Bands: offsets of SHIP's OOS errors around ZERO (no bias correction), smoothed as c_q*sqrt(h)
Q=[0.1,0.25,0.75,0.9]
def fit_c(df):
    # least-squares c_q for offsets q_h(err) ~ c_q*sqrt(h), pooled per-horizon quantiles
    cs=[]
    for q in Q:
        x=[];y=[]
        for h in range(1,11):
            e=(df[df.h==h].act-df[df.h==h].SHIP).dropna()
            if len(e)>=10: x.append(np.sqrt(h)); y.append(np.quantile(e,q))
        x=np.array(x); y=np.array(y); cs.append(float((x@y)/(x@x)))
    return cs
def interval(c,k80,k50,h):
    r=np.sqrt(h); return [k80*c[0]*r, k50*c[1]*r, k50*c[2]*r, k80*c[3]*r]
def loo_cov(k,which):
    hits=[]
    for w in BT.win.unique():
        c=fit_c(BT[BT.win!=w]); te=BT[BT.win==w]
        for h in range(1,11):
            z=(te[te.h==h].act-te[te.h==h].SHIP).dropna(); iv=interval(c,k,k,h)
            lo,hi=(iv[0],iv[3]) if which==80 else (iv[1],iv[2]); hits+=list((z>=lo)&(z<=hi))
    return float(np.mean(hits))
out['loo_cov_raw']={'cov80':round(loo_cov(1.0,80),2),'cov50':round(loo_cov(1.0,50),2)}
ks=np.arange(0.8,3.01,0.05)
k80=float(next((k for k in ks if loo_cov(k,80)>=0.80),ks[-1])); k50=float(next((k for k in ks if loo_cov(k,50)>=0.50),ks[-1]))
out['band_widening']={'method':'offsets=c_q*sqrt(h), widen factor by leave-one-window-out CV','k80':round(k80,2),'k50':round(k50,2),
                      'loo_cov80_after':round(loo_cov(k80,80),2),'loo_cov50_after':round(loo_cov(k50,50),2)}
C=fit_c(BT); out['band_c']=[round(c,4) for c in C]
band={}
for h in range(1,11):
    iv=interval(C,k80,k50,h); lo80,lo50,hi50,hi80=iv
    lo80=min(lo80,lo50); hi80=max(hi80,hi50)            # enforce ordering
    band[h]=np.array([lo80,lo50,0.0,hi50,hi80])
# 3) NZ policy-break test (info available at 2021Q1 only)
a=pd.read_csv(f'{R}/dallasfed_ihpd_annual_q4.csv'); a=a[a.period.str.endswith('Q4')]; a['y']=a.period.str[:4].astype(int)
pvn=np.log(a.rhpi_NZL/a.rpdi_NZL).values; yy=a.y.values; i20=list(yy).index(2020); pct_nz=(pvn[:i20+1]<=pvn[i20]).mean()
ar=[]
for c in ['AUS','NZL','CAN','GBR','IRL','NLD','SWE','NOR','DNK','USA','ESP','JPN']:
    lr=np.log(a['rhpi_'+c].values); pv=np.log(a['rhpi_'+c].values/a['rpdi_'+c].values)
    for i in range(10,len(yy)-5):
        if yy[i]+5<=2020: ar.append(dict(pct=(pv[:i+1]<=pv[i]).mean(),fwd=lr[i+5]-lr[i]))
ar=pd.DataFrame(ar); near=ar[(ar.pct-pct_nz).abs()<=0.15]
q5=pd.read_csv(f'{R}/dallasfed_ihpd_quarterly_AUS_NZL_CAN_GBR_2014_2026.csv').set_index('period')
nz_act=np.log(q5.loc['2026:Q1','rhpi_NZL']/q5.loc['2021:Q1','rhpi_NZL'])
base_pred=0.5*0+0.5*near.fwd.median()
OVR_NZ=-0.10   # what our overlay rule would have applied to an NZ-scale measure (removes deductibility on ALL stock)
out['nz_policy_break_test']=dict(nz_valuation_pct_2020=round(pct_nz,2),pred_5y_no_policy=round(float(np.exp(base_pred)-1),3),
    pred_5y_with_overlay=round(float(np.exp(base_pred+OVR_NZ)-1),3),actual_5y_2021Q1_2026Q1=round(float(np.exp(nz_act)-1),3),
    verdict='method too optimistic: missed the downside; rate shock + policy together exceeded both components')
# 4) Final forecasts from origin FY2026
cpi=fy_avg(mac,'cpi_idx'); T0=2026
def m2_now(h):
    sub=A[(A.h==h)]; pc=aus_pct[max(aus_pct)]; near=sub[(sub.pct-pc).abs()<=0.15]; return near.fwd.median()
CENTRAL={h:0.5*0+0.5*m2_now(h) for h in range(1,11)}
# policy overlay (JUDGEMENT; log points, real, level shift by FY): established houses vs units (investor-heavier)
OVR={'H':{2027:-0.01,2028:-0.02},'U':{2027:-0.015,2028:-0.035}}; FULL={'H':-0.03,'U':-0.05}
def ovr(ty,yr): return OVR[ty].get(yr,FULL[ty])
SCEN={'low':{'H':-0.08,'U':-0.12,'rate_extra':-0.05},'base':{'H':None,'U':None,'rate_extra':0.0},'high':{'H':0.0,'U':-0.01,'rate_extra':0.0}}
CPI_PATH={2027:0.035,2028:0.030}; cpi_g=lambda y: CPI_PATH.get(y,0.025)
yrs=list(range(2027,2037)); cum_infl=np.cumprod([1+cpi_g(y) for y in yrs])
NAMES={'SYD':'Sydney','MEL':'Melbourne','BRI':'Brisbane','ADL':'Adelaide','PER':'Perth','HOB':'Hobart','DAR':'Darwin','CBR':'Canberra'}
POLICY=[
 'Tax Reform No.1 Act 2026 (assent 26 Jun 2026): negative gearing quarantined for established dwellings acquired after 7:30pm AEST 12 May 2026, from FY2027-28; pre-cut-off holdings grandfathered until sale; new builds exempt.',
 'CGT 50% discount replaced by cost-base indexation + 30% minimum tax for gains accruing from 1 Jul 2027; pre-1 Jul 2027 gains keep 50% via deemed disposal/re-acquisition; new-build investors may choose either.',
 'SMSF: no new residential LRBAs from 10 Aug 2026 (treated as minor).',
 'Tax Reform No.3 Bill 2026 ("Tranche 2", new-dwelling definition s960-590) assumed to PASS substantially as introduced 14 Oct 2026. NOT yet law at retrieval.',
 'Foreign purchase ban on established dwellings to 30 Jun 2029 (assumed to lapse then, no forecast effect modelled).',
 'APRA serviceability buffer 3pp and 20%/6x DTI speed limit unchanged.',
 '5% Deposit Scheme (uncapped since 1 Oct 2025) and Help to Buy continue.']
MACRO=[
 'Cash rate 4.85% (3 Nov 2026) assumed to peak; scenarios span further +25-50bp (low) to cuts from H2 2027 (high).',
 'CPI assumption for nominal conversion: 3.5% FY2027, 3.0% FY2028, 2.5% thereafter (RBA 2-3% target midpoint) — ASSUMPTION, CPI uncertainty not included in bands.',
 'NOM per 2026-27 Budget: 245k in 2026-27 (stress test halves it).',
 'Housing Accord: target reached ~Dec 2030 per NHSAC Aug 2026 (i.e. missed by Jun 2029).']
OVERLAY_DOC={'established_houses_real_level_shift':{'FY2027':-0.01,'FY2028':-0.02,'FY2029_onward':-0.03},
             'units_real_level_shift':{'FY2027':-0.015,'FY2028':-0.035,'FY2029_onward':-0.05},
             'new_builds_relative_to_established':'+1% to +3% (judgement; no free new-build price series to model)',
             'basis':'JUDGEMENT anchored to NZ 2021-23 evidence (-12.8pp vs AUS/CAN = upper bound, confounded). AU measures are milder (existing stock grandfathered; CGT change also hits shares, so relative effect smaller). Units heavier because investor-owned share is higher.',
             'effects':{'a_grandfathered_lock_in':'reduces established listings -> partially offsets downside (included net)',
                        'b_shift_to_new_builds':'new-build relative +1-3%',
                        'c_sell_before_1Jul2027':'weak incentive (accrued gains preserved by deemed disposal) -> small 2027 listing bulge, inside FY2027 shift',
                        'd_fewer_investor_rentals':'upward pressure on rents (not a price forecast; flagged for Signals)',
                        'e_after_tax_vs_shares_super':'CGT change applies to shares too; relative shift driven mainly by negative gearing'}}
STRESS={'rates_plus2pp_sustained':{'real_price_impact':'-5% (AUS-calibrated) to -14% (CAN/NZ-calibrated)','basis':'2022-23 episode: cash +4.25pp -> AUS real -10.3% peak-to-trough, CAN -29.2%, NZ -26.6% (Dallas Fed RHPI); scaled per pp'},
        'migration_halved':{'real_price_impact':'-3% to -8% over 3-5y (ASSUMPTION; fundamentals model failed backtest so no validated elasticity)','basis':'2021 border closure: NOM negative yet AUS real prices +20% (stimulus/low rates dominated) — migration alone is not a reliable driver'},
        'housing_accord_met':{'real_price_impact':'-2% to -5% relative to base by 2031 (ASSUMPTION)','basis':'~220k extra completions vs current trajectory (NHSAC)'},
        'housing_accord_missed_further':{'real_price_impact':'+2% to +5% relative to base (ASSUMPTION)'},
        'recession_7pct_unemployment':{'real_price_impact':'-5% to -15% (ASSUMPTION)','basis':'1990-92 recession: AUS real house prices ~-4% (Dallas Fed); NZ/CAN 2022-25 show larger falls when combined with high rates'},
        'grandfathering_removed_future':{'real_price_impact':'up to -13pp vs base (upper bound)','basis':'NZ removed deductibility on existing stock: -12.8pp vs AUS/CAN 2021Q1-2023Q4'},
        'policy_reversed_by_future_govt':{'real_price_impact':'overlay removed: +3% houses / +5% units vs base','basis':'NZ reversal 2024-25 produced NO rebound (-5.3pp vs peers) -> treat as upside skew only'}}
gen=datetime.date.today().isoformat(); summary={}
for s in ST:
    c=CAP[s]; js={'schema_version':'1.0','state':s,'generated':gen,'last_data':'ABS 6432 Jun qtr 2026; RBA Oct 2026; policy verified 15 Nov 2026',
       'label':'Scenario-based estimate, not a prediction. General information only - not financial advice; does not consider your personal circumstances.',
       'units':'$ thousand, median transfer price (ABS Total Value of Dwellings Table 2, unstratified)','base_period':'FY2026 (Jul 2025-Jun 2026) average of quarterly medians',
       'years':yrs,'method':{'central':'50% no-real-change + 50% international base-rate (valuation-conditioned, Dallas Fed IHPD) + policy overlay',
       'why':'Only blend that did not lose to baselines; fundamentals ECM and drift models failed backtests and are NOT used','bands':'empirical out-of-sample error quantiles pooled over 3 rolling-origin backtests'},
       'policy_assumptions':POLICY,'macro_assumptions':MACRO,'policy_overlay':OVERLAY_DOC,'stress_tests':STRESS,'series':{}}
    for reg in ['cap','rest']:
        for ty in ['H','U']:
            key=(s,reg,ty)
            if key not in series: continue
            ps=series[key]; 
            if T0 not in ps.index: continue
            base=float(ps[T0]); nm=(NAMES[c] if reg=='cap' else 'Rest of '+s)+(' houses' if ty=='H' else ' units')
            real={k:[] for k in ['p10','p25','p50','p75','p90']}; sc={'low':[],'base':[],'high':[]}
            for i,y in enumerate(yrs):
                h=i+1; ctr=CENTRAL[h]+ovr(ty,y)
                for k,qv in zip(['p10','p25','p50','p75','p90'],band[h]-band[h][2]): real[k].append(round(base*np.exp(ctr+qv),1))
                sc['base'].append(round(base*np.exp(ctr),1))
                lo=CENTRAL[h]+(band[h][1]-band[h][2])+SCEN['low'][ty]*min(1,h/3)+SCEN['low']['rate_extra']*min(1,h/2)
                hi=CENTRAL[h]+(band[h][3]-band[h][2])+SCEN['high'][ty]
                sc['low'].append(round(base*np.exp(lo),1)); sc['high'].append(round(base*np.exp(hi),1))
            nom={k:[round(v*cum_infl[i],1) for i,v in enumerate(real[k])] for k in real}
            nsc={k:[round(v*cum_infl[i],1) for i,v in enumerate(sc[k])] for k in sc}
            js['series'][f'{reg}_{ty}']={'name':nm,'region':reg,'type':'houses' if ty=='H' else 'units','stock':'established' if ty=='H' else 'attached (established+new mix)',
                'base_value':round(base,1),'real':real,'nominal':nom,'scenarios_real':sc,'scenarios_nominal':nsc}
            summary[nm]=dict(base=round(base),p50_2036_real=real['p50'][-1],chg_real=round(real['p50'][-1]/base-1,3),
                             p10_real=real['p10'][-1],p90_real=real['p90'][-1],p50_2036_nominal=nom['p50'][-1],chg_nom=round(nom['p50'][-1]/base-1,3))
    json.dump(js,open(f'{B}/property_forecast_{s}.json','w'),indent=1)
out['central_real_logchg_by_h']={h:round(float(v),3) for h,v in CENTRAL.items()}
out['band_quantiles_logpts_by_h']={h:[round(float(x),3) for x in band[h]] for h in band}
out['summary_2036']=summary
json.dump(out,open(f'{B}/final_results.json','w'),indent=1,default=str)
print(json.dumps({k:v for k,v in out.items() if k!='summary_2036'},indent=1,default=str))
print('\n2036 (FY) median vs FY2026 base:')
for k,v in summary.items(): print(f"  {k:26s} base ${v['base']}k  real {v['chg_real']:+.0%} (p10 {v['p10_real']/v['base']-1:+.0%} .. p90 {v['p90_real']/v['base']-1:+.0%})  nominal {v['chg_nom']:+.0%}")
