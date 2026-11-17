# Restart the Day Board safely: stop EVERY running copy, wait for its WebView2 helpers to let go of the
# sign-in profile, then start exactly one copy the way the Startup shortcut does. Never touches any other app,
# never focuses, moves or minimizes a window. Prints the foreground window before and after, so a check that
# Day Board didn't take focus from a game is in the output.
#
#   & "C:\Claude's Workspace\HQ\tools\restart-dayboard.ps1"          restart (stop all copies, start one)
#   & "C:\Claude's Workspace\HQ\tools\restart-dayboard.ps1" -Status  just list running copies, change nothing
#
# Allowed without a prompt by the HQ permission rule PowerShell(& "C:\Claude's Workspace\HQ\tools\*).
param([switch]$Status)

$d = "C:\Users\mattt\Documents\DayBoard"
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text;
public static class RDFG { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  public static string Now() { var sb = new StringBuilder(256); GetWindowText(GetForegroundWindow(), sb, 256); return sb.ToString(); } }
"@

function Get-DayBoardProcs { @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like "*DayBoard\app.py*" }) }
function Get-Helpers { @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'msedgewebview2.exe' -and $_.CommandLine -like "*DayBoard\webdata*" }) }

$procs = Get-DayBoardProcs
# each copy = a .venv launcher plus the Python 3.12 process it starts
"running: {0} process(es) = about {1} copy/copies: {2}" -f $procs.Count, [math]::Ceiling($procs.Count / 2), (($procs | ForEach-Object { "$($_.ProcessId)@$($_.CreationDate.ToString('HH:mm:ss'))" }) -join ', ')
if ($Status) { exit 0 }

"focus before: " + [RDFG]::Now()
$mark = (Get-Item "$d\dayboard.log").Length
$procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$t0 = Get-Date
do { Start-Sleep -Milliseconds 500; $wv = Get-Helpers } while ($wv.Count -gt 0 -and ((Get-Date) - $t0).TotalSeconds -lt 15)
if ($wv.Count) { "helpers still holding the profile after 15 s: $($wv.Count), stopping them"; $wv | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; Start-Sleep 2 }
"left: app=" + (Get-DayBoardProcs).Count + " helpers=" + (Get-Helpers).Count

Start-Process -FilePath "$d\.venv\Scripts\pythonw.exe" -ArgumentList "`"$d\app.py`"" -WorkingDirectory $d
"started at $((Get-Date).ToString('HH:mm:ss'))"

# wait for the startup line, up to 60 s
$t0 = Get-Date; $txt = ''
do {
  Start-Sleep 2
  $fs = [IO.File]::Open("$d\dayboard.log", 'Open', 'Read', 'ReadWrite'); $fs.Seek($mark, 'Begin') | Out-Null
  $txt = (New-Object IO.StreamReader($fs)).ReadToEnd(); $fs.Close()
} until ($txt -match 'started; ptt=' -or ((Get-Date) - $t0).TotalSeconds -gt 60)
$txt -split "`n" | Where-Object { $_ -match 'chat dock|started; ptt=|ERROR|Traceback' } | ForEach-Object { $_.Trim() }
"errors since start: " + ([regex]::Matches($txt, ' ERROR ')).Count
"running now: " + (Get-DayBoardProcs).Count + " process(es)"
"focus after: " + [RDFG]::Now()
