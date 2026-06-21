"""show-nav.py — shows all topbar nav items. Paste output to Claude."""
import re
with open('regime-board.html', encoding='utf-8') as f:
    content = f.read()

# Find the topbar/nav component
for marker in ['topbar-nav', 'topbar', 'NavBar', 'navLinks', 'navItems', '.nav']:
    idx = content.find(marker)
    if idx != -1:
        print(f"=== '{marker}' at char {idx} ===")
        print(content[max(0,idx-50):idx+600])
        print()
        break
