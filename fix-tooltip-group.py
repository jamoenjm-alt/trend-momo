"""
fix-tooltip-group.py — Tooltip only shows pairs for the hovered column
Run: python fix-tooltip-group.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. handleEnter: add group param + store in tooltip state ─────────────────
OLD1 = "handleEnter(e, asset, sigs) { if (!sigs) return; setTooltip({asset,sigs,x:e.clientX,y:e.clientY}); }"
NEW1 = "handleEnter(e, asset, sigs, group) { if (!sigs) return; setTooltip({asset,sigs,x:e.clientX,y:e.clientY,group}); }"
if OLD1 in content:
    content = content.replace(OLD1, NEW1, 1)
    changes += 1
    print('✓  handleEnter: group param added')
elif NEW1 in content:
    print('–  handleEnter already updated')
else:
    print('✗  handleEnter not matched:')
    idx = content.find('handleEnter(e, asset')
    if idx != -1: print(repr(content[idx:idx+120]))

# ── 2. onEnter call: pass group from column index ────────────────────────────
OLD2 = "onEnter:e=>handleEnter(e,asset,sigs)"
NEW2 = "onEnter:e=>handleEnter(e,asset,sigs,['canary','st','lt','all'][i])"
if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    changes += 1
    print("✓  onEnter: group passed by column index")
elif NEW2 in content:
    print('–  onEnter already passes group')
else:
    print('✗  onEnter not matched:')
    idx = content.find('onEnter:e=>handleEnter')
    if idx != -1: print(repr(content[idx:idx+80]))

# ── 3. TrendLadder render: pass group from tooltip state ─────────────────────
OLD3 = "TrendLadder, { asset:tooltip.asset, sigs:tooltip.sigs, x:tooltip.x, y:tooltip.y }"
NEW3 = "TrendLadder, { asset:tooltip.asset, sigs:tooltip.sigs, x:tooltip.x, y:tooltip.y, group:tooltip.group }"
if OLD3 in content:
    content = content.replace(OLD3, NEW3, 1)
    changes += 1
    print('✓  TrendLadder render: group prop passed')
elif NEW3 in content:
    print('–  TrendLadder render already passes group')
else:
    print('✗  TrendLadder render not matched:')
    idx = content.find('TrendLadder, { asset:tooltip')
    if idx != -1: print(repr(content[idx:idx+100]))

# ── 4. TrendLadder: accept group + filter to single group ────────────────────
OLD4 = "function TrendLadder({ asset, sigs, x, y })"
NEW4 = "function TrendLadder({ asset, sigs, x, y, group })"
if OLD4 in content:
    content = content.replace(OLD4, NEW4, 1)
    changes += 1
    print('✓  TrendLadder: group destructured')
elif NEW4 in content:
    print('–  TrendLadder already accepts group')
else:
    print('✗  TrendLadder signature not matched')

# ── 5. Replace the all-groups map with single-group render ───────────────────
OLD5 = "['canary','st','lt','all'].map(g => {"
NEW5 = "[group||'canary'].map(g => {"
if OLD5 in content:
    content = content.replace(OLD5, NEW5, 1)
    changes += 1
    print('✓  TrendLadder: now renders only the hovered column group')
elif NEW5 in content:
    print('–  TrendLadder already filtered to single group')
else:
    print('✗  groups map not matched')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
