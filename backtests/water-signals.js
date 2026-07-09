const MA_PAIRS = [
  { slow: 10,  fast: 3,  group: 'canary' },  // Coal Mine Canary
  { slow: 15,  fast: 5,  group: 'canary' },
  { slow: 42,  fast: 10, group: 'st'     },  // ST Trend Momo
  { slow: 50,  fast: 15, group: 'st'     },
  { slow: 63,  fast: 21, group: 'st'     },
  { slow: 84,  fast: 21, group: 'lt'     },  // LT Trend Momo
  { slow: 126, fast: 42, group: 'lt'     },
  { slow: 168, fast: 42, group: 'lt'     },
  { slow: 200, fast: 50, group: 'all'    },  // extended — only in All Indicators
  { slow: 252, fast: 63, group: 'all'    },
];

const WATCHLIST = [
  // Personal watchlist
  { ticker: 'AAPL',    name: 'Apple Inc',             cls: 'Watch'     },
  { ticker: 'MSFT',    name: 'Microsoft Corp',         cls: 'Watch'     },
  { ticker: 'TSLA',    name: 'Tesla Inc',              cls: 'Watch'     },
  { ticker: 'NVDA',    name: 'Nvidia Corp',            cls: 'Watch'     },
  { ticker: 'ASML',    name: 'ASML Holding',           cls: 'Watch'     },
  { ticker: 'IVV',     name: 'iShares S&P 500 ETF',   cls: 'Watch'     },
  { ticker: 'PCT',     name: 'PureCycle Technologies', cls: 'Watch'     },
  { ticker: 'SOUN',    name: 'SoundHound AI',          cls: 'Watch'     },
  { ticker: 'SPCX',    name: 'SpaceX',                  cls: 'Watch'     },
  // Top 20 US stocks by market cap
  { ticker: 'AAPL',    name: 'Apple Inc',              cls: 'Top20'     },
  { ticker: 'MSFT',    name: 'Microsoft Corp',         cls: 'Top20'     },
  { ticker: 'NVDA',    name: 'Nvidia Corp',            cls: 'Top20'     },
  { ticker: 'AMZN',    name: 'Amazon.com Inc',         cls: 'Top20'     },
  { ticker: 'GOOGL',   name: 'Alphabet Inc Cl A',      cls: 'Top20'     },
  { ticker: 'META',    name: 'Meta Platforms',         cls: 'Top20'     },
  { ticker: 'TSLA',    name: 'Tesla Inc',              cls: 'Top20'     },
  { ticker: 'BRK.B',   name: 'Berkshire Hathaway B',  cls: 'Top20'     },
  { ticker: 'AVGO',    name: 'Broadcom Inc',           cls: 'Top20'     },
  { ticker: 'JPM',     name: 'JPMorgan Chase',         cls: 'Top20'     },
  { ticker: 'LLY',     name: 'Eli Lilly & Co',        cls: 'Top20'     },
  { ticker: 'V',       name: 'Visa Inc',               cls: 'Top20'     },
  { ticker: 'UNH',     name: 'UnitedHealth Group',     cls: 'Top20'     },
  { ticker: 'ORCL',    name: 'Oracle Corp',            cls: 'Top20'     },
  { ticker: 'MA',      name: 'Mastercard Inc',         cls: 'Top20'     },
  { ticker: 'XOM',     name: 'Exxon Mobil Corp',       cls: 'Top20'     },
  { ticker: 'NFLX',    name: 'Netflix Inc',            cls: 'Top20'     },
  { ticker: 'COST',    name: 'Costco Wholesale',       cls: 'Top20'     },
  { ticker: 'WMT',     name: 'Walmart Inc',            cls: 'Top20'     },
  { ticker: 'HD',      name: 'Home Depot Inc',         cls: 'Top20'     },
  // Crypto
  { ticker: 'BTC',     name: 'Bitcoin',                cls: 'Crypto'    },
  { ticker: 'ETH',     name: 'Ethereum',               cls: 'Crypto'    },
  { ticker: 'SOL',  name: 'Solana',             cls: 'Crypto'    },
  { ticker: 'XRP',  name: 'XRP',                cls: 'Crypto'    },
  { ticker: 'BNB',  name: 'BNB',                cls: 'Crypto'    },
  { ticker: 'ADA',  name: 'Cardano',            cls: 'Crypto'    },
  { ticker: 'LINK', name: 'Chainlink',          cls: 'Crypto'    },
  { ticker: 'TON',  name: 'Toncoin',            cls: 'Crypto'    },
  { ticker: 'AVAX', name: 'Avalanche',          cls: 'Crypto'    },
  { ticker: 'SUI',  name: 'Sui',                cls: 'Crypto'    },
  { ticker: 'DOGE', name: 'Dogecoin',           cls: 'Crypto'    },
  { ticker: 'DOT',  name: 'Polkadot',           cls: 'Crypto'    },
  { ticker: 'TRX',  name: 'Tron',               cls: 'Crypto'    },
  { ticker: 'MATIC',name: 'Polygon',            cls: 'Crypto'    },
  { ticker: 'LTC',  name: 'Litecoin',           cls: 'Crypto'    },
  { ticker: 'BCH',  name: 'Bitcoin Cash',       cls: 'Crypto'    },
  { ticker: 'APT',  name: 'Aptos',              cls: 'Crypto'    },
  { ticker: 'NEAR', name: 'Near Protocol',      cls: 'Crypto'    },
  { ticker: 'ARB',  name: 'Arbitrum',           cls: 'Crypto'    },
  { ticker: 'ATOM', name: 'Cosmos',             cls: 'Crypto'    },
  { ticker: 'OP',   name: 'Optimism',           cls: 'Crypto'    },
  { ticker: 'INJ',  name: 'Injective',          cls: 'Crypto'    },
  { ticker: 'HBAR', name: 'Hedera',             cls: 'Crypto'    },
  { ticker: 'FIL',  name: 'Filecoin',           cls: 'Crypto'    },
  { ticker: 'AAVE', name: 'Aave',               cls: 'Crypto'    },
  { ticker: 'VET',  name: 'VeChain',            cls: 'Crypto'    },
  { ticker: 'XLM',  name: 'Stellar',            cls: 'Crypto'    },
  { ticker: 'ETC',  name: 'Ethereum Classic',   cls: 'Crypto'    },
  { ticker: 'ALGO', name: 'Algorand',           cls: 'Crypto'    },
  { ticker: 'UNI',  name: 'Uniswap',            cls: 'Crypto'    },
  { ticker: 'ICP',  name: 'Internet Computer',  cls: 'Crypto'    },
  { ticker: 'GRT',  name: 'The Graph',          cls: 'Crypto'    },
  { ticker: 'SAND', name: 'The Sandbox',        cls: 'Crypto'    },
  { ticker: 'MANA', name: 'Decentraland',       cls: 'Crypto'    },
  { ticker: 'MKR',  name: 'Maker',              cls: 'Crypto'    },
  { ticker: 'RUNE', name: 'THORChain',          cls: 'Crypto'    },
  { ticker: 'LDO',  name: 'Lido DAO',           cls: 'Crypto'    },
  { ticker: 'STX',  name: 'Stacks',             cls: 'Crypto'    },
  { ticker: 'FTM',  name: 'Fantom',             cls: 'Crypto'    },
  { ticker: 'SEI',  name: 'Sei',                cls: 'Crypto'    },
  { ticker: 'EGLD', name: 'MultiversX',         cls: 'Crypto'    },
  { ticker: 'DYDX', name: 'dYdX',               cls: 'Crypto'    },
  { ticker: 'PEPE', name: 'Pepe',               cls: 'Crypto'    },
  { ticker: 'FLOKI',name: 'Floki',              cls: 'Crypto'    },
  { ticker: 'WIF',  name: 'Dogwifhat',          cls: 'Crypto'    },
  // Commodities (via ETF proxies)
  { ticker: 'GLD',     name: 'Gold (GLD ETF)',         cls: 'Commodity' },
  { ticker: 'SLV',     name: 'Silver (SLV ETF)',       cls: 'Commodity' },
  { ticker: 'PALL',    name: 'Palladium (PALL ETF)',   cls: 'Commodity' },
  { ticker: 'PPLT',    name: 'Platinum (PPLT ETF)',    cls: 'Commodity' },
  // ASX
  { ticker: 'MQG',     name: 'Macquarie Group',        cls: 'ASX'       },
  { ticker: 'A2M',     name: 'a2 Milk Company',        cls: 'ASX'       },
  { ticker: 'ANZ',     name: 'ANZ Banking Group',      cls: 'ASX'       },
  { ticker: 'CBA',  name: 'Commonwealth Bank',  cls: 'ASX'       },
  { ticker: 'BHP',  name: 'BHP Group',           cls: 'ASX'       },
  { ticker: 'WBC',  name: 'Westpac Banking',     cls: 'ASX'       },
  { ticker: 'NAB',  name: 'National Australia Bank', cls: 'ASX'   },
  { ticker: 'WES',  name: 'Wesfarmers',          cls: 'ASX'       },
  { ticker: 'CSL',  name: 'CSL Limited',         cls: 'ASX'       },
  { ticker: 'WDS',  name: 'Woodside Energy',     cls: 'ASX'       },
  { ticker: 'FMG',  name: 'Fortescue Metals',    cls: 'ASX'       },
  // Hong Kong
  { ticker: '1211.HK', name: 'BYD Co',                cls: 'HK'        },
  // Global Indices (ETFs)
  { ticker: 'SPY',  name: 'S&P 500 ETF',            cls: 'Index'     },
  { ticker: 'QQQ',  name: 'NASDAQ 100 ETF',        cls: 'Index'     },
  { ticker: 'DIA',  name: 'Dow Jones ETF',          cls: 'Index'     },
  { ticker: 'EWJ',  name: 'Japan (Nikkei) ETF',    cls: 'Index'     },
  { ticker: 'EWG',  name: 'Germany (DAX) ETF',     cls: 'Index'     },
  { ticker: 'EWU',  name: 'UK (FTSE) ETF',         cls: 'Index'     },
  { ticker: 'FXI',  name: 'China Large Cap ETF',   cls: 'Index'     },
  { ticker: 'INDA', name: 'India ETF',              cls: 'Index'     },
  { ticker: 'EEM',  name: 'MSCI Emerging Mkts (BRICS proxy)', cls: 'Index' },
  // Forex (vs USD)
  { ticker: 'EURUSD', name: 'Euro / USD',           cls: 'Forex'     },
  { ticker: 'GBPUSD', name: 'British Pound / USD',  cls: 'Forex'     },
  { ticker: 'USDJPY', name: 'USD / Japanese Yen',   cls: 'Forex'     },
  { ticker: 'AUDUSD', name: 'Australian Dollar / USD', cls: 'Forex'  },
  { ticker: 'USDCAD', name: 'USD / Canadian Dollar', cls: 'Forex'    },
  { ticker: 'DXY',    name: 'US Dollar Index',           cls: 'Forex'    },
];

