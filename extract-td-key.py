"""extract-td-key.py — shows TD key and custom ticker flow"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, marker, chars=300):
    idx = content.find(marker)
    if idx == -1: print(f'✗ {label} not found'); return
    print(f'\n=== {label} ===')
    print(content[idx:idx+chars])

grab('TD_KEY', "TD_KEY = '")
grab('customFailed filter', 'customFailed=WATCHLIST.filter')
grab('cache read block', 'CACHE_TTL')
grab('AV fallback in universal', 'AV US stock')
