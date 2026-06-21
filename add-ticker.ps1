# add-ticker.ps1
# Adds a new ticker to regime-board.html and update-prices.ps1
#
# HOW TO RUN:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\add-ticker.ps1

$ErrorActionPreference = "Stop"
$htmlPath = Join-Path $PSScriptRoot "regime-board.html"
$ps1Path  = Join-Path $PSScriptRoot "update-prices.ps1"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Trend Momo - Add Ticker" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── Prompt for details ────────────────────────────────────────
$ticker = (Read-Host "Ticker symbol (e.g. CBA, SHOP, BABA)").Trim().ToUpper()
if (-not $ticker) { Write-Host "No ticker entered. Exiting." -ForegroundColor Red; exit 1 }

$name = (Read-Host "Company name (e.g. Commonwealth Bank)").Trim()
if (-not $name) { Write-Host "No name entered. Exiting." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  Sections:" -ForegroundColor Gray
Write-Host "    1. Watch      (your personal watchlist)" -ForegroundColor Gray
Write-Host "    2. Top20      (US large caps)" -ForegroundColor Gray
Write-Host "    3. Crypto     (BTC / ETH etc)" -ForegroundColor Gray
Write-Host "    4. Commodity  (GLD / SLV / PALL etc)" -ForegroundColor Gray
Write-Host "    5. ASX        (Australian stocks)" -ForegroundColor Gray
Write-Host "    6. HK         (Hong Kong stocks)" -ForegroundColor Gray
Write-Host ""
$secNum = (Read-Host "Section number (1-6)").Trim()
$sectionMap = @{ "1"="Watch"; "2"="Top20"; "3"="Crypto"; "4"="Commodity"; "5"="ASX"; "6"="HK" }
if (-not $sectionMap.ContainsKey($secNum)) { Write-Host "Invalid section. Exiting." -ForegroundColor Red; exit 1 }
$cls = $sectionMap[$secNum]

# Yahoo Finance symbol default
$defaultYF = switch ($cls) {
    "ASX"    { $ticker + ".AX" }
    "HK"     { $ticker + ".HK" }
    "Crypto" { $ticker + "-USD" }
    default  { $ticker }
}
$yfInput = (Read-Host "Yahoo Finance symbol (press Enter for '$defaultYF')").Trim()
$yfSym = if ($yfInput) { $yfInput } else { $defaultYF }

# Stooq symbol (used as browser fallback)
$defaultStooq = switch ($cls) {
    "ASX"    { $ticker.ToLower() + ".au" }
    "HK"     { $ticker.ToLower() + ".hk" }
    default  { $ticker.ToLower() + ".us" }
}
$stooqInput = (Read-Host "Stooq symbol (press Enter for '$defaultStooq', or 'none')").Trim()
$stooqSym = if ($stooqInput -eq "none") { "" } elseif ($stooqInput) { $stooqInput } else { $defaultStooq }

Write-Host ""
Write-Host "  Adding: $ticker | $name | $cls | Yahoo=$yfSym" -ForegroundColor Yellow
$confirm = (Read-Host "Confirm? (y/n)").Trim().ToLower()
if ($confirm -ne "y") { Write-Host "Cancelled." -ForegroundColor Gray; exit 0 }

# ── Read files ────────────────────────────────────────────────
$html = Get-Content $htmlPath -Raw -Encoding UTF8
$ps1  = Get-Content $ps1Path  -Raw -Encoding UTF8

# Check ticker doesn't already exist
if ($html -match """$ticker""") {
    Write-Host "WARNING: $ticker already appears in the HTML. Check for duplicates." -ForegroundColor Yellow
}

# ── 1. WATCHLIST ──────────────────────────────────────────────
# Insert after the LAST entry of the matching section
$watchEntry = "  { ticker: '$ticker', name: '$name', cls: '$cls' },"

# Find insertion point: last line matching cls: '$cls' in WATCHLIST
$clsPattern = "cls: '$cls'"
$lastIdx = -1
$searchFrom = 0
while ($true) {
    $idx = $html.IndexOf($clsPattern, $searchFrom)
    if ($idx -lt 0) { break }
    $lastIdx = $idx
    $searchFrom = $idx + 1
}

if ($lastIdx -lt 0) {
    # Section doesn't exist yet — insert before closing ];
    $html = $html -replace "(\r?\n\];\s*\r?\n\s*const SECTIONS)", "`n$watchEntry`n];`n`nconst SECTIONS"
} else {
    # Find end of that line and insert after it
    $lineEnd = $html.IndexOf("`n", $lastIdx)
    if ($lineEnd -lt 0) { $lineEnd = $html.Length }
    $html = $html.Substring(0, $lineEnd + 1) + $watchEntry + "`n" + $html.Substring($lineEnd + 1)
}

# ── 2. BALANCE_SHEET ─────────────────────────────────────────
$bsEntry = "  '$ticker':     { score: null, tip: 'Balance sheet not yet scored — update manually' },"
# Insert before closing }; of BALANCE_SHEET
$html = $html -replace "(const PE_RATIOS)", "$bsEntry`n`$1"

# ── 3. PE_RATIOS ─────────────────────────────────────────────
$peEntry = "  '$ticker':     { pe: null, tip: 'P/E not yet set — update manually' },"
# Insert before closing }; of PE_RATIOS — find "const STOOQ_MAP" or next const
$html = $html -replace "(const STOOQ_MAP)", "$peEntry`n`$1"

# ── 4. STOOQ_MAP ─────────────────────────────────────────────
if ($stooqSym) {
    # Append before closing }; of STOOQ_MAP
    $html = $html -replace "(};`r?`n\s*const sym = STOOQ_MAP)", "  '$ticker': '$stooqSym',`n`$1"
}

# ── 5. update-prices.ps1 ─────────────────────────────────────
# Insert before "1211.HK" line (last entry)
$ps1 = $ps1 -replace '("1211\.HK"\s*=\s*"1211\.HK")', "    `"$ticker`"     = `"$yfSym`"`n    `$1"

# ── Write files ───────────────────────────────────────────────
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$htmlBytes = $utf8NoBom.GetBytes($html)
[System.IO.File]::WriteAllBytes($htmlPath, $htmlBytes)

$ps1Bytes = $utf8NoBom.GetBytes($ps1)
[System.IO.File]::WriteAllBytes($ps1Path, $ps1Bytes)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Done! $ticker added to:" -ForegroundColor Green
Write-Host "    - WATCHLIST ($cls section)" -ForegroundColor Green
Write-Host "    - BALANCE_SHEET (score: N/A - set manually)" -ForegroundColor Green
Write-Host "    - PE_RATIOS (P/E: N/A - set manually)" -ForegroundColor Green
if ($stooqSym) {
Write-Host "    - STOOQ_MAP ($stooqSym)" -ForegroundColor Green
}
Write-Host "    - update-prices.ps1 ($yfSym)" -ForegroundColor Green
Write-Host ""
Write-Host "  Next: run update-prices.ps1 to fetch $ticker price history." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to close"
