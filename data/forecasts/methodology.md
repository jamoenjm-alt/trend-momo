# Property forecast 2027–2036 — methodology, validation and limits

Version 1.0 · built 16 Nov 2026 · policy verified 15 Nov 2026 · price data to June quarter 2026.
Reproduce: `cd data/forecasts/scripts && python3 phase2_analogues.py && python3 phase3_models.py && python3 phase4_final.py`
(pure Python + pandas/numpy; all inputs in `raw/`).

## Plain-English summary (read this first)
- We tried to forecast house and unit prices for every state and territory for the next 10 years.
- **Most forecasting methods we tested did worse than simply assuming prices keep pace with inflation.** A
  "fundamentals" model (prices vs incomes, interest rates, population, building) was clearly worse and is **not
  used**. Extending past growth was also worse and is **not used**.
- The forecast that ships is deliberately simple: half "no change after inflation", half "what happened in other
  countries when housing was this expensive", minus an allowance for the 2026 tax changes.
- Its middle line is roughly **+7% after inflation over 10 years for houses (+5% units)** — about +0.7% a year — or
  about **+39% / +36% before inflation** under our inflation assumption. **The middle line is not the message. The
  range is.** By 2036 there is roughly a 1-in-10 chance prices end **more than ~27% lower** in real terms and a 1-in-10 chance they
  end **more than ~70% higher**. That range is honest: it is what our past forecasting errors actually looked like.
  It leans to the upside only because 2006–2025 kept surprising upward; in today's high-rate setting the downside is
  probably *under*-stated (see §5, NZ test).
- We **cannot** tell you which state will do best. No method we tried could separate states better than chance over
  10 years, so every state carries the same percentage path applied to its own starting price.

## 1. Data (all retrieved 15–16 Nov 2026)
| File in `raw/` | Source | URL | Coverage |
|---|---|---|---|
| `abs_tvd_t2_median_prices_q.csv` | ABS 6432.0 Total Value of Dwellings, Table 2 (Jun qtr 2026): median established-house and attached-dwelling transfer prices, 8 capitals + 7 rest-of-state | https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings/latest-release | capitals 2002Q1–2026Q2; rest-of-state & units 2003Q3–2026Q2 |
| `abs_6416_t8_established_homes_1986_2005.csv` | ABS 6416.0 RPPI (archived Dec 2021), Table 8 Price Index of Established Homes | https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/residential-property-price-indexes-eight-capital-cities/latest-release | 1986Q2–2005Q2 |
| `abs_6416_t2_established_house_index_2002_2021.csv`, `abs_6416_t3_attached_dwellings_index_2003_2021.csv` | ABS 6416.0 Tables 2–3 (stratified indexes) — kept for cross-checks | as above | 2002/03–2021 |
| `rba_macro_q.csv` | RBA F1.1 (cash rate, 90-day bills), F5 (housing lending rates), D1/D2 (housing credit by investor/owner-occupier), G1 (CPI, trimmed mean) | https://www.rba.gov.au/statistics/tables/ | 1959Q1–2026Q3 |
| `abs_3101_population_fy.csv` | ABS 3101.0 National, state & territory population (Mar 2026): ERP, NOM, net interstate migration by state, aggregated to financial years | https://www.abs.gov.au/statistics/people/population/national-state-and-territory-population/latest-release | FY1981–FY2026 (FY2026 flows = 3 qtrs) |
| `abs_5220_household_gdi_fy.csv` | ABS 5220.0 State Accounts 2024-25: household gross disposable income (total and per capita) | https://www.abs.gov.au/statistics/economy/national-accounts/australian-national-accounts-state-accounts/latest-release | FY1990–FY2025 |
| `abs_8752_completions_fy.csv` | ABS 8752.0 Building Activity (Jun 2026), Table 39: dwelling units completed, Total Sectors, houses and other residential, by state | https://www.abs.gov.au/statistics/industry/building-and-construction/building-activity-australia/latest-release | FY1981–FY2026 |
| `dallasfed_ihpd_*.csv` | Dallas Fed International House Price Database hp2602 | https://www.dallasfed.org/research/international/houseprice | 1975Q1–2026Q2 |

Licensing: ABS and RBA data are CC BY 4.0 (attribute "Source: ABS"/"Source: RBA"). Dallas Fed data free with
citation (Mack & Martínez-García 2011). **No paid data (Cotality/CoreLogic, SQM) is used in these forecasts.**

### Data gaps (report, do not paper over)
1. **No free, long, state-level new-build price series** → established vs new is handled only as a judgement
   relative adjustment (+1% to +3% for new), not modelled.
