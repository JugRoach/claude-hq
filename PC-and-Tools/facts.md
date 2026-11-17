# PC & Tools: facts

Each fact is dated; the newest wins. Facts come from a read-only look at the files unless marked as Matt's words.

## Day Board (2026-11-16)

- **Location:** `C:\Users\mattt\Documents\DayBoard`.
- **How it's built:** a Python app (`app.py`, using the pywebview library) that shows its pages in an Edge WebView2 window. It runs from the `.venv` folder there.
  - It also uses keyboard, sounddevice, and Whisper speech-to-text (the `whisper\` folder, about 2.2 GB).
- **Window:** one window with three tabs, DAY BOARD | DISCORD | CLAUDE DUET (`EMBED_TABS: true`). It starts maximized (`BOARD_START_MAXIMIZED: true`).
  - The Claude Duet tab is the claude.ai messages page; F12 sends speech into it from any tab.
  - Discord has its own tab, and Ctrl+Alt+D toggles it. The backtick key is Discord push-to-talk / hot mic.
- **Board page:** `board\day-board.html`, about 72 KB, last edited 2026-11-16 12:46.
  - It scales to the window (`BOARD_FIT`) and reflows to two columns, or one when narrow.
- **Current theme** (`config.json` → THEME):

  | Role | Color |
  |---|---|
  | page | `#131314` |
  | panel | `#1A1A1C` |
  | hairline | `#2A2A2D` |
  | text | `#E8E2D6` |
  | secondary | `#A39E94` |
  | muted | `#6B6760` |
  | accent | `#B08D57` |

- **Business tracker:** `business-status.json`. There are 2 entries, and both are currently "Not launched".
  - Allowed states: Running, Needs you, Earning, Not launched.
  - `approval.waiting` plus `what` flags an approval waiting on Matt.
  - The newer of the local file and its Drive copy wins.
- **Backup naming:**
  - Matt's convention for backups beside the folder is `C:\Users\mattt\Documents\DayBoard-backup-YYYY-MM-DD-<name>`. There are 21 of these; `-11-16-sticky` is about 3 GB.
  - Older backups inside the folder use `backup-YYYY-MM-DD-<name>` (17 of them).
  - Single-file backups use `<file>.bak-YYYY-MM-DD-<name>` or `<file>.before-YYYY-MM-DD-<name>.html`.
- **Running copies:** on 2026-11-16 at about 19:10 there were **four** `pythonw app.py` processes: two from `.venv` and two from the system Python 3.12. This may mean duplicate instances. It's unconfirmed and nothing has been changed.
- **Files to leave alone:**
  - `config.json`: it holds the hotkeys and the Discord and Drive settings.
  - `webdata\` (about 800 MB): the WebView profile, including sign-ins.
  - `dayboard.log`.
  - Never minimize or restart the running board without Matt's yes.

## Matt's words

- **2026-11-16, redesign:**
  - Put the calendar and the Claude Duet chat on ONE page. Discord stays its own tab.
  - Add a One Night Press tile covering the business side only (deadlines, accounts, launch tasks, what's waiting on Matt), never content.
  - Each business shows running, earning, not launched, or waiting on Matt.
- **2026-11-16, "Quiet Villain" style:**
  - dark, low-chroma base colors (L ≤ 35, C ≤ 12)
  - cream, not white
  - one small warm accent where the eye lands
  - matte finish
  - nothing that looks like generic AI design
  - every control obvious
