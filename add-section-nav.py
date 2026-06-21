"""
add-section-nav.py — Adds a sticky section jump bar below the topbar
Buttons: Watchlist | Top 20 US | ASX | Indices | Crypto | Commodities | Forex | Hong Kong
Run: python add-section-nav.py  then: .\\git-push.bat
"""
import shutil, sys

path = 'regime-board.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# ── 1. CSS for section nav bar ────────────────────────────────────────────────
NAV_CSS = """
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

if '#section-nav {' not in content:
    content = content.replace('</style>', NAV_CSS + '\n  </style>', 1)
    changes += 1
    print('✓  Section nav CSS added')
else:
    print('–  Section nav CSS already present')

# ── 2. HTML + JS for the section nav ─────────────────────────────────────────
SECTIONS = [
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
    f'  <button class="snav-btn" data-cls="{cls}">{label}</button>'
    for label, cls in SECTIONS
)

SECTION_NAV_HTML = f"""
<div id="section-nav">
{btn_html}
</div>

<script>
(function() {{
  // Wait for React to render the section rows, then wire up scroll buttons
  function wireSectionNav() {{
    var nav = document.getElementById('section-nav');
    if (!nav) return false;
    var btns = nav.querySelectorAll('.snav-btn');
    if (!btns.length) return false;

    // Find section header rows by looking for rows that span the full table
    // Section headers are rendered as <tr> with a <td colspan> containing the section label
    // We'll tag them by data-cls when found
    function findAndTagSections() {{
      // Look for th/td elements that contain only the section label text
      var allCells = document.querySelectorAll('td[colspan], th[colspan]');
      var tagged = 0;
      allCells.forEach(function(cell) {{
        var text = cell.textContent.trim();
        {chr(10).join(f"        if (text === '{label}') {{ cell.closest('tr').id = 'section-{cls}'; tagged++; }}" for label, cls in SECTIONS)}
      }});
      return tagged;
    }}

    // Also try finding by text in any table row header
    function findSectionsByText() {{
      var rows = document.querySelectorAll('tr');
      var tagged = 0;
      rows.forEach(function(row) {{
        var text = row.textContent.trim();
        {chr(10).join(f"        if (text === '{label}' && !row.id) {{ row.id = 'section-{cls}'; tagged++; }}" for label, cls in SECTIONS)}
      }});
      return tagged;
    }}

    var found = findAndTagSections() + findSectionsByText();

    btns.forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        var cls = btn.getAttribute('data-cls');
        var target = document.getElementById('section-' + cls);
        if (target) {{
          // Account for sticky nav height
          var navH = nav.offsetHeight;
          var topbarH = document.querySelector('.topbar') ? document.querySelector('.topbar').offsetHeight : 0;
          var offset = topbarH + navH + 4;
          var y = target.getBoundingClientRect().top + window.scrollY - offset;
          window.scrollTo({{ top: y, behavior: 'smooth' }});
          // Highlight active
          btns.forEach(function(b) {{ b.classList.remove('active'); }});
          btn.classList.add('active');
        }}
      }});
    }});

    // Highlight active section on scroll
    window.addEventListener('scroll', function() {{
      var navH = nav.offsetHeight;
      var topbarH = document.querySelector('.topbar') ? document.querySelector('.topbar').offsetHeight : 0;
      var offset = topbarH + navH + 20;
      var active = null;
      {chr(10).join(f"      var el_{cls} = document.getElementById('section-{cls}'); if (el_{cls} && el_{cls}.getBoundingClientRect().top <= offset) active = '{cls}';" for _, cls in SECTIONS)}
      btns.forEach(function(b) {{
        b.classList.toggle('active', b.getAttribute('data-cls') === active);
      }});
    }}, {{ passive: true }});

    return found > 0;
  }}

  // Insert nav right after the topbar
  function insertNav() {{
    var topbar = document.querySelector('.topbar');
    if (!topbar) return false;
    var nav = document.getElementById('section-nav');
    if (nav && !nav._inserted) {{
      topbar.parentNode.insertBefore(nav, topbar.nextSibling);
      nav._inserted = true;
    }}
    return true;
  }}

  var attempts = 0;
  var iv = setInterval(function() {{
    attempts++;
    insertNav();
    if (wireSectionNav() || attempts > 60) clearInterval(iv);
  }}, 100);
}})();
</script>"""

if 'id="section-nav"' not in content:
    content = content.replace('</body>', SECTION_NAV_HTML + '\n</body>', 1)
    changes += 1
    print('✓  Section nav HTML + JS injected')
else:
    print('–  Section nav already present')

# ── Result ────────────────────────────────────────────────────────────────────
if changes == 0:
    print('\nNothing changed.')
    sys.exit(0)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
shutil.copy2(path, 'index.html')
print(f'\n✓  {changes} fix(es) applied. index.html synced. Run: .\\git-push.bat')
