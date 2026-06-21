"""extract-crypto2.py — shows crypto loading logic in loadAll"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=2000):
    idx = content.find(start_str)
    if idx == -1: print(f'✗  {label} not found'); return
    print(f'\n{"="*55}\n=== {label} ===\n{"="*55}')
    print(content[idx:idx+chars])

grab('Crypto loading in loadAll', 'CRYPTO_COINCAP_IDS[')
grab('CoinCap fetch', 'coincap.io')
