"""extract-crypto-block.py — shows exact crypto fetch block for surgical replacement"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

start = content.find('const cryptoAssets=[')
end = content.find('const avKey', start)
if start == -1: print('✗ cryptoAssets not found')
elif end == -1: print('✗ avKey not found')
else:
    block = content[start:end]
    print(f'Block is {len(block)} chars:')
    print(repr(block))
