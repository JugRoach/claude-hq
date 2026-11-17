# Close-out: Day Board layout B, built and staged (2026-11-16)

Brief: `work/dayboard-layoutB/brief.md`. Routing: `log/2026-11-16-dayboard-layoutB-routing.md` (Opus, xhigh).

Staged only:

- Nothing in `C:\Users\mattt\Documents\DayBoard\` was written, renamed or deleted; it was only read.
- No `.go` trigger files, no app.py run or import, no artifact published.
- The running board and the screen weren't touched.
- Nothing committed or pushed.

## What's staged

Worktree: `C:\Claude's Workspace\.claude\worktrees\toasty-wibbling-diffie\`, branch `worktree-toasty-wibbling-diffie`. Paths below are under `PC-and-Tools\work\dayboard-layoutB\`.

| File | What |
|---|---|
| `staged/board/day-board.html` | The board page, one page with two modes. The default mode is today's page; layout B turns on only for `layout: "B"` in the config message. |
| `staged/app.py` | app.py plus `CHAT_DOCK`: the Claude Duet view docked right of the board on the DAY BOARD tab, tabs DAY BOARD \| DISCORD. |
| `staged/config-additions.json` | `CHAT_DOCK {"on": true, "width": 560}` and `CHAT_DOCK_HELP`. BOARD_FIT unchanged. |
| `STAGING.md` | Install order, what changes when, rollback, every behavior change, the business field shape, Matt's after-restart checklist, gaps and risks, hashes. |
| `test/harness.html` + 7 PNGs | Test-only harness and renders. |

Also written: this close-out, and a rewritten `start-here.md`.

## Diff summary

**app.py:** +181 lines, 20 changed.

- **New:**
  - `dock_cfg`, `dock_on`, `chat_in_view`, `ui_post`
  - `dock_build`: the DAY BOARD tab becomes a panel with the board view filling on the left, a 1 px hairline, and the chat docked right. It puts everything back if anything fails.
  - `dock_layout`: width in logical px, scaled for DPI, at most half the panel.
- **Changed:**
  - `embed_tabs` calls `dock_build` when on.
  - `show_tab` maps "claude" to "today" when docked, re-applies the width, and focuses the chat.
  - `paint`: hides the CLAUDE DUET label, cream underline when docked, nudge toast placed after the last visible tab.
  - `build_nudge_ui`: a twin unread dot on the DAY BOARD label, and the tick picks one of the two.
  - `unread_mark`, `banner_gone` and `reply_toast` use `chat_in_view()`.
  - `banner_anchor` uses the DAY BOARD label when docked.
  - `board_cfg` adds `layout`.
  - `reload_cfg` re-applies the width.
  - The menu label.
  - Comments and docstring.
- **Dock off:** every path reduces to today's code. Each changed function was re-read for that.

**day-board.html:** +305 lines, 6 changed.

- **The 6 changed lines:**
  - `input()` (wider range in B only)
  - `tickHeader` (+B clock)
  - `renderTimeline` (always the list view in B)
  - the to-do snapshot (+count)
  - `showView` (B hides the default views)
  - the config listener (+`setLayout`)
  - Each is gated on `LAYOUT==='B'`, or is a no-op when B is off.
- **Added:** `renderCal` calls `renderWeek` and `renderBiz` calls `renderBizB`; both return at once unless B is on.
- **New:** the B CSS (scoped to `body.layout-b`), the hidden `#bView` markup, and the B script block:
  - `setLayout` with park/unpark of five live nodes
  - `renderWeek`, `bAgenda`, `renderBizB`, `bTodoCount`, `tickB`
- **Kept:** every existing ID, message and function.

## Checks run