2. **Units and rest-of-state prices start 2003** → cannot be tested in the 2006–15 window (capital houses only).
3. **ABS medians are unstratified** — composition noise of ±5% a year is inside our backtest errors (and so inside
   our bands). ABS 6416 stratified indexes ceased in 2021.
4. **ABS Data API was unreachable** from this environment (spreadsheets used instead). Permanent Migration Program
   planning level 2026-27 not located. Housing finance by state (ABS 5601) and rents/vacancy by state not used.
5. Hong Kong not in Dallas Fed; not included in the analogue panel.

## 2. Models tested (all evaluated in **real** terms, log price)
| ID | Model | Status |
|---|---|---|
| B1 | Random walk, no drift ("no change after inflation") | baseline |
| B2 | Random walk with drift = series' historical average real growth (falls back to state capital houses if <8 yrs) | baseline — **fails** |
| M1 | Fundamentals, direct multi-horizon regression pooled across 30 series: national price-to-income gap (expanding mean), real mortgage rate, 5-yr state population growth, persons added per dwelling completed, 3-yr momentum, unit/regional dummies; ridge shrinkage λ fixed a priori | **fails — not used** |
| M2 | International base rate: median h-year real outcome in the 12-country panel among country-years within ±15 percentile points of Australia's current valuation percentile, using only outcomes observable at the forecast origin | used (½ weight) |
| SHIP | **0.5 × B1 + 0.5 × M2** — weights fixed *before* evaluation (not optimised) | **shipped** |

## 3. Backtests — rolling origin, no look-ahead
Origins: FY2005 (forecast 2006–15), FY2010 (2011–20), FY2015 (2016–25). Training uses only outcomes observable at the
origin. 30 series (8 capital houses, 8 capital units, 7 rest-of-state houses, 7 rest-of-state units), except the
2005 window for M1 (capital houses only).

**10-year-ahead RMSE (log real price; 0.27 ≈ ±31% typical error)**
| Window | B1 | B2 | M1 | M2 | **SHIP** |
|---|---|---|---|---|---|
| 2006–15 | 0.271 | 0.273 | 0.737 | 0.268 | **0.269** |
| 2011–20 | **0.232** | 0.510 | 0.437 | 0.332 | 0.267 |
| 2016–25 | 0.325 | 0.438 | 0.534 | **0.279** | 0.284 |

**All horizons 1–10 averaged:** SHIP 0.242 / 0.175 / 0.215 vs B1 0.249 / 0.143 / 0.232.

**Verdict, plainly:** the shipped blend beats the naive baseline in **2 of 3 windows and loses in one (2011–20)**.
It is not a strong forecasting edge. Its value is mainly that it is no worse than naive and comes with honest,
calibrated error bands. Nested weighting test (weights fit on 2006–15 + 2011–20, scored on 2016–25: B1 0.40, M2 0.31,
B2 0.22, M1 0.07) gave RMSE 0.305 at 10 years vs B1 0.325 — confirming the fundamentals model earns almost no weight.

Mean 10-yr bias: B2 over-forecast in every window (extrapolated the 2000s boom); M1 swung from −73% too low to +46%
too high — unstable.

## 4. Uncertainty bands and calibration
- Bands = out-of-sample errors of SHIP pooled across all three windows; for each quantile (10/25/75/90) the per-horizon
  error quantiles are smoothed as **c·√h** (least squares) so the band widens steadily with horizon and never crosses.
  Centre = SHIP + policy overlay (no bias correction). Fitted c = −0.096, −0.049, +0.073, +0.118.
- Raw bands were **too narrow**: leave-one-window-out coverage of the "80%" band was 71% and of the "50%" band 33%.
- Fix: widening factors chosen by **cross-validation** (each window scored with bands from the other two):
  **k80 = 1.25, k50 = 1.70** → leave-one-window-out coverage **81% (target 80%) and 50% (target 50%)**.
- The band is right-skewed (upside wider) because the 2006–2025 errors were; a high-rate decade may not repeat that.
- Nominal = real × assumed CPI path (3.5% FY27, 3.0% FY28, 2.5% after). **CPI uncertainty is not in the bands.**

