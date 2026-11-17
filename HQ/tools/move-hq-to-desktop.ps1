# Move the HQ conversation from the hidden terminal (CLI) into the Claude desktop app, safely:
# never two copies writing the same conversation, and a fallback if the desktop launch fails.
# Launched hidden by HQ itself (2026-11-16) at Matt's request. Log: HQ\log\2026-11-16-move-to-desktop.md
param([string]$SessionId = '14697bc8-a01e-4d1a-9d62-429ad953dba7', [int]$DelaySeconds = 90)

$ws = "C:\Claude's Workspace"
$log = "$ws\HQ\log\2026-11-16-move-to-desktop.md"
$claude = "C:\Users\mattt\.local\bin\claude.exe"
function Write-MoveLog($m) { Add-Content -Path $log -Encoding utf8 -Value ("- {0}  {1}" -f (Get-Date).ToString('HH:mm:ss'), $m) }

if (-not (Test-Path $log)) { Set-Content -Path $log -Encoding utf8 -Value "# Move HQ to the desktop app (2026-11-16)`n" }
Write-MoveLog "script started; waiting $DelaySeconds s so HQ's last reply finishes"
Start-Sleep -Seconds $DelaySeconds

# 1. stop the CLI HQ (the hidden terminal session), so only one copy holds the conversation
$cli = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'claude.exe' -and $_.CommandLine -match 'remote-control' -and $_.CommandLine -match 'HQ Opus' })
Write-MoveLog ("CLI HQ processes found: " + (($cli | ForEach-Object ProcessId) -join ', '))
$cli | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 4
$left = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'claude.exe' -and $_.CommandLine -match 'HQ Opus' }).Count
Write-MoveLog "CLI HQ stopped (left: $left)"

# 2. open the same conversation in the desktop app
Set-Location $ws
$out = & $claude --desktop --resume $SessionId 2>&1 | Out-String
$code = $LASTEXITCODE
Write-MoveLog ("claude --desktop --resume exit=$code output: " + (($out -replace '\s+', ' ').Trim()))

# 3. fallback: if the desktop launch failed, bring the hidden CLI HQ back (fresh session; it reads the handoff file)
if ($code -ne 0) {
  Start-Process wscript.exe -ArgumentList "`"$ws\HQ\tools\start-hq-hidden.vbs`""
  Write-MoveLog "desktop launch FAILED -> restarted the hidden CLI HQ (fresh session). Read HQ\work\handoff-2026-11-16-move-to-desktop.md"
} else {
  Write-MoveLog "desktop launch OK -> the HQ conversation should now be open in the Claude desktop app"
}
