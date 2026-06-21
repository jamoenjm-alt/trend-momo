"""check-crypto-fix.py — verify what fix-crypto-yahoo.py did"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('Yahoo crypto fallback injected', 'failedCrypto'),
    ('US Assets in SECTIONS', "label: 'US Assets'"),
    ('US Assets in nav map', "'US Assets': 'Top20'"),
    ('US Assets in nav button', '>US Assets</button>'),
    ('Custom Yahoo fallback', 'customFailed'),
    ('Top 20 US still present (should be gone)', "'Top 20 US'"),
]

for label, needle in checks:
    found = needle in content
    print(f"{'✓' if found else '✗'}  {label}")
