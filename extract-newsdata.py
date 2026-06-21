"""extract-newsdata.py — finds newsData state and how it's set"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, marker, chars=500):
    idx = content.find(marker)
    if idx == -1: print(f'✗ {label} not found'); return
    print(f'\n=== {label} ===')
    print(content[idx:idx+chars])

grab('newsData useState', 'newsData')
grab('setNewsData', 'setNewsData')
grab('AV news fetch', 'fetchAVNews')
grab('AV_KEY_DEFAULT value', "AV_KEY_DEFAULT = '")
grab('FH_KEY value', "FH_KEY_DEFAULT = '")
grab('news state set', 'setNews')
