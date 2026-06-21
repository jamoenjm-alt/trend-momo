"""extract-crypto-fetch.py — shows the full crypto fetch block in loadAll"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=3000):
    idx = content.find(start_str)
    if idx == -1: print(f'✗  {label} not found'); return
    print(f'\n{"="*60}\n=== {label} ===\n{"="*60}')
    print(repr(content[idx:idx+chars]))

grab('Crypto fetch block', "cls === 'Crypto'")
grab('CoinCap fetch', 'coincap.io/v2/assets/')
grab('Yahoo fallback for crypto?', 'USD&interval')
