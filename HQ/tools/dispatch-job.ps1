<#
  HQ job dispatcher (Screen Desk, 11/17). Runs ONE headless Claude Code job (claude -p), hidden, and logs it.

  powershell -File dispatch-job.ps1 -Model claude-haiku-5-5 -Effort low -Cwd "C:\Claude's Workspace" -Name my-job -Prompt "..."
  (or -PromptFile path)

  Rules (see HQ\CLAUDE.md, "Dispatcher"):
   - Model and effort are both required. If either is missing the job is NOT run: it is logged as refused and the script exits 2 (ask HQ).
   - The job runs on exactly that model (no fallback model is passed). The model that actually answered is read from the result and
     written to the log; a mismatch is flagged.
   - Hidden: no window. Headless: stdin = the prompt. The process is closed when it ends; on timeout the whole tree is stopped.
   - One log per job: HQ\jobs\<yyyyMMdd-HHmmss>-<name>.log. Parallel headless jobs are fine (each its own log).
   - Screen jobs never go through here (headless Claude has no computer use on Windows); they go through the HQ\queue screen queue.
   - Default permission mode "auto"; override with -PermissionMode (never bypassPermissions unless HQ says so in the tag).
   Exit codes: 0 ok, 2 refused (missing/invalid tag), 3 job failed, 4 timed out, 5 wrong model answered.
#>
param(
  [string]$Model,
  [string]$Effort,
  [string]$Cwd = "C:\Claude's Workspace",
  [string]$Name = "job",
  [string]$Prompt,
  [string]$PromptFile,
  [int]$TimeoutMin = 30,
  [string]$PermissionMode = "auto",
  [switch]$Screen,
  [switch]$HeavyGpu,          # heavy GPU work: waits for the game rule and the gpu lock on the resources board
  [string]$GpuHeldBy,         # the caller already holds the gpu lock under this owner name (don't take it again)
  [int]$WaitMin = 120,        # how long to wait for a lock / a game to close before giving up (exit 6)
  [switch]$Lean,              # lean lane: run from HQ\lean, no connectors, no user/project settings, plugins or slash commands, only -Tools
  [string]$Tools = "Read,Write,Edit,Bash,Glob,Grep",   # built-in tools a -Lean job gets (use the smallest set the tag needs)
  [ValidateSet('plan','api')][string]$Lane = 'plan',   # plan = weekly plan login. api stays disabled until HQ names the key.
  [string]$Dept = "HQ",       # log column: department
  [string]$TaskType = "other" # log column: task type from the routing rules file
)
$ErrorActionPreference = "Stop"
$root = "C:\Claude's Workspace"
$jobs = Join-Path $root "HQ\jobs"
# Protected folders (SIG): the log lives inside that folder and carries no prompt and no result, only metadata.
$protected = $false
try { if ($Cwd -and ((Resolve-Path $Cwd).Path -like "C:\SIG*")) { $protected = $true; $jobs = "C:\SIG\jobs" } } catch { }
$lock = Join-Path $root "HQ\tools\resource-lock.ps1"
New-Item -ItemType Directory -Force $jobs | Out-Null
# Jobs in the private area (C:\hq-private) get the company rules via a generated parent CLAUDE.md; refresh it first.
try { if ($Cwd -and ((Resolve-Path $Cwd).Path -like "C:\hq-private*")) { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "HQ\tools\sync-private-rules.ps1") | Out-Null } } catch { }
$slug = ($Name -replace '[^A-Za-z0-9_-]', '-')
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$log = Join-Path $jobs "$stamp-$slug.log"
function W($t) { Add-Content -Path $log -Value $t -Encoding UTF8 }

