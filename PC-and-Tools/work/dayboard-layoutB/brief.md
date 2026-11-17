# Brief: build Day Board layout B for real, staged for the next restart (2026-11-16)

You are the PC & Tools worker. Matt picked **layout B**, "Week Band and Chat Dock".

Read these first:
- `PC-and-Tools/work/dayboard-layouts/layout-b.png`, `layout-b.html` and `log/2026-11-16-dayboard-layouts.md` (the approved mockup and its palette)
- `PC-and-Tools/facts.md`

Build it for real. **Stage it; don't switch it on.** HQ installs your files, and Matt sees the change at Day Board's next restart.

## How Day Board works (HQ checked this read-only)

- **The app:** `C:\Users\mattt\Documents\DayBoard\app.py` (pywebview plus WinForms and WebView2). It reads `config.json` once at start; `reload.go` re-reads it but never re-creates windows. It creates three windows and embeds them as tabs in one window (`EMBED_TABS`):
  - **"Day Board":** loads `BOARD_URL`, a **claude.ai artifact**: `https://claude.ai/artifact/1eYpnzMrkWkP5L8LXkfyQr`.
  - **"Claude Duet · Day Board":** loads `https://claude.ai/messages` (`CLAUDE_TAB`).
  - **Discord.**
- **The board page's source** is `board\day-board.html`. It matches the published artifact byte for byte. Its capabilities:
  - `db`: collections `todos`, `tasks`, `inbox`, `workouts`, `focus`; docs `meta/theme`, `meta/feed`, `meta/focus`
  - `dictation`
  - `mcp`: Google Calendar `list_events`, Google Drive `download_file_content`
- **The page and app.py talk both ways:** app.py runs `evaluate_js` on the board window (see `BOARD_CFG_JS`, `push_board_cfg`, `board_post`), and the page sends `window.parent.postMessage` messages (`dayboard-nudge`, `dayboard-chime`, `dayboard-business-drive`, …) that app.py's `Api` handles.
- **Businesses** come from `DayBoard\business-status.json`, which app.py pushes to the page, plus its Drive mirror, which the page polls.
  - Allowed states: `Running`, `Earning`, `Not launched`, `Needs you`.
  - Real entries today: **Coppice** and **Game Art Kit**, both "Not launched". There's no One Night Press entry.

## What to build

### 1. The board page: `staged/board/day-board.html`, one page with two modes

- **Default mode must behave exactly like today's page.** That's what the running board, still on the old app.py, gets if the artifact reloads.
  - Keep every existing ID, message and function the old app.py relies on.
- **Layout B mode turns on only when the new app.py tells the page** (for example `LAYOUT: "B"` in the config it already pushes). In that mode:
  - **Week band across the top:**
    - today's day bar or timeline on the left, then the next 4 days as columns
    - all from the same Google Calendar call; widen its date range as needed
    - routines, pre-alerts, nudges, workout tally and motion all still work
  - **To-do strip** below the band, from db `todos`. It stays checkable, as today.
  - **Businesses grid** below that, from real data only:
    - One tile per entry in business-status.json (or the newer Drive copy). **No sample names, ever.**
    - **Always show a One Night Press tile.** With no entry for it, it shows **Not launched** with empty Deadlines / Accounts / Launch tasks / Needs you sections (a quiet "Nothing tracked yet").
    - Never invent items. Business side only, never any content.
    - **Optional fields:** if an entry has `deadlines`, `accounts`, `launch_tasks` or `needs`, render them in that tile. Design the shape, and document it in STAGING.md for HQ to add to the file's help text later.
    - **The label is "Needs you".** Never "Waiting on Matt".
    - Keep the approval box (`approval.waiting` / `what`).
  - **No Claude Duet chat inside the page.** The real chat is its own WebView that app.py docks to the right (see below). The page fills only the area to its left.
  - **Leave out** "Open with Claude" (`tasks`), the note box (`inbox`) and Focus.
  - **Style, from the mockup's palette:**
    - dark, low-chroma bases (CIELCh L ≤ 35, C ≤ 12), cream text, matte, every control obvious
    - **The warm accent `#B08D57` marks ONLY what needs Matt:** "Needs you" chips, the approval box, Needs-you items and the count of them.
    - Everything else that is brass today goes neutral cream in B mode: the Now line, the clock, the Next line, pre-alert text, the nudge glow, the glint and "workout due".

