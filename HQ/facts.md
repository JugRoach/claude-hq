# HQ: facts

Each fact is dated; the newest wins.

## How HQ runs (2026-11-16)

- **HQ is a Claude Code session named "HQ Opus"** (Opus, Remote Control), working in `C:\Claude's Workspace`.
  - Claude Duet, in Matt's claude.ai chat, routes jobs to it.
  - Launch command: `claude --remote-control "HQ Opus" --model opus`, from PowerShell in `C:\Claude's Workspace`.
  - `claude.exe` is at `C:\Users\mattt\.local\bin\claude.exe`. Version 2.1.326 on 2026-11-16.
- **Auto-start at logon** (set up 2026-11-16): the Startup-folder shortcut `Claude HQ.lnk`, in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`.
  - It opens a minimized PowerShell window in `C:\Claude's Workspace` running the launch command above.
  - Each boot starts a fresh HQ session that picks up from `start-here.md` files, per the company rules.
  - Delete the shortcut to turn auto-start off.
- **Other Startup items on this PC:** `Day Board.lnk` (`.venv\Scripts\pythonw.exe app.py`) and `Endless War icon watcher.lnk`.
- **Permissions:** no permission rules are set (`settings.json` has none). Sessions here have run in auto mode.
- **Workers:** launched per `rules/routing.md` (`claude --bg`, worktree at the default location, `claude agents --json`).
- **GitHub:** private repo `JugRoach/claude-hq`.
  - Commits use the author "Claude Duet HQ", passed per commit; no git config is set.
  - Git Credential Manager holds the GitHub sign-in.
- **The Day Board's Claude Duet chat** is docked on its DAY BOARD tab (layout B, live since 2026-11-16 21:08).
