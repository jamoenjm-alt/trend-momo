# update-prices.ps1
# Fetches price history for all 34 tickers from Yahoo Finance
# and bakes them into regime-board.html's STATIC_PRICES block.
#
# HOW TO RUN:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\update-prices.ps1

$ErrorActionPreference = "Stop"
$htmlPath = Join-Path $PSScriptRoot "regime-board.html"

if (-not (Test-Path $htmlPath)) {
    Write-Host "ERROR: regime-board.html not found at $htmlPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Board ticker -> Yahoo Finance symbol
$TICKERS = [ordered]@{
    "AAPL"    = "AAPL"
    "MSFT"    = "MSFT"
    "TSLA"    = "TSLA"
    "NVDA"    = "NVDA"
    "ASML"    = "ASML"
    "IVV"     = "IVV"
    "PCT"     = "PCT"
    "SOUN"    = "SOUN"
    "AMZN"    = "AMZN"
    "GOOGL"   = "GOOGL"
    "META"    = "META"
    "BRK.B"   = "BRK-B"
    "AVGO"    = "AVGO"
    "JPM"     = "JPM"
    "LLY"     = "LLY"
    "V"       = "V"
    "UNH"     = "UNH"
    "ORCL"    = "ORCL"
    "MA"      = "MA"
    "XOM"     = "XOM"
    "NFLX"    = "NFLX"
    "COST"    = "COST"
    "WMT"     = "WMT"
    "HD"      = "HD"
    "BTC"     = "BTC-USD"
    "SOL"     = "SOL-USD"
    "XRP"     = "XRP-USD"
    "BNB"     = "BNB-USD"
    "ADA"     = "ADA-USD"
    "LINK"    = "LINK-USD"
    "TON"     = "TON-USD"
    "AVAX"    = "AVAX-USD"
    "SUI"     = "SUI-USD"
    "ETH"     = "ETH-USD"
    "GLD"     = "GLD"
    "SLV"     = "SLV"
    "PALL"    = "PALL"
    "PPLT"    = "PPLT"
    "MQG"     = "MQG.AX"
    "A2M"     = "A2M.AX"
    "CBA"     = "CBA.AX"
    "BHP"     = "BHP.AX"
    "WBC"     = "WBC.AX"
    "NAB"     = "NAB.AX"
    "WES"     = "WES.AX"
    "CSL"     = "CSL.AX"
    "WDS"     = "WDS.AX"
    "FMG"     = "FMG.AX"
    "ANZ"     = "ANZ.AX"
    "SPY"     = "SPY"
    "QQQ"     = "QQQ"
    "DIA"     = "DIA"
    "EWJ"     = "EWJ"
    "EWG"     = "EWG"
    "EWU"     = "EWU"
    "FXI"     = "FXI"
    "INDA"    = "INDA"
    "EEM"     = "EEM"
    "EURUSD"  = "EURUSD=X"
    "GBPUSD"  = "GBPUSD=X"
    "USDJPY"  = "USDJPY=X"
    "AUDUSD"  = "AUDUSD=X"
    "USDCAD"  = "USDCAD=X"
    "DXY"     = "DX-Y.NYB"
    "1211.HK" = "1211.HK"
}

$HISTORY_DAYS = 420
$now   = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$start = [DateTimeOffset]::UtcNow.AddDays(-$HISTORY_DAYS).ToUnixTimeSeconds()

$headers = @{
    "User-Agent"      = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    "Accept"          = "application/json"
    "Accept-Language" = "en-US,en;q=0.9"
}

function Fetch-Closes($yfSymbol) {
    $url = "https://query1.finance.yahoo.com/v8/finance/chart/$([Uri]::EscapeDataString($yfSymbol))?interval=1d&period1=$start&period2=$now&events=history"
    try {
        $resp   = Invoke-WebRequest -Uri $url -Headers $headers -UseBasicParsing -TimeoutSec 20
        $json   = $resp.Content | ConvertFrom-Json
        $result = $json.chart.result[0]
        if (-not $result) { return $null }

        $closes     = $result.indicators.quote[0].close
        $timestamps = $result.timestamp

        $pairs = @()
        for ($i = 0; $i -lt $timestamps.Count; $i++) {
            if ($null -ne $closes[$i]) {
                $pairs += [PSCustomObject]@{ ts = $timestamps[$i]; c = [math]::Round($closes[$i], 4) }
            }
        }
        $sorted = $pairs | Sort-Object ts
        return $sorted | ForEach-Object { $_.c }
    } catch {
        return $null
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Trend Momo - Price Update" -ForegroundColor Cyan
Write-Host "  Fetching $($TICKERS.Count) tickers from Yahoo Finance" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Read existing HTML
$html = Get-Content $htmlPath -Raw -Encoding UTF8
$pricesDict = @{}

$existingMatch = [regex]::Match($html, 'window\.STATIC_PRICES\s*=\s*(\{.*?\});', [System.Text.RegularExpressions.RegexOptions]::Singleline)
if ($existingMatch.Success) {
    try {
        $existing = $existingMatch.Groups[1].Value | ConvertFrom-Json
        $existing.PSObject.Properties | ForEach-Object { $pricesDict[$_.Name] = $_.Value }
        Write-Host "Loaded $($pricesDict.Count) existing ticker(s) from HTML" -ForegroundColor DarkGray
    } catch { }
}

$ok  = 0
$err = 0

foreach ($board in $TICKERS.Keys) {
    $yfSym = $TICKERS[$board]
    $label = "$board".PadRight(10) + "($yfSym)"
    Write-Host "  -> $($label.PadRight(26))" -NoNewline

    $closes = Fetch-Closes $yfSym

    if ($closes -and $closes.Count -ge 21) {
        $pricesDict[$board] = $closes
        $ok++
        Write-Host "OK  $($closes.Count) closes   last=$($closes[-1])" -ForegroundColor Green
    } else {
        $err++
        if ($pricesDict.ContainsKey($board)) {
            Write-Host "FAIL - keeping previous data" -ForegroundColor Yellow
        } else {
            Write-Host "FAIL - no data" -ForegroundColor Red
        }
    }
    Start-Sleep -Milliseconds 350
}

$startMarker = "// @@STATIC_PRICES_START@@"
$endMarker   = "// @@STATIC_PRICES_END@@"
$si = $html.IndexOf($startMarker)
$ei = $html.IndexOf($endMarker)

if ($si -lt 0 -or $ei -lt 0) {
    Write-Host "ERROR: STATIC_PRICES markers not found in HTML - file may be corrupted." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$before = $html.Substring(0, $si)
$after  = $html.Substring($ei + $endMarker.Length)
$ts     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "  Writing to temp file first (safe write)..." -ForegroundColor DarkGray

# Write to a temp file first - if anything goes wrong, the original is untouched
$tempPath  = $htmlPath + ".tmp"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer    = New-Object System.IO.StreamWriter($tempPath, $false, $utf8NoBom)
try {
    $writer.Write($before)
    $writer.WriteLine("// @@STATIC_PRICES_START@@")
    $writer.WriteLine("// All prices last updated $ts by update-prices.ps1")
    $writer.Write("window.STATIC_PRICES = {")
    $first = $true
    foreach ($k in $pricesDict.Keys) {
        $vals = ($pricesDict[$k] | ForEach-Object { $_.ToString([System.Globalization.CultureInfo]::InvariantCulture) }) -join ","
        $entry = '"' + $k + '":[' + $vals + ']'
        if (-not $first) { $writer.Write(",") }
        $writer.Write($entry)
        $first = $false
    }
    $writer.WriteLine("};")
    $writer.Write("// @@STATIC_PRICES_END@@")
    $writer.Write($after)
} finally {
    $writer.Close()
}

# Verify temp file has both markers before replacing the real file
$verify   = Get-Content $tempPath -Raw -Encoding UTF8
$hasStart = $verify.Contains("// @@STATIC_PRICES_START@@")
$hasEnd   = $verify.Contains("// @@STATIC_PRICES_END@@")
$diskSize = (Get-Item $tempPath).Length

if (-not $hasStart -or -not $hasEnd) {
    Remove-Item $tempPath -Force
    Write-Host "ERROR: Temp file missing markers - original file preserved, nothing changed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Safe to replace
Move-Item -Path $tempPath -Destination $htmlPath -Force
Write-Host "  File integrity check: PASSED - $diskSize bytes, both markers present" -ForegroundColor DarkGray

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
$doneTime = Get-Date -Format "HH:mm:ss"
Write-Host "  Done at $doneTime  ($ok ok, $err failed)" -ForegroundColor Cyan
Write-Host "  regime-board.html updated - open it in your browser" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "  Press Enter to close"
