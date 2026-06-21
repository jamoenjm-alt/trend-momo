"""Extract the current state of doAdd and go() functions + key exposure"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, marker, chars=400):
    idx = content.find(marker)
    if idx == -1: print(f'✗ {label} not found'); return
    print(f'\n=== {label} (at {idx}) ===')
    print(repr(content[idx:idx+chars]))

grab('TD_KEY line', "const TD_KEY = '")
grab('AV_KEY_DEFAULT line', "const AV_KEY_DEFAULT = '")
grab('window._KEYS', 'window._KEYS')
grab('function doAdd', 'function doAdd(')
grab('function go()', 'function go()')
grab('async function go', 'async function go')
