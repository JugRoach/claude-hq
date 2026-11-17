' Claude Duet HQ launcher (2026-11-16).
' Starts the "HQ Opus" Claude Code session with Remote Control in C:\Claude's Workspace, in a HIDDEN console:
' no window, no taskbar button, no Alt+Tab entry. Matt manages HQ from Claude Duet over Remote Control.
' Run at logon by the Startup shortcut "Claude HQ.lnk" (target: wscript.exe "<this file>").
' Window style 0 = hidden. It also keeps Windows Terminal from taking over (tested 2026-11-16: conhost, not visible).
' The old visible launcher is kept at HQ\backup\Claude HQ (visible window).lnk.
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Claude's Workspace"
sh.Run """C:\Users\mattt\.local\bin\claude.exe"" --remote-control ""HQ Opus"" --model opus", 0, False
