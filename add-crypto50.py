"""
add-crypto50.py — Expands crypto section to ~top 50 by market cap
Run: python add-crypto50.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Add new crypto tickers to WATCHLIST ───────────────────────────────────
OLD_LAST_CRYPTO = "  { ticker: 'SUI',  name: 'Sui',                cls: 'Crypto'    },"

NEW_CRYPTO_BLOCK = """  { ticker: 'SUI',  name: 'Sui',                cls: 'Crypto'    },
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
  { ticker: 'WIF',  name: 'Dogwifhat',          cls: 'Crypto'    },"""

if OLD_LAST_CRYPTO in content and 'DOGE' not in content:
    content = content.replace(OLD_LAST_CRYPTO, NEW_CRYPTO_BLOCK, 1)
    changes += 1
    print('✓  36 new crypto tickers added to WATCHLIST')
elif 'DOGE' in content:
    print('–  Crypto already expanded')
else:
    print('✗  Last crypto entry not matched:')
    idx = content.find("cls: 'Crypto'")
    if idx != -1: print(repr(content[max(0,idx-60):idx+60]))

# ── 2. Add CoinCap IDs for new tickers ───────────────────────────────────────
OLD_COINCAP = """const CRYPTO_COINCAP_IDS = {
  BTC: 'bitcoin', ETH: 'ethereum', SOL: 'solana', XRP: 'ripple',
  BNB: 'binance-coin', ADA: 'cardano', LINK: 'chainlink',
  TON: 'the-open-network', AVAX: 'avalanche-2', SUI: 'sui',
};"""

NEW_COINCAP = """const CRYPTO_COINCAP_IDS = {
  BTC: 'bitcoin',          ETH: 'ethereum',          SOL: 'solana',
  XRP: 'ripple',           BNB: 'binance-coin',      ADA: 'cardano',
  LINK: 'chainlink',       TON: 'the-open-network',  AVAX: 'avalanche-2',
  SUI: 'sui',              DOGE: 'dogecoin',          DOT: 'polkadot',
  TRX: 'tron',             MATIC: 'matic-network',   LTC: 'litecoin',
  BCH: 'bitcoin-cash',     APT: 'aptos',             NEAR: 'near-protocol',
  ARB: 'arbitrum',         ATOM: 'cosmos',            OP: 'optimism',
  INJ: 'injective-protocol', HBAR: 'hedera-hashgraph', FIL: 'filecoin',
  AAVE: 'aave',            VET: 'vechain',            XLM: 'stellar',
  ETC: 'ethereum-classic', ALGO: 'algorand',          UNI: 'uniswap',
  ICP: 'internet-computer', GRT: 'the-graph',         SAND: 'the-sandbox',
  MANA: 'decentraland',    MKR: 'maker',              RUNE: 'thorchain',
  LDO: 'lido-dao',         STX: 'blockstack',         FTM: 'fantom',
  SEI: 'sei-network',      EGLD: 'elrond-erd-2',      DYDX: 'dydx',
  PEPE: 'pepe',            FLOKI: 'floki',             WIF: 'dogwifcoin',
};"""

if OLD_COINCAP in content:
    content = content.replace(OLD_COINCAP, NEW_COINCAP, 1)
    changes += 1
    print('✓  CRYPTO_COINCAP_IDS expanded with all 46 tickers')
elif 'DOGE:' in content and 'CRYPTO_COINCAP_IDS' in content:
    print('–  CRYPTO_COINCAP_IDS already expanded')
else:
    print('✗  CRYPTO_COINCAP_IDS not matched:')
    idx = content.find('CRYPTO_COINCAP_IDS')
    if idx != -1: print(repr(content[idx:idx+200]))

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