function sma(closes, w) {
  if (!closes || closes.length < w) return null;
  const slice = closes.slice(-w);
  return slice.reduce((a, b) => a + b, 0) / w;
}

function scoreToRegime(score) {
  if (score === null || score === undefined || isNaN(score)) return { label: 'No Data',     key: 'NO_DATA',     rank: 99 };
  if (score >  0.6) return { label: 'Strong Bull', key: 'STRONG_BULL', rank: 0 };
  if (score >  0.2) return { label: 'Weak Bull',   key: 'WEAK_BULL',   rank: 1 };
  if (score > -0.2) return { label: 'Sideways',    key: 'SIDEWAYS',    rank: 2 };
  if (score > -0.6) return { label: 'Weak Bear',   key: 'WEAK_BEAR',   rank: 3 };
  return                    { label: 'Strong Bear', key: 'STRONG_BEAR', rank: 4 };
}

function computeSignals(closes) {
  const price = closes[closes.length - 1];
  // Compute all needed MAs
  const periods = [...new Set(MA_PAIRS.flatMap(p => [p.slow, p.fast]))];
  const mas = {};
  for (const n of periods) { if (closes.length >= n) mas[n] = sma(closes, n); }
  // Each pair: Trend = price vs slow MA, Momo = fast MA vs slow MA
  const pairSigs = MA_PAIRS.map(({ slow, fast, group }) => {
    const slowMA = mas[slow] ?? null;
    const fastMA = mas[fast] ?? null;
    return {
      slow, fast, group, slowMA, fastMA,
      trend: slowMA != null ? (price > slowMA ? 1 : -1) : null,
      momo:  (fastMA != null && slowMA != null) ? (fastMA > slowMA ? 1 : -1) : null,
    };
  });
  // Average non-null signals per column group
  const colAvg = (groups) => {
    const vals = pairSigs
      .filter(p => groups.includes(p.group))
      .flatMap(p => [p.trend, p.momo])
      .filter(s => s != null);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  };
  const canary  = colAvg(['canary']);
  const stTrend = colAvg(['st']);
  const ltTrend = colAvg(['lt']);
  const allInd  = colAvg(['canary', 'st', 'lt', 'all']);
  return { price, mas, pairSigs, canary, stTrend, ltTrend, allInd };
}

function buyScore(sigs) {
  if (!sigs) return null;
  const { canary, stTrend, ltTrend, allInd } = sigs;
  const weighted = [[canary,1],[stTrend,2],[ltTrend,3],[allInd,4]];
  let wSum = 0, wTot = 0;
  for (const [v, w] of weighted) { if (v != null) { wSum += v * w; wTot += w; } }
  if (!wTot) return null;
  const raw  = wSum / wTot;
  const base = (raw + 1) / 2 * 9;
  const stab = sigs.stability;
  const bonus = stab === 'very_stable' ? 1 : stab === 'stable' ? 0.5 : stab === 'unstable' ? -0.5 : -1;
  return Math.min(10, Math.max(0, base + bonus));
}

module.exports={MA_PAIRS,WATCHLIST,computeSignals,buyScore,scoreToRegime,sma};