# schedule-daily-update.ps1
# Creates a Windows Task Scheduler entry to run update-prices.ps1 every day at 7:00 AM.
# Run this ONCE to set it up. After that, prices update automatically.
#
# HOW TO RUN:
#   Right-click -> "Run as Administrator"
#   OR from an elevated PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\schedule-daily-update.ps1

$taskName   = "TrendMomo-DailyPriceUpdate"
$scriptPath = Join-Path $PSScriptRoot "update-prices.ps1"
$runAt      = "07:00"

if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: update-prices.ps1 not found at $scriptPath" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Remove existing task if present
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task." -ForegroundColor DarkGray
}

$action  = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

$trigger = New-ScheduledTaskTrigger -Daily -At $runAt

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily price update for Trend Momo dashboard" `
    -RunLevel Highest | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Scheduled task created!" -ForegroundColor Green
Write-Host "  Name : $taskName" -ForegroundColor Green
Write-Host "  Runs : Every day at $runAt" -ForegroundColor Green
Write-Host "  File : $scriptPath" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To change the time, edit the task in:" -ForegroundColor Gray
Write-Host "  Task Scheduler -> Task Scheduler Library -> $taskName" -ForegroundColor Gray
Write-Host ""
Write-Host "To remove it, run:" -ForegroundColor Gray
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to close"
