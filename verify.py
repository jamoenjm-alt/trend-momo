"""verify.py — confirms what's actually in the HTML. Paste ALL output to Claude."""
import re
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

# 1. Check FH key
m = re.search(r"const FH_KEY_DEFAULT\s*=\s*'([^']*)'", content)
print("FH_KEY_DEFAULT:", repr(m.group(1)) if m else "NOT FOUND")

# 2. Check htu-reg-table CSS
idx = content.find('.htu-reg-table {')
print("\nhtu-reg-table CSS:", repr(content[idx:idx+120]) if idx!=-1 else "NOT FOUND")

# 3. Check if htu-reg-table uses <table> or divs in the HTML
idx2 = content.find('htu-reg-table')
print("\nFirst htu-reg-table usage:", repr(content[idx2:idx2+60]) if idx2!=-1 else "NOT FOUND")

# 4. Show the actual How To Use regime section HTML
idx3 = content.find('htu-badge htu-sb')
print("\nRegime badges HTML:", repr(content[max(0,idx3-20):idx3+300]) if idx3!=-1 else "NOT FOUND")
