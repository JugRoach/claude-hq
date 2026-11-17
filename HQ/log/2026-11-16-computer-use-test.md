# Computer-use test after the move to the desktop app (2026-11-16)

**Result: no test was possible. HQ is still the hidden terminal session, not the desktop app.**

## Where HQ is running
- The move failed (see `2026-11-16-move-to-desktop.md`). At 22:42:17, `claude --desktop --resume` exited with code 1: "--desktop opens the Claude Desktop app and can't run non-interactively (`--print`, `--sdk-url`, `--init-only`, or redirected output)." The script captured its output (`2>&1 | Out-String`), so it couldn't work from a hidden script.
- The fallback then restarted the hidden CLI HQ. This session confirms that:
  - `CLAUDE_CODE_ENTRYPOINT=cli`
  - process `claude.exe --remote-control "HQ Opus" --model opus` (PID 33960)
  - it's a fresh session (b84d3e4e-…), not a resume of 14697bc8-…
- Matt cancelled the leftover "Save as" dialog himself.

## Tools check
- ToolSearch "computer" (max 60) and "screenshot computer-use remote-devices" found **no `mcp__computer-use__*` or `mcp__remote-devices__computer_*` tools**. That matches the docs: no computer use in the CLI on Windows.
- **Screenshot: not taken.** There was no tool for it. Nothing on screen was touched.

## What this means
- Nothing changes: Claude Duet (device jugroach-dt) still does the clicking. HQ writes jobs and sends "SCREEN JOB READY".
- **To try again:** Matt runs `claude --desktop --continue` (or `--resume 14697bc8-a01e-4d1a-9d62-429ad953dba7`) in a normal, visible terminal from `C:\Claude's Workspace`, after first stopping the hidden HQ so they never run at the same time. Or he opens a Code session on this folder in the desktop app. A script can't do it.
- The autostart (`Claude HQ.lnk`, the hidden CLI) stays as it is.