## 5. Policy-break adjustment (judgement, explicitly separated)
History contains no precedent for the 2026 tax reform, so it is applied as a **visible overlay**, not learned:
| | FY2027 | FY2028 | FY2029 onward |
|---|---|---|---|
| Established houses (real level shift) | −1% | −2% | −3% |
| Units (investor-heavier) | −1.5% | −3.5% | −5% |
| New builds vs established | +1% to +3% relative (not modelled) | | |
Effects (a)–(e) from the brief and how each is treated are in every JSON under `policy_overlay.effects`.
Scenario overlays: **low** −8% houses / −12% units plus a further −5% for rates staying higher; **high** 0% / −1%.
Anchor: NZ 2021–23 relative decline of −12.8pp (an upper bound — see `analogues.md`).

### NZ policy-break test (would the method have seen NZ coming?)
Using only information available at 2021Q1: NZ valuation was at the 100th percentile of its history; the base-rate
blend predicted **+5.3%** real over 5 years; with an NZ-scale overlay (−10%), **−4.8%**. Actual 2021Q1→2026Q1:
**−17.7%**. **The method was too optimistic** — the rate shock and tax change together exceeded both components.
Australia today has the same combination (18-year-high cash rate + tax reform), so **treat the downside as
under-weighted in the central line**; the low scenario is built to include an NZ-like outcome.

## 6. Stress tests (real price impact vs base; full text in each JSON)
| Test | Impact | Basis |
|---|---|---|
| Rates +2pp sustained | −5% to −14% | 2022–23: cash +4.25pp → AUS −10.3%, CAN −29.2%, NZ −26.6% peak-to-trough [Dallas Fed] |
| Migration halved | −3% to −8% (assumption) | M1 failed, so no validated elasticity; 2021 NOM<0 yet prices +20% |
| Housing Accord met | −2% to −5% by 2031 (assumption) | ~220k extra completions vs trajectory [NHSAC] |
| Accord missed further | +2% to +5% (assumption) | |
| Recession, 7% unemployment | −5% to −15% (assumption) | 1990–92 AUS ~−4% real [Dallas Fed]; larger when combined with high rates |
| Grandfathering removed | up to −13pp | NZ upper bound |
| Policy reversed | +3% houses / +5% units (upside only) | NZ reversal produced no rebound |

## 7. The five biggest ways this forecast could be wrong
1. **Rates stay high for years.** All backtest windows and almost all analogue episodes come from a falling-rate era;
   the central line likely overstates real growth if 4.85% is not the peak.
2. **Rate shock + tax change compound** (the NZ failure mode). The test above shows we under-predicted exactly this.
3. **States diverge sharply.** We apply one percentage path to every state because nothing validated better — but in
   reality WA/QLD vs NSW/VIC have differed by 30–50pp over a decade. The band covers it; the median does not.
4. **Policy changes again** (Tranche 2 amended, grandfathering removed, a future government reverses it).
5. **Data noise and definitions.** Unstratified medians shift with the mix of what sells; a regime of more apartment
   or new-estate sales moves the median without any price change.

## 8. Output schema — `property_forecast_{STATE}.json`
```
schema_version, state, generated (ISO date), last_data, label (scenario-estimate + general-advice wording),
units ("$ thousand, median transfer price"), base_period ("FY2026 average"), years [2027..2036] (FY ending June),
method {central, why, bands}, policy_assumptions [...], macro_assumptions [...], policy_overlay {...}, stress_tests {...},
series {
  "<cap|rest>_<H|U>": {
     name, region, type, stock, base_value,
     real:     {p10[10], p25[10], p50[10], p75[10], p90[10]},   # FY2026 dollars
     nominal:  {p10..p90},                                       # assumed CPI path applied
     scenarios_real: {low[10], base[10], high[10]},
     scenarios_nominal: {low, base, high}
  }
}
```
ACT has no rest-of-state series.

## 9. Website display requirements (mandatory)
1. Chart per state shows the **band** (shade p10–p90, darker p25–p75); the median line is thin and labelled
   "middle of range", never "forecast".
2. Label: **"Scenario-based estimate — not a prediction"**, with "Last updated: <generated>" and "Data to June 2026".
3. Show the key assumptions inline (tax reform as legislated + Tranche 2 assumed to pass; cash rate 4.85% peak;
   CPI path) and link to this methodology.
4. Toggle real / nominal; default **real** (avoids the illusion that inflation is growth).
5. State plainly: "No method we tested could rank states; every state uses the same percentage range."
6. Disclaimer (verbatim): *"General information only — not financial advice. It does not take into account your
   objectives, financial situation or needs. Consider whether it is appropriate for you and seek independent
   advice before making any decision."*
7. Do not show more than one decimal of percentage, and round dollar values to $1k — false precision undermines the
   honesty of the band.
