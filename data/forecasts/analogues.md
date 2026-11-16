# International analogues — findings (Phase 2)

Retrieved 15–16 Nov 2026. Script: `scripts/phase2_analogues.py`. Output: `analogues_results.json`.
**Data:** Dallas Fed International House Price Database, release hp2602 (Q2 2026):
https://www.dallasfed.org/research/international/houseprice — real house price index (RHPI) and real
personal disposable income (RPDI), quarterly 1975Q1–2026Q2. Files: `raw/dallasfed_ihpd_annual_q4.csv`,
`raw/dallasfed_ihpd_quarterly_AUS_NZL_CAN_GBR_2014_2026.csv`.
Hong Kong is **not** in the Dallas Fed database — it was not included (gap; BIS has it, not fetched this run).

Convention: **[S]** = sourced number; **[J]** = judgement; **[V]** = from general knowledge, must be verified
against a primary source before publication.

---

## 1. New Zealand (priority analogue)

### 1a. What changed (verified sources)
Sources: ANZ NZ https://www.anz.co.nz/personal/home-loans-mortgages/investment-property/tax-changes/ ;
Baker Tilly https://bakertillysr.nz/news/bright-line-tax-and-rental-interest-deductibility-what-you-need-to-know/ ;
Davenports Law https://www.davenportslaw.co.nz/property/bright-line-test-changes/ (all secondary — IRD primary
page not reached; **confirm before relying on exact dates**).
- **Bright-line test:** 10 years for residential property bought on/after **27 Mar 2021** (5 years for
  2018–2021 purchases; new builds 5 years). Reduced to **2 years for all sales from 1 Jul 2024**. [S]
- **Interest deductibility:** phased out for residential investors from the 2021 income year; new builds
  (CCC after 27 Mar 2020) kept deductibility. Restored to **80% for 1 Apr 2024–31 Mar 2025** and **100% from
  1 Apr 2025**. [S] The exact 2021–2023 phase-down schedule for *existing* properties differs between
  secondary sources (one says fully removed by 31 Mar 2023) — **unresolved, needs IRD confirmation** [open question].
- **Concurrent shocks (confounders):** RBNZ OCR rose from 0.25% (Oct 2021) to 5.5% (2023) [V]; Credit Contracts
  and Consumer Finance Act lending-rule changes Dec 2021 [V]; a large construction surge [V].

### 1b. What happened — real prices (Dallas Fed RHPI) [S]
| | NZ | Australia | Canada | UK |
|---|---|---|---|---|
| Announcement 2021Q1 → 2023Q4 | **−10.9%** | +6.4% | −2.6% | −6.3% |
| 2021Q1 → 2026Q2 | **−17.5%** | +14.1% | −12.0% | −8.4% |
| Peak → trough | −26.6% (2021Q4→2026Q1) | −10.3% (2022Q1→2023Q1) | −29.2% (2022Q1→2026Q1) | −10.4% |
| After reversal 2024Q1 → 2026Q2 | **−6.8%** | +6.6% | −9.6% | −0.4% |

**Difference-in-differences vs average of AUS and CAN:**
- Removal window (2021Q1→2023Q4): **NZ −12.8 percentage points** relative to peers. [S, computed]
- Reversal window (2024Q1→2026Q2): **NZ −5.3pp** — i.e. restoring deductibility produced **no rebound**. [S]

### 1c. Interpretation [J]
- NZ underperformed while the policy was being tightened — consistent with a negative investor-tax effect.
- But (i) Canada fell *further* peak-to-trough with **no** comparable tax change, (ii) NZ kept falling after the
  reversal, and (iii) NZ had other simultaneous shocks. So **−12.8pp is an upper bound** on the tax effect, not an
  estimate. Separating the tax effect from the rate shock is not possible with this data — we say so rather than
  pretend otherwise.
