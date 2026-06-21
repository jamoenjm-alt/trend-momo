"""extract-fetchstooq.py — shows fetchStooq + TD/Yahoo fallback chain"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, marker, chars=800):
    idx = content.find(marker)
    if idx == -1: print(f'✗ {label} not found'); return
    print(f'\n=== {label} ===')
    print(content[idx:idx+chars])

grab('fetchStooq function', 'fetchStooq')
grab('TD Yahoo fallback chain', 'tdTickers.filter(t=>!tdResults[t])')
