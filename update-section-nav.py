"""
update-section-nav.py — Replaces scroll nav with filter tabs.
Click a tab → only that section's rows show. "All" resets.
Run: python update-section-nav.py  then: .\\git-push.bat
"""
import re, shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. Replace section nav CSS ────────────────────────────────────────────────
OLD_CSS = """
    /* ── Section jump nav ─────────────────────────────────── */
    #section-nav {
      position: sticky;
      top: 0;
      z-index: 80;
      background: #0f172a;
      border-bottom: 1px solid #1e293b;
      padding: 0 14px;
      display: flex;
      align-items: center;
      gap: 4px;
      overflow-x: auto;
      scrollbar-width: none;
      -ms-overflow-style: none;
      white-space: nowrap;
    }
    #section-nav::-webkit-scrollbar { display: none; }
    .snav-btn {
      background: none;
      border: none;
      color: #64748b;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      padding: 8px 10px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: color 0.15s, border-color 0.15s;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .snav-btn:hover { color: #e2e8f0; }
    .snav-btn.active { color: #60a5fa; border-bottom-color: #3b82f6; }"""

NEW_CSS = """
    /* ── Section filter nav ────────────────────────────────── */
    #section-nav {
      position: sticky;
      top: 0;
      z-index: 80;
      background: #0f172a;
      border-bottom: 2px solid #1e293b;
      padding: 6px 14px;
      display: flex;
      align-items: center;
      gap: 6px;
      overflow-x: auto;
      scrollbar-width: none;
      -ms-overflow-style: none;
    }
    #section-nav::-webkit-scrollbar { display: none; }
    .snav-btn {
      background: #1e293b;
      border: 1px solid #334155;
      color: #94a3b8;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      padding: 5px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .snav-btn:hover { background: #293548; color: #e2e8f0; border-color: #475569; }
    .snav-btn.active { background: #1d4ed8; border-color: #3b82f6; color: #fff; font-weight: 700; }
    .snav-btn[data-cls="all"] { border-color: #475569; }"""

if OLD_CSS in content:
    content = content.replace(OLD_CSS, NEW_CSS, 1)
    changes += 1
    print('✓  Section nav CSS updated (pill buttons)')
elif NEW_CSS in content:
    print('–  CSS already updated')
else:
    print('✗  Section nav CSS not matched — will try to inject fresh')
    if '#section-nav {' not in content:
        content = content.replace('</style>', NEW_CSS + '\n  </style>', 1)
        changes += 1
        print('✓  Section nav CSS injected fresh')

# ── 2. Replace section nav HTML + JS (full replacement via regex) ─────────────
SECTIONS = [
    ('All',          'all'),
    ('Watchlist',    'Watch'),
    ('Top 20 US',    'Top20'),
    ('ASX',          'ASX'),
    ('Indices',      'Index'),
    ('Crypto',       'Crypto'),
    ('Commodities',  'Commodity'),
    ('Forex',        'Forex'),
    ('Hong Kong',    'HK'),
]

btn_html = '\n'.join(
    f'  <button class="snav-btn{" active" if cls == "all" else ""}" data-cls="{cls}">{label}</button>'
    for label, cls in SECTIONS
)

SECTION_LABELS = {
    'Watchlist': 'Watch', 'Top 20 US': 'Top20', 'ASX': 'ASX',
    'Global Indices': 'Index', 'Crypto': 'Crypto',
    'Commodities': 'Commodity', 'Forex': 'Forex', 'Hong Kong': 'HK'
}

NEW_NAV = f"""
<div id="section-nav">
{btn_html}
</div>

<script>
(function() {{
  var SECTION_MAP = {repr(SECTION_LABELS)};
  var activeFilter = 'all';

  // Tag every table row with its section after React renders
  function tagRows() {{
    var rows = document.querySelectorAll('tr');
    var current = 'all';
    var tagged = 0;
    rows.forEach(function(row) {{
      var text = row.textContent.trim();
      // Detect section header rows (short text matching a known section label)
      if (SECTION_MAP[text] !== undefined) {{
        current = SECTION_MAP[text];
        row.setAttribute('data-section', current);
        row.setAttribute('data-section-header', '1');
        tagged++;
      }} else if (row.querySelectorAll('td, th').length > 1) {{
        row.setAttribute('data-section', current);
      }}
    }});
    return tagged;
  }}

  function applyFilter(cls) {{
    activeFilter = cls;
    var rows = document.querySelectorAll('tr[data-section]');
    rows.forEach(function(row) {{
      var sec = row.getAttribute('data-section');
      var isHeader = row.getAttribute('data-section-header');
      if (cls === 'all') {{
        row.style.display = '';
      }} else if (sec === cls) {{
        row.style.display = '';
      }} else {{
        row.style.display = 'none';
      }}
    }});
    // Update button states
    document.querySelectorAll('.snav-btn').forEach(function(b) {{
      b.classList.toggle('active', b.getAttribute('data-cls') === cls);
    }});
  }}

  function wireButtons() {{
    var nav = document.getElementById('section-nav');
    if (!nav || nav._wired) return false;
    var btns = nav.querySelectorAll('.snav-btn');
    if (!btns.length) return false;
    btns.forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        applyFilter(btn.getAttribute('data-cls'));
      }});
    }});
    nav._wired = true;
    return true;
  }}

  // Insert nav after topbar
  function insertNav() {{
    var topbar = document.querySelector('.topbar');
    var nav = document.getElementById('section-nav');
    if (topbar && nav && !nav._inserted) {{
      topbar.parentNode.insertBefore(nav, topbar.nextSibling);
      nav._inserted = true;
    }}
  }}

  var attempts = 0;
  var iv = setInterval(function() {{
    attempts++;
    insertNav();
    var tagged = tagRows();
    if (wireButtons() && tagged >= 6) {{
      clearInterval(iv);
    }}
    if (attempts > 80) clearInterval(iv);
  }}, 100);
}})();
</script>"""

# Remove old nav block (div + script) and replace
old_nav_start = content.find('<div id="section-nav">')
old_script_end = content.find('</script>', content.find('wireSectionNav') if 'wireSectionNav' in content else old_nav_start)
if old_script_end != -1:
    old_script_end = old_script_end + len('</script>')

if old_nav_start != -1 and old_script_end != -1 and old_script_end > old_nav_start:
    content = content[:old_nav_start] + NEW_NAV.strip() + '\n' + content[old_script_end:]
    changes += 1
    print('✓  Section nav HTML + JS replaced with filter version')
elif 'id="section-nav"' not in content:
    content = content.replace('</body>', NEW_NAV + '\n</body>', 1)
    changes += 1
    print('✓  Section nav injected fresh')
else:
    print('✗  Could not locate old nav block to replace')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