| Check | Result |
|---|---|
| `py_compile` (DayBoard venv; cache in `test/pycache`) | Pass |
| pyflakes, staged vs live | Same single warning in both (unused `Region` import); no undefined names |
| Diffs re-read, function by function | Done (summary above; full list in STAGING.md) |
| Harness, 7 renders with headless Edge | 0 script errors in every render |
| Default page (old app, no layout key) vs live page | Max 7/255 difference (random grain), 0 pixels over 12 |
| New app with the dock off (`layout: ""`) vs live | Same |
| B, then back to default ("flip") vs live | Same: B moves everything back |
| Calendar range | Default asks 11-15 to 11-18, as live does; B asks 11-15 to 11-21. The TEST event on 11-21 doesn't show. |
| B vs approved mockup | Same structure and palette with real names (Coppice, Game Art Kit, One Night Press). No brass when nothing needs Matt. |
| B with TEST fields | Accent only on Needs you chips, items and labels, "Needs you: 3", and the approval box |
| B at 1440×900 (zoom 0.8) | Holds together; long titles wrap |

Fixes made after looking at the renders:

- B's today list follows the now line, starting on a whole row. The default list keeps its old scroll position all day, so in B the now line would have drifted out of view.
- Long titles wrap in B.
- The launch-checklist row stays on one line.

The harness's own sizing was also fixed.

## What couldn't be wired to real data

- **One Night Press** has no entry in business-status.json. Its tile shows Not launched, with "Nothing tracked yet" in Deadlines, Accounts, Launch tasks and Needs you.
- **Coppice and Game Art Kit** have no optional fields yet. The field shape is in STAGING.md, ready for the file's help text.
- **No Review/Open buttons on Needs-you items**, because there's nothing to wire them to.
- **Future-day columns** show calendar events only.
- **The docked chat and the WinForms docking** were checked by reading the code only (app.py can't run here).

## Risks

- **Duplicate app.py processes.** facts.md recorded four running `app.py` processes. Restarting with duplicates could leave two copies fighting over F12 and backtick. Check before the restart.
- **First re-parenting of the board's own WebView2** into a panel. A caught failure falls back to three tabs and logs `chat dock failed`. An uncaught one (for example a blank view) means using the off switch: `CHAT_DOCK.on=false` and restart.
- **Wrong install order.** Republishing the page after the app means a session of the old layout squeezed left. The install order in STAGING.md avoids it.
- **No banners on DAY BOARD.** Replies get no banner while DAY BOARD is in front, because the chat is on screen. That's intended, but it's a change Matt will notice.
- **Brief default-layout flash.** About 2 s of the usual layout at each start, before the config message switches the page to B.

## Notes

- **How the files were made:**
  - The two source files were copied into the worktree with one `cp` (byte-exact, hashes checked), rather than retyped, to avoid transcription errors in a 184 KB file.
  - Every change after that went through the Edit tool. Every other file was written with Write.
  - Diffs went to the job's tmp folder.
- **Writes outside the worktree:** only Edge's throwaway profile `%TEMP%\dayboard-layoutB-edge`, as the brief's command sets. It's still there; deleting it waits for Matt's OK.
- **Extra Edge flags:** `--allow-file-access-from-files` and `--virtual-time-budget=6000`, beyond the brief's command (reasons in STAGING.md).
- **Taste card:** `rules/taste-card.md` is still a stub ("Pending: the Taste Dossier writes this card"). It isn't in the worktree, so I read it from the main checkout. The style follows the approved mockup and Matt's Quiet Villain words in facts.md.
- **Throwaway cache:** `test/pycache` (about 1 MB) is a compile cache, not a deliverable.

## Waiting on Matt

- Nothing new to decide. When Matt is ready: HQ installs (STAGING.md), then he restarts and runs the checklist.

## Next

- HQ:
  1. Checks the files.
  2. Copies out `staged/`, `STAGING.md`, `test/harness.html` + PNGs, this close-out, and `start-here.md`.
  3. Republishes the page and merges the config.
  4. Copies in app.py.
  5. Confirms a single app.py process.
  6. Restarts when Matt says yes.
- Later: add One Night Press (and any optional fields) to business-status.json, and add the field shape to its `help`.