- **Transfer to Australia:** Australia's 2026 reform is milder — existing holdings are grandfathered until sale,
  new builds stay eligible, and the CGT change also hits shares (so the relative tilt is smaller). We size the
  Australian overlay at roughly **¼ to ½ of the NZ upper bound**: −3% established houses, −5% units (base);
  −8%/−12% (low). [J]

### 1d. Limits of the comparison
NZ: shorter fixed terms → faster rate pass-through; no capital gains tax beyond bright-line; strong net
*out*-migration to Australia in 2023–25 [V]; smaller, more investor-concentrated market. Australia: mostly variable
mortgages; CGT regime change simultaneous; superannuation alternative for savings; grandfathering means the
effect builds only as stock turns over (slow — decades for the full stock).

---

## 2. Other tax/investor-policy episodes (price outcomes from Dallas Fed [S]; policy details [V])
| Episode | Policy (verify) | Real price after [S] | Read |
|---|---|---|---|
| UK Section 24 (mortgage-interest relief restricted to basic-rate credit, phased Apr 2017–Apr 2020) [V] | investor interest deduction curtailed | UK RHPI 2016Q4 112.7 → 2020Q4 122.5 (**+8.7%**) | no visible national price hit; effect absorbed |
| Netherlands mortgage-interest deductibility cut (gradual from 2014) [V] | owner-occupier deduction reduced | NLD RHPI 2013Q4 79.6 → 2021Q4 126.7 (**+59%**) | low rates swamped tax change |
| Canada foreign-buyer / vacancy taxes (Vancouver 2016, Toronto 2017) [V] | demand-side tax on non-residents | CAN RHPI 2016Q4 181.8 → 2018Q4 178.8 (**−1.6%**) | national pause, then boom resumed to 2022 |
| Ireland post-2008 | credit bust (not a tax-led episode) | IRL RHPI 2007Q4 116.1 → 2012Q4 60.3 (**−48%**) | what a true credit crash looks like |

**Pattern:** investor-tax changes have, on this evidence, produced modest or invisible national price effects
*unless* combined with a rate shock (NZ 2021–23). Rates and credit dominate. [J]

---

## 3. Base rates: 10-year outcomes from expensive starting points
Method: for 12 countries (AUS NZL CAN GBR IRL NLD SWE NOR DNK USA ESP JPN), each year 1985–2015, compute the
price-to-income ratio (RHPI/RPDI) percentile **within that country's own history to date** (expanding window — no
look-ahead), then the next 10 years' real price change. 384 country-years; 114 at the top decile of valuation.

| Outcome (10y real) | All starting points | Top-decile valuation (like Australia now) |
|---|---|---|
| Crash (≤ −25%) | 4.4% | **4.4%** |
| Stagnation (−25% to +5%) | 22.9% | **33.3%** |
| Soft landing / moderate growth (+5% to +30%) | 21.4% | **21.1%** |
| Continued boom (≥ +30%) | 51.3% | **41.2%** |
| Median 10y real change | +32% | **+23%** |
| 10th–90th percentile | −13% to +87% | **−17% to +62%** |

Australia today: price-to-income at the **98th percentile** of its own 1975–2026 history (2026Q2 1.383 vs max
1.388 in 2025Q4). [S]

**Small-sample warning:** the 114 conditioned observations overlap heavily; there are only about **26 independent
episodes**. Almost all of them started during the 1985–2015 era of *falling* interest rates — a tailwind that
pushed valuations up and is unlikely to repeat from an 18-year-high cash rate. **These base rates are therefore
probably too optimistic for 2027–2036.** [J]

## 4. What this means for the forecast
- The analogue base rate is used as one half of the central path (`methodology.md`) — it was the only model that
  added anything over a naive baseline, and only in 2 of 3 backtest windows.
- The NZ policy-break test (below and in `methodology.md`) shows the method **under-predicted the downside** when a
  rate shock and tax change coincided. The *low* scenario is built to include an NZ-like outcome.
