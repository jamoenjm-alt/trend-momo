// ============================================================================
// CRYPTO_RISK_FLAGS — research block for Trend Momo. NOT a score input.
// Researched 8 September 2026. Sources listed per field.
//
// THIS REOPENS A SETTLED DECISION. Read before integrating.
// regime-board.html already declares crypto fundamentals not applicable on
// purpose: BALANCE_SHEET['BTC'].score = null with the tip "Decentralised asset
// — balance sheet not applicable", and valueScore()'s own comment says value
// "has no meaning for crypto/commodities/forex" and returns an honest N/A.
// That call was correct and this file does not overturn it.
//
// WHY IT STAYS OUT OF valueScore()
// Tested properly (Presto Research, 761 days), a fundamentals index built on
// fee multiples TRAILED BITCOIN BY ~350 PERCENTAGE POINTS and lost on 65.7%
// of days. Over the same window DOGE — zero fundamentals by design — returned
// 187% against the index's 53%. Wiring this into a score would be adding a
// metric already known to underperform, which is the one thing the protocol
// forbids. It also matches this repo's own results: momentum rotation 2.7%
// vs 14.4% buy-and-hold.
//
// WHAT IT IS FOR: `flags`. An eliminating layer, surfaced as a tooltip or a
// warning icon on the ticker cell. It answers "is there something disqualifying
// here that price cannot see" — not "which coin is cheapest".
//
// `context` is deliberately nested so nothing top-level invites a sort.
// feeMultiple = market cap / annualised protocol fees, the nearest analogue to
// a P/E. Comparing across assets is mostly meaningless anyway because `accrual`
// differs: Bitcoin's fees pay miners (a security COST no holder ever sees),
// Ethereum's are burned, Hyperliquid's fund a buyback. Reading BTC's 19,477x
// against HYPE's 23x as the same measurement is the standard error in the field.
// ============================================================================

