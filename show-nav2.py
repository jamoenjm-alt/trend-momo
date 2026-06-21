"""show-nav2.py — finds the actual rendered nav links in the React component"""
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

# Find ALL occurrences of topbar-nav (second one will be the React render)
idx = 0
found = []
while True:
    idx = content.find('topbar-nav', idx)
    if idx == -1: break
    found.append(idx)
    idx += 1

print(f"Found 'topbar-nav' at {len(found)} location(s)")
for i, pos in enumerate(found):
    print(f"\n=== Occurrence {i+1} at char {pos} ===")
    print(content[max(0,pos-30):pos+400])
