"""extract-av-news.py — checks AV key, news data format, and setData context"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, marker, chars=400):
    idx = content.find(marker)
    if idx == -1: print(f'✗ {label} not found'); return
    print(f'\n=== {label} ===')
    print(content[idx:idx+chars])

grab('AV_KEY_DEFAULT', 'AV_KEY_DEFAULT')
grab('FH_KEY_DEFAULT', 'FH_KEY_DEFAULT')
grab('avKey assignment', 'const avKey')
grab('news in data shape', 'news:')
grab('NewsCell render', 'NewsCell')
grab('Crypto news IIFE', 'Crypto news via Finnhub')
grab('setData usage', 'setData(newData)')
