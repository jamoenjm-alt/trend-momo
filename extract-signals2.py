"""extract-signals2.py — finds where SignalCell is called and tooltip is rendered"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=800):
    idx = content.find(start_str)
    if idx == -1: print(f'✗  {label} not found'); return
    print(f'\n{"="*55}\n=== {label} (char {idx}) ===\n{"="*55}')
    print(content[idx:idx+chars])

grab('SignalCell call site', 'SignalCell, {')
grab('TrendLadder render call', 'TrendLadder, {')
grab('onEnter definition', 'onEnter:')
