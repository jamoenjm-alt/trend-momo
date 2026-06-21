"""extract-signals.py — shows SignalCell + TrendLadder trigger. Paste ALL output to Claude."""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=1500):
    idx = content.find(start_str)
    if idx == -1:
        print(f'✗  {label} not found')
        return
    print(f'\n{"="*60}')
    print(f'=== {label} (char {idx}) ===')
    print(f'{"="*60}')
    print(content[idx:idx+chars])

grab('SignalCell component', 'function SignalCell')
grab('TrendLadder first line', 'function TrendLadder')
grab('Tooltip state / setTooltip', 'setTooltip', chars=400)
grab('TrendLadder groups map', "['canary','st','lt','all']")
