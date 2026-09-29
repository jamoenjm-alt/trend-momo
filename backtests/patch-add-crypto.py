# -*- coding: utf-8 -*-
# Add 18 verified new coins to the crypto section: WATCHLIST + CRYPTO_COINCAP_IDS
# (regime-board.html) and CRYPTO_CG (update-prices.py). CoinGecko ids verified live.
import io

# ticker, display name, coingecko id
NEW = [
    ("PENDLE","Pendle","pendle"),
    ("RUNE","THORChain","thorchain"),
    ("CAKE","PancakeSwap","pancakeswap-token"),
    ("XTZ","Tezos","tezos"),
    ("JASMY","JasmyCoin","jasmycoin"),
    ("ZRX","0x Protocol","0x"),
    ("IMX","Immutable","immutable-x"),
    ("DAG","Constellation","constellation-labs"),
    ("APE","ApeCoin","apecoin"),
    ("AZERO","Aleph Zero","aleph-zero"),
    ("PRIME","Echelon Prime","echelon-prime"),
    ("WIF","dogwifhat","dogwifcoin"),
    ("FET","Fetch.ai","fetch-ai"),
    ("PAXG","PAX Gold","pax-gold"),
    ("FARTCOIN","Fartcoin","fartcoin"),
    ("USELESS","Useless","useless-3"),
    ("ASTER","Aster","aster-2"),
    ("BERT","Bert","bertram-the-pomeranian"),
]

def rep(src, old, new, label):
    n = src.count(old)
    assert n == 1, 'EXPECTED 1 for [%s] got %d' % (label, n)
    print('ok:', label)
    return src.replace(old, new)

# ---------- regime-board.html ----------
H='regime-board.html'
h=io.open(H,encoding='utf-8').read()

wl = ''.join("  { ticker: '%s', name: '%s', cls: 'Crypto' },\n" % (t,name) for t,name,_ in NEW)
h = rep(h,
    "  { ticker: 'SEI',     name: 'Sei',                                 cls: 'Crypto' },\n  // Commodities (ETF proxies)",
    "  { ticker: 'SEI',     name: 'Sei',                                 cls: 'Crypto' },\n" + wl + "  // Commodities (ETF proxies)",
    "WATCHLIST crypto rows")

cc = ''.join("  %s: '%s',\n" % (t,cg) for t,_,cg in NEW)
h = rep(h,
    "  SEI: 'sei-network',\n};",
    "  SEI: 'sei-network',\n" + cc + "};",
    "CRYPTO_COINCAP_IDS")

io.open(H,'w',encoding='utf-8',newline='').write(h)
nH=open(H,'rb').read().count(b'\x00'); print('html NULs:',nH); assert nH==0

# ---------- update-prices.py ----------
U='update-prices.py'
u=io.open(U,encoding='utf-8').read()
cg = ''.join('    "%s": "%s",\n' % (t,cgid) for t,_,cgid in NEW)
u = rep(u,
    '    "SEI": "sei-network",\n}',
    '    "SEI": "sei-network",\n' + cg + '}',
    "CRYPTO_CG (baker)")
io.open(U,'w',encoding='utf-8',newline='').write(u)
nU=open(U,'rb').read().count(b'\x00'); print('py NULs:',nU); assert nU==0

# verify counts
print('crypto rows now:', h.count("cls: 'Crypto'"))
print('coincap ids now:', h.count(": '") )  # rough
print('added', len(NEW), 'coins')
