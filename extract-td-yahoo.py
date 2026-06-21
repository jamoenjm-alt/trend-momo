"""extract-td-yahoo.py — shows TD batch + Yahoo fallback code"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=2500):
    idx = content.find(start_str)
    if idx == -1: print(f'✗  {label} not found'); return
    print(f'\n{"="*60}\n=== {label} ===\n{"="*60}')
    print(content[idx:idx+chars])

grab('TD batch fetch', 'tdResults')
grab('Yahoo stock fallback', 'yahoo.com/v8/finance/chart')
grab('Custom in TD filter', "includes(a.cls)")