### 2. The app: `staged/app.py`, a modified copy of the current `app.py`

- **A new config key `CHAT_DOCK`** (for example `{"on": true, "width": 560}`).
- **When on:**
  - The tab bar shows only **DAY BOARD | DISCORD**.
  - On DAY BOARD, the board WebView takes the left part of the client area and the Claude Duet WebView sits docked on the right at `width`. Both resize with the window.
  - DISCORD shows Discord as today.
  - The page gets `LAYOUT: "B"`.
- **When off or missing:** behavior is exactly today's. This is the off switch.
- **Everything must keep working as now:**
  - F12 (record, auto-send, and typing into the focused chat box; it currently needs the chat window "in front")
  - F11 screenshot-send
  - backtick (Discord push-to-talk / hot mic)
  - audio mirror and mic HUD, chimes, nudges, pre-alerts
  - reply toasts and banners, approval cards, the unread mark
  - guard_loop, place / group_sync, BOARD_FIT, trigger files, restart
- **Trace every place that assumes a separate Claude tab** (`TAB_TITLES["claude"]`, `tabwin == "claude"`, `show_tab`, the unread mark, `banner_tab_mark`, the HUD's claude light, …). Make each behave sensibly when the chat is docked, for example:
  - no unread mark while it's visible
  - F12 from the Discord tab does what it does today, with the Day Board tab standing in for the Claude tab
- **List every behavior change** in STAGING.md.

### 3. The rest of the deliverables

- **`staged/config-additions.json`:** only the keys to add or change in config.json (CHAT_DOCK, and BOARD_FIT if the board area's base size changes). HQ merges it.
- **`STAGING.md`**, for HQ:
  - the exact install steps
  - what changes when
  - rollback steps (from `DayBoard-backup-2026-11-16-layoutB` and config `CHAT_DOCK.on=false`)
  - the business-status.json field shape
  - a short after-restart checklist for Matt (F12, backtick, toasts, Discord tab, resize)
  - everything you couldn't wire to real data

All of these go in your worktree under `PC-and-Tools/work/dayboard-layoutB/`.

## How to check your work (never touch the running board)

- **Compile:** `& "C:\Users\mattt\Documents\DayBoard\.venv\Scripts\python.exe" -m py_compile <staged app.py>`. Write any `__pycache__` only in your worktree.
- **Never import or run app.py.** A second copy would grab F12 and backtick system-wide.
- **Diff** staged/app.py against the current app.py, and staged/board/day-board.html against the current one. Re-read every changed function.
- **Test renders:**
  - Write a test-only harness, `test/harness.html`, that loads the staged page with a fake runtime: fake `claude`/`mcp`/`db` objects returning a few placeholder calendar events labeled "TEST", and today's real business-status.json content. Then send the config message.
  - Render **both** modes with headless Edge at a realistic board size (window 1920×1080, board area about 1360×1030):
    ```
    & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$env:TEMP\dayboard-layoutB-edge" --window-size=W,H --screenshot="<abs>.png" "file:///<abs>.html"
    ```
  - Look at the PNGs with Read. Check that default mode looks like today's board and B mode matches the approved mockup with real names.
  - Put the PNGs in `test/`.

## Hard limits

- **Work in a git worktree at the default location** (EnterWorktree, no custom path). Don't commit, push or merge; HQ copies your files out.
- **Write only inside your worktree.**
- **In `C:\Users\mattt\Documents\DayBoard\` you may only read.** Don't:
  - write, rename or delete anything there
  - create any `.go` trigger file
  - run the app
  - touch `webdata\`
- **Never touch the running Day Board.** Don't:
  - focus, minimize, move, restart or reload it
  - take desktop screenshots
  - use computer use
- **Don't publish or republish any artifact.** HQ does that.
- **Don't write files through the shell to get around the write guard,** and don't change any settings. If something blocks you, write down what and stop.
- **One Night Press:** business side only, never content.

## When done

1. Write the close-out to `PC-and-Tools/log/2026-11-16-dayboard-layoutB.md`:
   - what's staged
   - the diff summary
   - checks run and their results
   - what couldn't be wired to real data
   - risks
2. Rewrite `PC-and-Tools/start-here.md` (Current / Waiting on Matt / Next).
3. Stop.