window.CRYPTO_RISK_FLAGS = {
  asAt: "2026-09-08",
  sources: {
    marketCap: "CoinGecko, live",
    chainFees: "DefiLlama /fees/chains, 30-day",
    hypeRevenue: "Hyperliquid quarterly reported",
    zecMetrics: "Datawallet, Aug 2026",
  },

  BTC: {
    context: { feeMultiple: 19477, feesAnnual: "$81M", marketCap: "$1,583B" },
    accrual: "MINERS — holders get nothing. Fees are a security cost.",
    revTrend: "flat",
    flags: [],
    note: "Most expensive asset in crypto on fees by ~85x, and the best performer YTD (-28.9% vs SOL -39.6%). That inversion is the whole point."
  },
  ETH: {
    context: { feeMultiple: 2326, feesAnnual: "$131M", marketCap: "$304B" },
    accrual: "BURNED (EIP-1559) — genuinely accrues to holders",
    revTrend: "down",
    flags: [],
    note: "62% below its $4,950 ATH."
  },
  BNB: {
    context: { feeMultiple: 467, feesAnnual: "$216M", marketCap: "$100.8B" },
    accrual: "BURNED — quarterly auto-burn",
    revTrend: "flat", flags: []
  },
  SOL: {
    context: { feeMultiple: 227, feesAnnual: "$268M", marketCap: "$60.8B" },
    accrual: "~50% burned, ~50% validators",
    revTrend: "down",
    flags: ["TVL HALVED: $11.5B (Aug 2025) -> ~$5.5B. The 'cheap' multiple follows a shrinking network, not an undervalued one."],
    note: "75% below its $294 Jan-2025 high."
  },
  TRX: {
    context: { feeMultiple: 106, feesAnnual: "$302M", marketCap: "$32.1B" },
    accrual: "BURNED",
    revTrend: "flat", flags: [],
    note: "Second-cheapest major on fees. Rarely discussed, which is itself informative about how little fees drive attention."
  },
  HYPE: {
    context: { feeMultiple: 23, feesAnnual: "$819M", marketCap: "$18.7B" },
    accrual: "ASSISTANCE FUND BUYBACK — most direct accrual in crypto",
    revTrend: "FALLING HARD",
    flags: [
      "REVENUE -43% WHILE VOLUME HITS RECORDS: $357M -> $295M -> $217M -> $202M per quarter.",
      "CAUSE IS STRUCTURAL, NOT CYCLICAL: HIP-3 lets builders deploy markets and keep up to half the fees. Builder share went 2% -> ~50% of volume in 2026. The protocol is being disintermediated by its own design.",
      "BUYBACK -49%: Assistance Fund $290M -> $149M per quarter. The mechanism supporting the token is shrinking with the revenue."
    ],
    note: "Cheapest major on fees at 23x — but the multiple is computed on a numerator falling 43%. A cheap multiple on collapsing revenue is not cheap."
  },
  ZEC: {
    context: { feeMultiple: null, feesAnnual: "negligible", marketCap: "$19.5B" },
    accrual: "MINERS — holders get nothing",
    revTrend: "n/a",
    flags: [
      "FOUR-YEAR COUNTERFEITING FLAW: sat in the Orchard proof circuit May 2022 - May 2026. Could mint ZEC with NO ON-CHAIN TRACE.",
      "PERMANENTLY UNAUDITABLE: whether it was ever exploited cannot be determined, because the zero-knowledge proofs hide the pool's internals. CoinDesk Research found evidence pointing away from exploitation; proof is impossible by construction.",
      "$1.7B STRANDED: 3.66M ZEC sits in the sealed Orchard pool behind a turnstile capping withdrawals at verified deposits. Migration is voluntary and incomplete.",
      "USAGE FLAT THROUGH THE ENTIRE RALLY: public transactions ~8,500/day, unchanged while price ran 2,496%.",
      "LEVERAGE: futures volume ran 9:1 against spot; open interest ~13% of market cap."
    ],
    genuinePositive: "Shielded supply went 8% -> 31% of coins in 18 months, more than the prior eight years combined. Hashrate at a record 17.2 GH/s. The adoption is real; it is the price that has outrun it.",
    note: "Scores 10.0/10 and Fear/Greed 100 on this board. By the board's OWN guide — 'All STRONG UPTREND = likely late' and max-greed returned 2.7% vs max-fear 8.0% in your backtests — the top score is the warning."
  },
  XRP: {
    context: { feeMultiple: null, feesAnnual: "trivial", marketCap: "$87.9B" },
    accrual: "burned, but amounts are immaterial",
    revTrend: "n/a",
    flags: ["REGULATORY: CLARITY Act stalled in the Senate. 75% below its $3.65 high."]
  },
  DOGE: {
    context: { feeMultiple: null, feesAnnual: "negligible", marketCap: "—" },
    accrual: "MINERS",
    revTrend: "n/a",
    flags: ["NO FUNDAMENTALS BY DESIGN."],
    note: "Kept on the board deliberately as the control. Over the 761-day Presto window DOGE returned 187% against the fundamentals index's 53%. If a fundamentals ranking cannot explain DOGE, it cannot explain crypto."
  },

  // ---- market-wide base rates, for the header or the Guide ----
  baseRates: {
    tokensFailed: "53.2% of all cryptocurrencies ever listed have failed (CoinGecko). Survival 46.8%. 11.56M died in 2025 alone.",
    hacksH1_2026: "$972M stolen across 207 incidents (vs 83 in H1 2025). Infrastructure compromises were 15% of incidents but 76% of losses.",
    drawdowns: "Majors sit 50-75% below all-time highs. BTC -50% from $126,000 (Oct 2025), ETH -62%, SOL -75%, XRP -75%.",
    currentMove: "The +25-40% across majors in the three weeks to 8 Sep was a RATES trade — Waller signalling a hold produced BTC's largest ETF inflow in nine months. No protocol's fee line moved. The board reads this as STRONG UPTREND everywhere because the board reads price."
  }
};
