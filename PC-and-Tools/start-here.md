# PC & Tools: start here

_Rewritten 2026-11-16 by HQ, after installing Day Board layout B._

## Current

- **Day Board layout B is LIVE (restarted 2026-11-16 21:08).** One copy is running.
  - Layout, Discord tab, banners and resize passed.
  - F12 and backtick are hooked; Matt still needs to try each one live.
  - Results: `log/2026-11-16-dayboard-restart.md`.
- **How it was installed** (before the restart):
  - **Board page:** artifact `https://claude.ai/artifact/1eYpnzMrkWkP5L8LXkfyQr` was republished as version 29 from `work/dayboard-layoutB/staged/board/day-board.html`.
    - It's one page with two modes. It stays in the usual layout until the app sends `layout: "B"`, which the old running app never does.
    - Capabilities are unchanged.
  - **Day Board folder:**
    - `board\day-board.html` and `app.py` are replaced with the staged copies (hashes checked; app.py compiles).
    - `config.json` gained `CHAT_DOCK {"on": true, "width": 560}` and `CHAT_DOCK_HELP`. Nothing else in it changed.
  - **Backup taken before anything changed:** `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-layoutB`.
  - **Details:**
    - `work/dayboard-layoutB/STAGING.md`: behavior changes, rollback, the business-status.json field shape, the after-restart checklist
    - `log/2026-11-16-dayboard-layoutB.md`: the worker's close-out
    - `log/2026-11-16-dayboard-layoutB-routing.md`: score and tier
- **Off switch:** set `CHAT_DOCK.on` to `false` in config.json, then restart.
- **Full rollback:**
  - Copy `app.py`, `board\day-board.html` and `config.json` back from the backup.
  - Republish the artifact from the backup page.
  - Restart.

## Waiting on Matt

- **Try F12 and backtick live:** F12 into the docked chat, and backtick in a Discord call.
- **Clear the TEST banners:** three of them show the next time DISCORD is open; click "Clear all".
- **One Night Press** has no entry in business-status.json, so its tile shows Not launched with "Nothing tracked yet". Real business-side items have to be added to the file.
- **Optional:** OK to delete the worker's throwaway Edge profile `%TEMP%\dayboard-layoutB-edge`.

## Next

- **After the restart,** if anything is off: use the off switch, then send the log lines (`chat dock …`, `tab shown …`) to PC & Tools.
- **Later:** add the optional business fields (shape in STAGING.md) to business-status.json and its `help` text.