$efforts = 'low', 'medium', 'high', 'xhigh', 'max'
# Effort is always set explicitly (Sonnet would default to high). If the tag has a model but no effort, use the tier default; log it.
$effortDefaulted = $false
if ($Model -and -not $Effort) {
  $tier = $(if ($Model -like '*haiku*') { 'low' } elseif ($Model -like '*sonnet*') { 'medium' } elseif ($Model -like '*opus*') { 'medium' } elseif ($Model -like '*fable*') { 'high' } else { $null })
  if ($tier) { $Effort = $tier; $effortDefaulted = $true }
}
if ($Lane -eq 'api') { W "REFUSED $(Get-Date -Format s): the api lane is disabled until HQ names which API key it uses."; Write-Output "REFUSED: api lane disabled (see $log)"; exit 2 }
if ($Screen) { W "REFUSED $(Get-Date -Format s): screen jobs don't run headless; use the HQ\queue screen queue."; Write-Output "REFUSED: screen job (see $log)"; exit 2 }
if (-not $Model -or -not $Effort) { W "REFUSED $(Get-Date -Format s): job '$Name' has no model/effort tag (model='$Model', effort='$Effort'). Ask HQ for the tag."; Write-Output "REFUSED: missing model or effort tag. Ask HQ. ($log)"; exit 2 }
if ($efforts -notcontains $Effort) { W "REFUSED $(Get-Date -Format s): effort '$Effort' is not one of $($efforts -join ', ')."; Write-Output "REFUSED: bad effort '$Effort' ($log)"; exit 2 }
if ($PromptFile) { $Prompt = Get-Content -Raw -Path $PromptFile }
if (-not $Prompt) { W "REFUSED $(Get-Date -Format s): no prompt."; Write-Output "REFUSED: no prompt ($log)"; exit 2 }
if (-not (Test-Path $Cwd)) { W "REFUSED $(Get-Date -Format s): working folder '$Cwd' not found."; Write-Output "REFUSED: folder not found ($log)"; exit 2 }

W "JOB $Name"
W "started   : $(Get-Date -Format s)"
W "model     : $Model (requested)"
W "effort    : $Effort$(if ($effortDefaulted) { ' (tier default)' })"
W "lane      : $Lane$(if ($Lean) { ' / lean' } else { ' / full' })"
W "dept      : $Dept"
W "task type : $TaskType"
W "folder    : $Cwd"
W "permission: $PermissionMode"
W "timeout   : $TimeoutMin min"
if ($protected) { W "prompt    : (not logged: protected folder)" } else { W "prompt    : $(($Prompt -replace '\s+', ' ').Substring(0, [Math]::Min(300, ($Prompt -replace '\s+', ' ').Length)))" }
W "----"

