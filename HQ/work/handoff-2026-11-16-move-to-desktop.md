# HQ handoff: moving the HQ session into the Claude desktop app (2026-11-16 ~22:45)

If you're HQ and your context is thin, start here.

## What's happening

- Matt asked to move this HQ conversation into the Claude desktop app, so HQ itself can use computer use.
  - Session id: `14697bc8-a01e-4d1a-9d62-429ad953dba7`, folder `C:\Claude's Workspace`.
- The move runs as `HQ\tools\move-hq-to-desktop.ps1`, launched hidden by HQ. It:
  1. waits 90 s
  2. stops the terminal (CLI) HQ process, `claude.exe --remote-control "HQ Opus"`
  3. runs `claude --desktop --resume 14697bc8-a01e-4d1a-9d62-429ad953dba7`
  4. logs everything to `HQ\log\2026-11-16-move-to-desktop.md`
  - **If the launch fails,** it restarts the hidden CLI HQ with `HQ\tools\start-hq-hidden.vbs`. That's a fresh session; read this file and `HQ\start-here.md`.

## First thing to do in the desktop app

1. **Check you have computer-use tools:** ToolSearch "computer" with max_results 60. Expect `mcp__computer-use__*`.
2. **Run ONE harmless test:** request access if asked, then take ONE screenshot. Don't click, type or touch any game window. If WoW is in front, the screenshot alone is fine.
3. **Log the result** in `HQ\log\2026-11-16-computer-use-test.md`: tools present or not, the screenshot taken or the error. Then update `HQ\work\computer-use-setup.md` and `HQ\queue\README.md` ("Who does the clicking") to match.
4. **If it works,** HQ can run the screen-queue jobs itself, under `HQ\queue\README.md`.

## Where everything lives (all in files)

- **Rules:**
  - root `CLAUDE.md`: departments, the act/stop rules, screen jobs, purchases, privacy
  - `rules\routing.md`
  - `HQ\queue\README.md`: the screen-queue rules
- **Screen queue:** `HQ\queue\screen-queue.md`
  - Job 1, the desktop-app project pass: queued; Duet gave it to a desktop chat at about 22:25 and it hasn't started.
  - Job 2, the WoW UI rebuild: expected.
- **HQ state:**
  - `HQ\start-here.md`, `HQ\facts.md`, `HQ\log\*`
  - each department's `start-here.md` (Businesses, Finances, Taste-Dossier, Games-and-Hobbies, PC-and-Tools, Daily-Life, Career-and-Transition)
- **Open work:**
  - `HQ\work\life-organization-plan.md` (local only): the PC/Drive map, 6 questions for Matt, delete candidates D1–D10, nothing moved yet
  - `HQ\work\computer-use-setup.md`
  - `HQ\work\desktop-projects-pass.md`
- **Day Board:**
  - page v31 (artifact `https://claude.ai/artifact/1eYpnzMrkWkP5L8LXkfyQr`)
  - layout B, business card and watch lines live
  - `HQ\tools\restart-dayboard.ps1`, backups `Documents\DayBoard-backup-2026-11-16-*`
- **To verify:** the Coppice Gmail check at 1:23 / 7:23 PM (`Businesses\start-here.md`).
- **Permissions:** user `settings.json` (auto mode, allow and ask lists; see `HQ\facts.md`).
- **Memory:** `C:\Users\mattt\.claude\projects\C--Claude-s-Workspace\memory\`.
  - A desktop-app session in the same folder should use the same project key; if not, copy the folder.
- **Autostart:** `Claude HQ.lnk` still starts the hidden CLI HQ at logon (a fresh session).
  - **Decide after the test:** keep that, or retire it in favor of the desktop app.
  - **Never run both at once.**
