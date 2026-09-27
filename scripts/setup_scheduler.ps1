# Windows Task Scheduler setup script
# Run as Administrator in PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts/setup_scheduler.ps1

param(
    [string]$TaskName = "NewsAssistant-Daily",
    [string]$RunTime = "07:30"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkingDir = Split-Path -Parent $ScriptDir
$PythonExe = (Get-Command python).Source

$WrapperPath = Join-Path $ScriptDir "run_daily.ps1"
$WrapperContent = @"
`$ErrorActionPreference = "Stop"
Set-Location "$WorkingDir"
& "$PythonExe" "$WorkingDir\scripts\run_daily.py"
"@
Set-Content -Path $WrapperPath -Value $WrapperContent -Encoding UTF8
Write-Host "Wrapper created: $WrapperPath"

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WrapperPath`"" `
    -WorkingDirectory $WorkingDir

$Trigger = New-ScheduledTaskTrigger -Daily -At $RunTime

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Daily international news scraping and push" `
    -Force

Write-Host "Task '$TaskName' registered. Runs daily at $RunTime." -ForegroundColor Green
Write-Host "Test manually: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
Write-Host "Unregister: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:$false" -ForegroundColor Yellow
