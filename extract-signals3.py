"""extract-signals3.py"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=1200):
    idx = content.find(start_str)
    if idx == -1: print(f'✗  {label} not found'); return
    print(f'\n{"="*55}\n=== {label} (char {idx}) ===\n{"="*55}')
    print(content[idx:idx+chars])

grab('handleEnter function', 'handleEnter')
# Show broader context around the onEnter call (200 chars before)
idx = content.find('onEnter:e=>handleEnter')
if idx != -1:
    print(f'\n=== onEnter call site context (char {idx}) ===')
    print(content[max(0,idx-600):idx+200])
