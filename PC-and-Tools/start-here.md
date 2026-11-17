# PC & Tools: start here

_Rewritten 2026-11-16 21:35 by HQ, after the business card went live._

## Current

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
