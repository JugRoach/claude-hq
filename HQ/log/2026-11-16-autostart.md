# Close-out: rollout step 7, HQ auto-start on boot (2026-11-16)

## Done

- **Created** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Claude HQ.lnk`:
  - target: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
  - arguments: `-NoExit -NoLogo -Command "& 'C:\Users\mattt\.local\bin\claude.exe' --remote-control 'HQ Opus' --model opus"`
  - start in: `C:\Claude's Workspace`
  - window: minimized
- **It mirrors how the current HQ session was started:** `claude.exe --remote-control "HQ Opus" --model opus` from PowerShell in this folder. Checked from the running process's command line.
- **The command parses cleanly** in PowerShell (0 errors).
- **Not test-launched:** a second "HQ Opus" next to the running one would give Claude Duet two sessions with the same name. The first real run is the next logon.

## Choices made (easy to change)

- **A fresh session each boot,** not `--continue`. Company rule: memory lives in files, and a fresh session carries on from `start-here.md`.
- **Minimized window**, so the desktop stays clear. It's a normal terminal window, so Matt can restore it from the taskbar to see a prompt.
- **No permission flags.** It runs in the account's default mode, the same as now. Nothing was bypassed and no settings were changed.
- **A Startup shortcut, not a scheduled task:** the same mechanism Day Board uses. Undo by deleting `Claude HQ.lnk`.

## Waiting on Matt

- After the next restart of the PC, check that "HQ Opus" shows up in Claude Duet's list of sessions, and send it a test job.