# ---- resources board (HQ\resources.json): heavy GPU jobs wait for the game rule and the gpu lock ----
$tookGpu = $false
function Release-Gpu { if ($script:tookGpu) { & powershell -NoProfile -File $lock release -Name gpu -Owner "dispatch-$slug" | Out-Null; $script:tookGpu = $false } }
if ($HeavyGpu) {
  $deadline = (Get-Date).AddMinutes($WaitMin)
  $board = Get-Content -Raw "C:\Claude's Workspace\HQ\resources.json" | ConvertFrom-Json
  while ($true) {
    $games = @(& powershell -NoProfile -File $lock games)
    $gameOpen = ($LASTEXITCODE -eq 1)
    $board = Get-Content -Raw "C:\Claude's Workspace\HQ\resources.json" | ConvertFrom-Json
    if (-not $gameOpen -or $board.mattSaidGo) { break }
    W "waiting $(Get-Date -Format s): a game is running ($($games -join ', ')); heavy GPU jobs wait unless Matt said go."
    if ((Get-Date) -ge $deadline) { W "NOT RUN: a game stayed open for $WaitMin min."; Write-Output "NOT RUN: game running (see $log)"; exit 6 }
    Start-Sleep 30
  }
  if (-not $GpuHeldBy) {
    $r = & powershell -NoProfile -File $lock take -Name gpu -Owner "dispatch-$slug" -Label "dispatched job" -Eta "$TimeoutMin min max" -OwnerPid $PID -WaitMin $WaitMin
    if ($LASTEXITCODE -ne 0) { W "NOT RUN: gpu lock still held ($r)"; Write-Output "NOT RUN: gpu lock held ($log)"; exit 6 }
    $tookGpu = $true
    W "gpu lock : taken"
  } else { W "gpu lock : held by caller ($GpuHeldBy)" }
}
$tmp = Join-Path $env:TEMP "dispatch-$stamp-$slug"
$inF = "$tmp.in"; $outF = "$tmp.out"; $errF = "$tmp.err"
Set-Content -Path $inF -Value $Prompt -Encoding UTF8
$leanDir = Join-Path $root "HQ\lean"
if ($Lean) { $Cwd = $leanDir }
$claude = "C:\Users\mattt\.local\bin\claude.exe"
$argList = @('-p', '--model', $Model, '--effort', $Effort, '--permission-mode', $PermissionMode, '--output-format', 'json', '--no-session-persistence', '--disallowedTools', '"Bash(git push:*)"', '"Bash(git * push:*)"')   # no pushes from dispatched jobs, ever
if ($Lean) {
  # Lean lane: no connectors, no user/project settings (so no parent CLAUDE.md or memory), no plugins/skills, only the named tools.
  $argList += @('--strict-mcp-config', '--mcp-config', ('"' + (Join-Path $leanDir 'empty-mcp.json') + '"'), '--setting-sources', '""', '--disable-slash-commands', '--tools', "`"$Tools`"", '--append-system-prompt-file', ('"' + (Join-Path $leanDir 'CLAUDE.md') + '"'))
}
$p = Start-Process -FilePath $claude -ArgumentList $argList -WorkingDirectory $Cwd -WindowStyle Hidden `
  -RedirectStandardInput $inF -RedirectStandardOutput $outF -RedirectStandardError $errF -PassThru
$done = $p.WaitForExit($TimeoutMin * 60 * 1000)
if (-not $done) {
  & taskkill /PID $p.Id /T /F | Out-Null
  W "TIMED OUT after $TimeoutMin min; process tree stopped."
  Release-Gpu
  W "finished  : $(Get-Date -Format s)"
  Write-Output "TIMEOUT ($log)"; exit 4
}
$p.WaitForExit(); $p.Refresh()
$code = $p.ExitCode   # can come back blank with redirected output; resolved below from the JSON result
$raw = "" + $(if (Test-Path $outF) { Get-Content -Raw $outF })
$err = "" + $(if (Test-Path $errF) { Get-Content -Raw $errF })
$result = $raw; $used = @(); $cost = $null; $j = $null; $tin = $null; $tout = $null; $tcache = $null; $tcw = $null
try {
  $j = $raw | ConvertFrom-Json
  $result = $j.result
  if ($j.modelUsage) { $used = @($j.modelUsage.PSObject.Properties.Name) }
  $cost = $j.total_cost_usd
  if ($j.usage) { $tin = $j.usage.input_tokens; $tout = $j.usage.output_tokens; $tcache = $j.usage.cache_read_input_tokens; $tcw = $j.usage.cache_creation_input_tokens }
} catch { }
if ($null -eq $code -or "$code" -eq "") { $code = $(if ($j -and ($j.is_error -eq $false)) { 0 } else { 3 }) }
W "exit code : $code"
W "model used: $($used -join ', ')"
W "tokens    : input $tin, output $tout, cached-read $tcache, cache-write $tcw"
if ($null -ne $cost) { W "cost (usd): $cost" }
if ($err.Trim()) { W "stderr    : $($err.Trim())" }
W "---- result ----"
if ($protected) { W "(not logged: protected folder; the result went to the caller only)" } else { W $result }
W "----"
W "finished  : $(Get-Date -Format s)"
W "SUMMARY   : dept=$Dept | type=$TaskType | model=$($used -join '+') | effort=$Effort | lane=$Lane$(if ($Lean) { '/lean' }) | in=$tin out=$tout cached=$tcache | cost=$cost | $(if ($code -eq 0) { 'pass' } else { 'fail' })"
Remove-Item $inF, $outF, $errF -ErrorAction SilentlyContinue
Release-Gpu

$bad = $false
if ($used.Count -gt 0 -and (@($used | ? { $_ -notlike "$Model*" }).Count -gt 0)) { $bad = $true; W "WRONG MODEL: asked for $Model, used $($used -join ', ')." }
Write-Output $result
if ($code -ne 0) { Write-Output "(job failed, exit $code; see $log)"; exit 3 }
if ($bad) { exit 5 }
exit 0
