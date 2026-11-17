# Move HQ to the desktop app (2026-11-16)

- 22:40:42  script started; waiting 90 s so HQ's last reply finishes
- 22:42:12  CLI HQ processes found: 24880
- 22:42:17  CLI HQ stopped (left: 0)
- 22:42:17  claude --desktop --resume exit=1 output: claude.exe : --desktop opens the Claude Desktop app and can't run non-interactively (`--print`, `--sdk-url`, `--init-only`, or redirected output). At C:\Claude's Workspace\HQ\tools\move-hq-to-desktop.ps1:25 char:8 + $out = & $claude --desktop --resume $SessionId 2>&1 | Out-String + ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ + CategoryInfo : NotSpecified: (--desktop opens...rected output).:String) [], RemoteException + FullyQualifiedErrorId : NativeCommandError
- 22:42:17  desktop launch FAILED -> restarted the hidden CLI HQ (fresh session). Read HQ\work\handoff-2026-11-16-move-to-desktop.md
