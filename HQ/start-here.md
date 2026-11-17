# HQ: start here

_Handoff written 2026-11-17 ~5:15 PM by the outgoing Remote control (Screen Desk) session, which is ~908k of 1M context and is being replaced. The fresh session reads this first and carries on from "Next"._

## Next

- **Routing plan steps 2-8 are done** (see `PC-and-Tools\log6-11-17-routing-plan.md`). Waiting on HQ: **push of master** (merge + routing fold-in are committed locally; pre-push hook first) and **which API key the `-Lane api` lane uses** (refused until then).
- Then: row 16 Day Board usage meter; Duet-to-API job moves in `rules/routing.md`.
- Hard rules: no new API keys, no billing changes, nothing paid, sent or deleted; protected data stays local; workers never push, only HQ.
- This session is the replacement Screen Desk (Remote Control on). The old session stops taking jobs.

## Who you are

- You are the **Screen Desk / dispatcher** session: the desktop-app Code session titled "Remote control", working folder `C:\Claude's Workspace`, Remote Control on. It is the only session with computer-use tools. HQ Opus (hidden CLI, started at logon) and SIG (hidden CLI, `C:\SIG`) are separate sessions.
- **Screen rules:** one screen job at a time, via `HQ\queue\` (read `queue/README.md`, keep `queue/screen-queue.md` current; rows run to 16+). Never click in, type into or close a game window. Brave and Chrome are **read-only** for computer use (no clicks or typing): launch pages from the shell and let Matt click. Terminals can't be typed into. Request every app a job needs in one access request at the start. Keep the Claude app on the small bottom monitor, uncovered.
- **Dispatcher:** `HQ\tools\dispatch-job.ps1 -Model -Effort -Cwd -Name -Prompt [-HeavyGpu]` runs headless `claude -p` jobs, logs to `HQ\jobs\` (SIG jobs log inside `C:\SIG\jobs`, content-free), refuses an untagged job, denies `git push`. Verified on haiku/sonnet/opus/fable 11/17.
- **Resources board** `HQ\resources.json` + `HQ\tools\resource-lock.ps1` (locks `gpu`, `screen`; game rule: heavy GPU jobs wait while a game runs unless `mattSaidGo`).

## What's running now (11/17 evening)

- **Day Board** (restarted ~3:26 PM with the dock fix), full screen on the small bottom monitor DISPLAY2, pinned to all desktops, with **`HQ Screen Layout`** (Task Scheduler, hidden controller): Ctrl+Alt+B = Day Board, Ctrl+Alt+C = toggle Day Board/Claude, tiny DAY BOARD corner button, CLAUDE button on the Day Board tab bar.
- **SIG**: hidden CLI session in `C:\SIG` (Remote Control), currently still on **Fable high**; `start-sig-hidden.vbs` now says **Opus medium**, applied at its next launch.
- **HQ Opus**: hidden CLI, started at logon.
- Open windows: Brave (two windows, restored pinned tabs + a clean New Tab), Chrome (Claude extension sign-in page for Matt), iCloud for Windows (sign-in screen), File Explorer on `C:\hq-private\photos\sorted`, WoW at times (Matt's).

## Waiting on Matt (nothing here is mine to do)

- **iCloud:** sign in himself. No Photos sync, no uploads until the Takeout photo dates are fixed into a new folder and Matt checks counts (parked until after 11/22 per routing).
- **Chrome Claude extension:** sign in (Add to Chrome and pin were his clicks). Ads privacy toggles are his.
- **Bitwarden/Brave:** extension installed (verified real); sign-in, "Offer to save passwords" off, and the saved-password count are his. Brave: unpin or close the 13 pinned tabs (all saved in bookmark folder "Saved tabs 11-17"); startup setting click if it reopens pages.
- **itch.io (Wholetone):** Matt fills the form himself (an account on that email may already exist: he went to "forgot password"). Gmail watch for the verification/reset email is mine, sender and time only.
- **Photo sort:** he reviews `C:\hq-private\photos\sorted` (esp. `Review - delete` 456 and `Private` 128) and decides about deleting; the Takeout zips (5.85 GB) are kept until he says.
- **powercfg:** run `HQ\tools\powercfg-requests.bat` as administrator once to list what holds the display awake (WoW is the likely one). Display timeout is 15 min on AC, sleep Never.
- **Windows default browser** shows Edge (not Brave); his call in Settings.
- **WoW UI:** review found 1 pass / 4 fail (`HQ\wow-ui-review\2026-11-17\`); a mockup is next, nothing installed or changed until his yes. HealDeal job 2 is partial (steps 6-8 open).

## Open jobs / queued

- **Row 16 (queued): Day Board usage meter** (two bars: regular usage vs 85%, API spend vs 95%, refreshed ~15 min), asked by Matt 11/17, for SIG (PC & Tools). Not started. Note: two rows share number 16; the model-split one is done.
- **Photo date fix + iCloud uploads:** parked until after 11/22.
- **SIG restart onto Opus medium:** Matt hasn't said when; a restart drops its Remote Control link briefly. SIG's `send_message` alert path is unverified.
- **Moving from Duet to PC API jobs** (see `rules/routing.md`): weekly PC & Tools research, weekly health check, verifier passes, file reorg analysis, Day Board/wallpaper builds, mic tuning analysis.
- Dispatcher cost note: one-line jobs load the workspace rules (about $0.01 Haiku up to $0.76 Fable); the lean lane (step 4) fixes that.

## Facts worth keeping

- **Company folder** `C:\Claude's Workspace` (git: private `JugRoach/claude-hq`; one commit was waiting to push; lots of uncommitted work today). **Private material is in `C:\hq-private\`** (Finances, Taste-Dossier, One-Night-Press, life-org data, takeout, photos, backups). SIG stays in `C:\SIG` with `C:\SIG\PROTECTED` (only the Design/Taste Dossier project may read it).
- **GitHub lockdown:** no worker pushes; `git push` is denied for departments, SIG and dispatched jobs; pre-push hook refuses private paths and secrets (tested on a temp local repo). Already-pushed history names SIG/PROTECTED/"taste" in rules and Day Board copies (names only); not rewritten.
- **Day Board:** backups `DayBoard\backup-2026-11-17-claude-button\` and `backup-2026-11-17-dock-fix\`. Bug fix logs in `PC-and-Tools\log\`.
- **Logs:** one per job in `HQ\log\2026-11-17-*.md` (consoles, dispatcher, sig-session, resources-sig-protected, github-lockdown, oled-protection, takeout-*, photo-sort, brave-setup, chrome-setup, itch-signup, icloud-install, bitwarden-prep, job3, job4).
- **Standing rules from Matt (11/16-17):** WoW launches only through Battle.net, one instance; the Claude app stays on the small bottom monitor and uncovered; requests for apps in one access request; long jobs (2+ hours, Matt off the PC) run 4-7 AM ET; protected tastes never named outside the Taste Dossier; nothing sent, posted, paid or deleted without his yes.
- **HQ tools:** `restart-dayboard.ps1`, `check-summary.ps1`, `hq-window.ps1`, `dispatch-job.ps1`, `resource-lock.ps1`, `sync-private-rules.ps1` (refresh `C:\hq-private\CLAUDE.md` after editing the company CLAUDE.md or rules), `pre-push-hook.sh`/`install-pre-push.ps1`, `screen-layout\`, `photos\`, `brave\`, `chrome\`.
