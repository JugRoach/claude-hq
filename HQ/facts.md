# HQ: facts

Each fact is dated; the newest wins.

## How HQ runs (2026-11-16)

- **HQ is a Claude Code session named "HQ Opus"** (Opus, Remote Control), working in `C:\Claude's Workspace`.
  - Claude Duet, in Matt's claude.ai chat, routes jobs to it.
  - Launch command: `claude --remote-control "HQ Opus" --model opus`, from PowerShell in `C:\Claude's Workspace`.
  - `claude.exe` is at `C:\Users\mattt\.local\bin\claude.exe`. Version 2.1.326 on 2026-11-16.
- **Auto-start at logon, hidden** (changed 2026-11-16 21:22): the Startup-folder shortcut `Claude HQ.lnk`, in `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`, runs `wscript.exe "C:\Claude's Workspace\HQ\tools\start-hq-hidden.vbs"`.
  - The script starts the launch command above in a **hidden console** (window style 0): no window, no taskbar button, no Alt+Tab entry. Matt manages HQ only through Claude Duet.
  - **Tested 2026-11-16** with a throwaway "HQ Hidden Test" session (Haiku) started the same way:
    - Its console was a classic conhost window with visible=False. Windows Terminal, the default terminal, did not take it over.
    - Remote Control registered (`[remote-bridge] Created session …`), and the session showed as "Remote Control · idle".
    - A message sent to it over Remote Control was handled, and it replied "hidden test OK".
    - The test session was then stopped.
  - **Backup** of the old visible-window shortcut: `HQ\backup\Claude HQ (visible window).lnk`. To go back, copy it over the Startup shortcut. Never put both in Startup, or two "HQ Opus" sessions would start.
  - Each boot starts a fresh HQ session that picks up from `start-here.md` files, per the company rules. Delete the Startup shortcut to turn auto-start off.
  - **No tray icon was added.**
  - **If HQ ever stops,** Claude Duet can't restart it, because it's a local process. Matt can sign out and back in, or double-click `HQ\tools\start-hq-hidden.vbs`.
  - To look at a hidden HQ screen while troubleshooting: `HQ\tools\hq-window.ps1 -List`, then `-Show -Hwnd 0x…`.
- **The window of the session started before this change** (Windows Terminal, started 18:46) was hidden on 2026-11-16 at 21:23 with `hq-window.ps1 -Hide`.
  - The session and its Remote Control connection kept running.
  - `hq-window.ps1 -ShowAllHidden` brings it back.
  - Windows Terminal is on default settings, so new Terminal windows open as new windows, not inside the hidden one.
- **Other Startup items on this PC:** `Day Board.lnk` (`.venv\Scripts\pythonw.exe app.py`) and `Endless War icon watcher.lnk`.
- **Permissions:** no permission rules are set (`settings.json` has none). Sessions here have run in auto mode.
- **Workers:** launched per `rules/routing.md` (`claude --bg`, worktree at the default location, `claude agents --json`).
- **GitHub:** private repo `JugRoach/claude-hq`.
  - Commits use the author "Claude Duet HQ", passed per commit; no git config is set.
  - Git Credential Manager holds the GitHub sign-in.
- **The Day Board's Claude Duet chat** is docked on its DAY BOARD tab (layout B, live since 2026-11-16 21:08).
