# Show or hide the window that hosts the HQ Opus session, without touching the session itself.
# Hiding a window never stops the processes in it, so Remote Control stays connected.
#
#   hq-window.ps1 -List          list Windows Terminal / console windows and whether they're visible
#   hq-window.ps1 -Hide -Hwnd 0x...   hide one window (no taskbar button, no Alt+Tab)
#   hq-window.ps1 -Show -Hwnd 0x...   show it again
#   hq-window.ps1 -ShowAllHidden      show every hidden Windows Terminal window (recovery)
#
# From 2026-11-16 HQ starts in a hidden console by itself (tools\start-hq-hidden.vbs), so this is only for
# windows started the old way, or for looking at HQ's screen while troubleshooting.
param([switch]$List, [switch]$Hide, [switch]$Show, [switch]$ShowAllHidden, [string]$Hwnd)

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class HQW {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
}
"@

function Get-TermWindows {
  $rows = New-Object System.Collections.ArrayList
  [HQW]::EnumWindows({ param($h, $l)
    $c = New-Object System.Text.StringBuilder 256; [HQW]::GetClassName($h, $c, 256) | Out-Null
    if ($c.ToString() -in 'CASCADIA_HOSTING_WINDOW_CLASS', 'ConsoleWindowClass') {
      $t = New-Object System.Text.StringBuilder 256; [HQW]::GetWindowText($h, $t, 256) | Out-Null
      $p = [uint32]0; [HQW]::GetWindowThreadProcessId($h, [ref]$p) | Out-Null
      [void]$rows.Add([pscustomobject]@{ hwnd = ('0x{0:X}' -f [int64]$h); class = $c.ToString(); pid = $p; visible = [HQW]::IsWindowVisible($h); title = $t.ToString() })
    }
    return $true }, [IntPtr]::Zero) | Out-Null
  $rows
}

if ($List -or -not ($Hide -or $Show -or $ShowAllHidden)) { Get-TermWindows | Format-Table -AutoSize | Out-String -Width 200; exit 0 }
if ($ShowAllHidden) {
  Get-TermWindows | Where-Object { $_.class -eq 'CASCADIA_HOSTING_WINDOW_CLASS' -and -not $_.visible } | ForEach-Object {
    [HQW]::ShowWindow([IntPtr][Convert]::ToInt64($_.hwnd, 16), 5) | Out-Null; "shown: $($_.hwnd) $($_.title)" }
  exit 0
}
if (-not $Hwnd) { "give -Hwnd 0x... (see -List)"; exit 1 }
$h = [IntPtr][Convert]::ToInt64($Hwnd, 16)
[HQW]::ShowWindow($h, $(if ($Hide) { 0 } else { 5 })) | Out-Null    # 0 = SW_HIDE, 5 = SW_SHOW
"{0}: {1} -> visible={2}" -f $(if ($Hide) { 'hide' } else { 'show' }), $Hwnd, [HQW]::IsWindowVisible($h)
