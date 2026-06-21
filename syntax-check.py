"""syntax-check.py — finds node.exe and checks JS syntax"""
import re, subprocess, os, glob

# Find node.exe on Windows
node = None
candidates = [
    r'C:\Program Files\nodejs\node.exe',
    r'C:\Program Files (x86)\nodejs\node.exe',
    os.path.expandvars(r'%APPDATA%\npm\node.exe'),
    os.path.expandvars(r'%LOCALAPPDATA%\Programs\nodejs\node.exe'),
]
# Also check PATH
for p in candidates:
    if os.path.exists(p):
        node = p
        break
if not node:
    import shutil
    node = shutil.which('node') or shutil.which('node.exe')

if not node:
    # Try nvm / volta paths
    for pattern in [
        os.path.expandvars(r'%APPDATA%\nvm\*\node.exe'),
        os.path.expandvars(r'%LOCALAPPDATA%\Volta\tools\image\node\*\node.exe'),
        r'C:\Users\*\AppData\Roaming\nvm\*\node.exe',
    ]:
        found = glob.glob(pattern)
        if found:
            node = found[0]
            break

if not node:
    print('✗ node.exe not found. Install Node.js from https://nodejs.org')
    exit(1)

print(f'Using node: {node}')

with open('regime-board.html', encoding='utf-8') as f:
    src = f.read()

# Extract ALL script blocks (module may span differently)
# Try multiline match without DOTALL restriction on outer tags
blocks = re.findall(r'<script\b[^>]*>([\s\S]*?)</script>', src)
print(f'Found {len(blocks)} script block(s)')

module_js = None
for b in blocks:
    if 'import' in b and 'react' in b.lower():
        module_js = b
        break

if not module_js:
    # fallback: grab everything between first <script and last </script>
    s = src.find('<script')
    e = src.rfind('</script>')
    if s != -1 and e != -1:
        inner = src[src.find('>',s)+1:e]
        module_js = inner
        print('Used fallback script extraction')

if not module_js:
    print('✗ Could not extract script block')
    exit(1)

print(f'Script block: {len(module_js):,} chars')

# Strip ES module imports (node --check in CJS mode doesn't like them)
js = re.sub(r"^\s*import\s+.*?from\s+'[^']+';?\s*$", '', module_js, flags=re.MULTILINE)

stub = ('const h=()=>{},useState=v=>[v,()=>{}],useEffect=()=>{},'
        'useCallback=f=>f,useRef=()=>({current:null}),Fragment=null,'
        'createRoot=()=>({render:()=>{}});\n')

tmp = os.path.join(os.environ.get('TEMP', 'C:/Temp'), 'check_regime.js')
with open(tmp, 'w', encoding='utf-8') as f:
    f.write(stub + js)

result = subprocess.run([node, '--check', tmp], capture_output=True, text=True)
if result.returncode == 0:
    print('✓ JS syntax OK')
else:
    print('✗ Syntax error:')
    print(result.stderr)
