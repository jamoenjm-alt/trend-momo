"""
extract-tooltip.py — prints the TrendLadder / SignalCell component code
Run: python extract-tooltip.py
Paste ALL output back to Claude.
"""

with open('regime-board.html', 'r', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=4000):
    idx = content.find(start_str)
    if idx == -1:
        print(f'✗  {label} not found')
        return
    print(f'\n{"="*60}')
    print(f'=== {label} (at char {idx}) ===')
    print(f'{"="*60}')
    print(content[idx:idx+chars])

grab('SignalCell component', 'function SignalCell')
grab('TrendLadder component', 'function TrendLadder')
grab('Tooltip CSS block', '.tooltip {', chars=600)
grab('tt-table CSS block', '.tt-table {', chars=600)
grab('panelW variable', 'const panelW')
