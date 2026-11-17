# PC & Tools: start here

_Rewritten 2026-11-17 by Screen Desk for HQ (model split, dispatcher check); the Day Board notes below are from 11/16 21:35 and still current._

## Current

- **New model split (Matt 11/17 4:55 PM)** is in `rules/routing.md`: Fable for taste/judgment/design/writing in Matt's voice/hard calls/SIG; Opus for deep analysis, planning, code, config design; Sonnet for routine research, drafting, summaries, verifier checks; Haiku for bulk/mechanical work. Effort rises for money, deletes, drivers/BIOS, security, public output. Duet departments are managers and send real work to subagents. Every result names the model that made the key call. API first, priority SIG, then businesses, then everything else.
- **Moving from Duet to PC API jobs** (run through `HQ\tools\dispatch-job.ps1`): weekly PC & Tools research, weekly health check, verifier passes on PC recommendations, file reorg analysis, Day Board/wallpaper builds (Fable for visual calls), mic tuning analysis. **Photo date fix + iCloud uploads are parked until after 11/22.**
- **Dispatcher verified on all four models (11/17):** haiku, sonnet, opus and fable each answered with its exact id, exit 0 (logs `HQ\jobs\*model-check-*.log`). Fable through the dispatcher worked on its first try. Cost note: even a one-line job loads the workspace rules, about $0.01 on Haiku to about $0.76 on Fable, so tiny Fable jobs are not free; run jobs from a lean folder when they don't need the rules.
- **Day Board chat-collapse bug fixed 11/17** (Dock None/Fill squeeze; see `log/2026-11-17-dayboard-dock-fix.md`). Backup: `DayBoard\backup-2026-11-17-dock-fix\`.

- **The Day Board runs layout B with the business card.** It was last restarted at 21:30, and one copy is running.
  - **Layout B** (live since 21:08):
    - DAY BOARD | DISCORD tabs, with the Claude Duet chat docked on the right.
    - Week band, to-do strip, businesses.
    - Off switch: `CHAT_DOCK.on: false`, then restart.
  - **Business card** (live since 21:30):
    - One big card cycling Coppice → Game Art Kit → One Night Press every 20 s.
    - It holds while the mouse is over it, and the dots are clickable.
    - Off switch: `BIZ_CARD.on: false`, then restart (brings back the tiles).
  - **Checked live:**
    - The layout, Discord tab, banners and resize (21:08).
    - The card cycling and F12 into the docked chat, used by Matt at 21:31 (21:30).
- **Board page:** artifact `https://claude.ai/artifact/1eYpnzMrkWkP5L8LXkfyQr`, version 30. Its source is `board\day-board.html`, the same as `work/dayboard-bizcard/staged/board/day-board.html`.
- **Backups:**
  - `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-layoutB`, from before layout B.
  - `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-bizcard`, from before the card.
  - Full rollback: copy `app.py`, `board\day-board.html` and `config.json` back from one, republish the artifact from its page, then restart.
- **Details:**
  - `work/dayboard-layoutB/STAGING.md` and `work/dayboard-bizcard/STAGING.md`: behavior, rollback, the business-status.json field shape.
  - `log/`: the close-outs for each step.

## Waiting on Matt

- **Backtick in a Discord call:** it's hooked, but not yet tried live.
- **One Night Press** has no entry in business-status.json, so its slide shows Not launched with "Nothing tracked yet". Real business-side items have to be added to the file.

## Next

- **If anything is off,** use the matching off switch, then send the log lines (`chat dock …`, `tab shown …`) to PC & Tools.
- **Later:** add the optional business fields (shape in `work/dayboard-layoutB/STAGING.md`) to business-status.json and its `help` text.
- **Watch for duplicate copies.** Starting Day Board from a shortcut while it's already running makes a second copy that fights over F12 and backtick. This happened at 21:18. A single-instance guard in `app.py` would prevent it. Not done; it needs Matt's OK.

## 2026-11-17 routing plan (Screen Desk)
- Lean dispatcher lane built (`dispatch-job.ps1 -Lean`, `-Lane plan|api`, log columns, explicit effort defaults). Dispatcher bills the weekly plan login. Details: `log/2026-11-17-routing-plan.md`. API lane waits on HQ naming the key.
