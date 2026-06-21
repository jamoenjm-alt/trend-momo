"""extract-crypto.py — shows current crypto tickers + data fetch logic"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

def grab(label, start_str, chars=1500):
    idx = content.find(start_str)
    if idx == -1: print(f'✗  {label} not found'); return
    print(f'\n{"="*55}\n=== {label} ===\n{"="*55}')
    print(content[idx:idx+chars])

# Current crypto entries in WATCHLIST
import re
cryptos = re.findall(r"\{[^}]*cls:\s*'Crypto'[^}]*\}", content)
print("=== Current Crypto WATCHLIST entries ===")
for c in cryptos:
    print(c)

# Crypto fetch function
grab('Crypto fetch logic', 'CoinCap')
grab('Yahoo Finance crypto mapping', 'BTC-USD')
