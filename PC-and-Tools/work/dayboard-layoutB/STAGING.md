# Staging: Day Board layout B, "Week Band and Chat Dock" (2026-11-16)

For HQ. Everything here is staged, not live. Nothing in `C:\Users\mattt\Documents\DayBoard\` was changed, and the running board was not touched.

## What's staged

| File | Installs to | sha256 |
|---|---|---|
| `staged/board/day-board.html` | `DayBoard\board\day-board.html`, then republish the board artifact from it | `0694613dee7530e8ab029477c2ab3d2c81ef302318bf03cf4bd08a40f0cfbb9b` |
| `staged/app.py` | `DayBoard\app.py` | `155d34d2da8fbcd9ac0b6f150d12e3b26f01fa1a1044561145ed0dbe0801f22e` |
| `staged/config-additions.json` | merge into `DayBoard\config.json` | `bb57bb0fff09739215b06ceda5d45e78c253345f194e658533074a1b310ca845` |
| `test/` | **don't install**: harness and screenshots only (`test/pycache` is a throwaway compile cache) | |

## Install steps

Do them in this order. Each step is safe on its own, because the running (old) app.py never sends layout B.

1. **Check the backup** is still at `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-layoutB`.
2. **Page:**
   - Copy `staged/board/day-board.html` over `DayBoard\board\day-board.html`.
   - Republish the board artifact `https://claude.ai/artifact/1eYpnzMrkWkP5L8LXkfyQr` from it, to the same URL, the same way the current page was published. The file starts with the artifact's own document skeleton, like the current one.
   - Capabilities are unchanged: `db` (same collections and docs), `dictation`, and `mcp` (Google Calendar `list_events`, Google Drive `download_file_content`). In layout B, the calendar call only asks for a wider date range.
   - The running board keeps its current look, even if the page reloads (checked pixel for pixel; see Test evidence).
3. **Config:** merge `staged/config-additions.json` into `config.json`.
   - It adds two keys: `CHAT_DOCK` and `CHAT_DOCK_HELP`. `BOARD_FIT` is unchanged.
   - The running app ignores the new keys. Its Ctrl+Alt+T re-reads config.json before saving, so the merged keys survive.
4. **App:** copy `staged/app.py` over `DayBoard\app.py`. The running copy keeps its in-memory code; nothing changes until a restart.
5. **Restart:** Matt's next restart, or `restart.go` once Matt says yes.
   - **Before restarting, check that only one `app.py` is running.** facts.md recorded four `pythonw app.py` processes on 2026-11-16. Two copies would fight over F12 and backtick.

## What changes when

| After | What Matt sees |
|---|---|
| Page republished | Nothing. The page waits for layout B, and the old app never sends it. |
| Config merged | Nothing. The old app ignores `CHAT_DOCK`. |
| app.py copied | Nothing until restart. |
| Restart | One window: DAY BOARD \| DISCORD. On DAY BOARD, layout B is on the left and the Claude Duet chat is docked on the right. |

For about 2 s after a restart, the page shows its usual layout until the first config message arrives. The theme arrives the same way today.

## Rollback

- **Off switch:** set `CHAT_DOCK.on` to `false` in config.json, then restart.
  - Back to the three tabs exactly as before.
  - The page stays the new one, and its default mode matches today's page pixel for pixel.
- **Full rollback:**
  - Copy `app.py` and `board\day-board.html` (and `config.json`, if wanted) back from `DayBoard-backup-2026-11-16-layoutB`.
  - Republish the artifact from the backup page.
  - Restart.
- **New app, old page** (page not republished yet): the board shows its usual layout in the narrower left area. It's still usable, but it isn't B. Republish first.

## Behavior changes (CHAT_DOCK on)

### The app

1. **Tab bar** shows DAY BOARD | DISCORD.
   - The CLAUDE DUET label is built as before but hidden.
   - The active tab's underline is cream instead of brass, as in the approved mockup.
2. **DAY BOARD tab:** the board on the left and the Claude Duet chat on the right, with a 1 px hairline between.
   - The chat is `width` logical px wide (560), scaled for DPI, and never more than half the area.
   - Both resize with the window. The chat keeps its width and the board takes the rest; only in a narrow window does the chat shrink to half.
3. **DISCORD tab:** Discord covers the whole area, as now. The board and chat keep running behind it (covered, never hidden), so the chat never resizes on a tab switch.
4. **Anything that opened the Claude Duet tab now opens DAY BOARD:**
   - the menu item, renamed "Claude Duet chat (on the Day Board tab)"
   - clicking a reply banner
   - a failed Allow/Deny ("… Opening Claude Duet.")
5. **Keyboard focus:** opening DAY BOARD puts it in the chat. Before, it went to the board page, which in B has nothing to type into.
6. **Unread mark (orange dot):** it sits on the left end of DAY BOARD and lights only while DISCORD is in front. Opening DAY BOARD clears it. There's no mark while the chat is on screen. The nudge dot keeps the right end of the same tab.
7. **Reply and approval banners:**
   - They hang from the DAY BOARD tab and show only while DISCORD is in front.
   - **On DAY BOARD there are no banners** (the chat is on screen), so no banner Reply-by-voice there. Use the chat or F12. Before, new replies did show banners on the Day Board tab.
8. **Nudges:**
   - The toast slides out just right of DISCORD (before: right of CLAUDE DUET).
   - The dot on DAY BOARD and the page glow work as before.
9. **The board page** is told `layout: "B"` in its config message, but only while the chat really is docked. If docking fails at start, the app logs `chat dock failed`, keeps three tabs, and the page stays in its usual layout.
10. **Board zoom (BOARD_FIT):** the settings are unchanged, but the board area is narrower, so the zoom is lower: about 1.06 instead of 1.27 in a 1920-wide window.
11. **reload.go** re-applies the `CHAT_DOCK` width. Turning the dock on or off needs a restart.

**Unchanged**, checked by reading every path:

- F12: record, auto-send, Esc cancel, early start, and typing into the focused chat box. It is in-page JS on the chat view, so it doesn't care where the view sits.
- F11 screenshot-send, backtick (Discord push-to-talk / hot mic), and Ctrl+Alt+D/T/H/V/W.
- The audio mirror (including mute-all while F12 is hot), chimes, and pre-alerts.
- The mic HUD and the tab bar's CLAUDE/DISCORD mic labels. The HUD's "claude" light shows F12 recording, not a tab, so it needed no change.
- Approval cards: Allow/Deny still press the real card.
- guard_loop and apply_z (one window, as now), place (only places the Day Board window in one-window mode, as now), group_sync (off in one-window mode, as now).
- The trigger files and restart.
- FLIP_FALLBACK (off in config) still can't type in one-window mode, as now.

**CHAT_DOCK off or missing:**

- Every path reduces to today's code.
- The only differences:
  - The config message also carries `"layout": ""`. The old page ignores it; the new page treats it as its usual layout.
  - Two hidden, unused dot panels sit on the DAY BOARD tab label.

### Where the separate Claude tab was assumed (all traced)

| Place | Docked behavior |
|---|---|
| `TAB_TITLES["claude"]`, `tab_windows`, `show_tab_windows`, `group_sync`, `place`, `toggle_hidden`, `our_rects` | Separate-window mode only. Docking needs one-window mode, so these are unused, as now. |
| `show_tab("claude")` (menu, banner click, `apr_fail`) | Opens DAY BOARD. |
| `state["tabwin"] == "claude"` checks: `unread_mark`, `banner_gone`, `reply_toast`, the unread tick | One helper, `chat_in_view()`: the Claude tab, or DAY BOARD when docked. |
| `banner_anchor` (CLAUDE DUET label) | DAY BOARD label. |
| The unread dot on the CLAUDE DUET label | A twin dot on the DAY BOARD label; only one shows. |
| Nudge toast position (after the 3rd tab) | After the last visible tab. |
| HUD claude light, tab-bar mic labels | Recording state, not a tab: unchanged. |
| `send_with_flip` (needs the chat window in front) | Unchanged (off; already can't work in one-window mode). |

### The board page

- **Default mode** (no `layout`, or `layout: ""`): unchanged. Rendered next to the live page, it differs only by the page's random grain texture (max 7/255).
  - The same holds after switching into B and back.
  - The calendar call is the same as now: yesterday through tomorrow.
- **Layout B** (`layout: "B"`), from the approved mockup:
  - **Header:** long date (serif), weekday, the workout line and week tally, and the clock.
  - **Week band:**
    - The **Today** column is the live day list: the default page's own timeline, always shown as a list. It keeps routines, pre-alerts, nudges, workout click/Ctrl+Alt+W, and the Next line. It follows the now line unless Matt scrolled it in the last 2 minutes.
    - Then **four day columns**: calendar events only, all-day first, from the same `list_events` call. In B the range runs from yesterday to the end of today + 4.
  - **To-do strip:** the same live, checkable list, laid out in a row, with "N of M done".
  - **Businesses:**
    - One tile per entry in business-status.json (or the newer Drive copy), plus a One Night Press tile always.
    - The header reads "N businesses · Needs you: N" (or "nothing needs you") and "as of …".
    - The approval box is kept.
  - **Left out in B:** Open with Claude (tasks), the note box (inbox) and Focus. Their data still loads.
  - **Colors:** the mockup palette, with bases at L ≤ 35, C ≤ 12.
    - The accent `#B08D57` marks only Needs you chips, Needs you items and labels, their count, and the approval box.
    - The clock, Now line, Next line, pre-alert text, nudge glow, glint and "Workout due" are cream.
    - B keeps this palette whatever THEME / meta/theme say. Those still recolor the default page.
  - **Motion:** a fade and one glint on today's list items, day items and business tiles that are added or changed (MOTION on/ms/glint). Nothing glints on load, on a mode switch, or at the day rollover.
  - **Narrow fallback:** below 1000 CSS px wide, the band shows today plus 2 days and the businesses stack. Below 640 CSS px tall, the page scrolls.

## business-status.json: optional fields (for the file's help text)

All four fields are optional, and all are business side only: names, dates, account states, task names. Never content.

```json
{
  "name": "One Night Press",
  "state": "Not launched",
  "line": "One short status line.",
  "updated": "2026-11-16T10:00:00-05:00",
  "deadlines":    [{"what": "Sales tax registration", "due": "2026-11-20"}],
  "accounts":     [{"name": "Payout account", "status": "pending verification"}],
  "launch_tasks": {"done": 4, "total": 9, "next": "Set up tax settings"},
  "needs":        [{"what": "Approve the price list", "due": "2026-11-18"}]
}
```

- **Plain strings work:** any list item can be a plain string, for example `"needs": ["Approve the price list"]`.
- **`due`:**
  - `YYYY-MM-DD` shows as "Fri Nov 20".
  - An ISO date-time shows by its date.
  - Anything else shows as written.
- **`launch_tasks` can also be a list:** `[{"task": "Set up tax settings", "done": false}, …]`. Then the count comes from `done: true`, and "Next task" is the first item that isn't done.
- **Other key names accepted:**
  - deadlines: `what|name|task|title|text` and `due|date|when`
  - accounts: `name|account|what|text` and `status|state|note`
  - needs: `what|task|title|name|text` and `due|when|note`
- **Where it shows:**
  - On an ordinary tile, a section shows only if it has data.
  - On the One Night Press tile, all four sections always show; an empty one says "Nothing tracked yet".
  - Each list shows up to 6 rows, then "+N more in business-status.json".
- **One Night Press:** its tile uses the entry named "One Night Press" (any case). With no entry, it shows Not launched and four empty sections.
- **The "Needs you" count** counts each `needs` item, or 1 for a business whose state is Needs you but has no items.
- **State labels:** a state starting "Waiting…" also shows as **Needs you**. The label is always "Needs you".

Suggested sentence for the file's `help`:

> Optional per business, business side only: deadlines [{what, due YYYY-MM-DD}], accounts [{name, status}], launch_tasks {done, total, next}, needs [{what, due}]; list items may be plain strings. Layout B shows them on that business's tile; One Night Press always has a tile.

## After-restart checklist for Matt

1. The window shows **DAY BOARD | DISCORD**. DAY BOARD has the week band, to-dos and businesses on the left, and the Claude Duet chat on the right.
2. **F12:** press, talk, and it sends into the docked chat.
   - Try it again from the DISCORD tab.
   - Click into a reply box first, and F12 types there.
   - Esc cancels.
3. **Backtick:** the Discord hot-mic light comes on, then mutes itself after you stop talking.
4. **Toasts:**
   - On DISCORD, send something with F12. When the reply lands, a banner drops from DAY BOARD, an orange dot lights on DAY BOARD, and the chime plays.
   - Open DAY BOARD: the dot goes out and the reply is in the chat.
5. **Discord tab:** Discord fills the whole window, and a call keeps going when you switch back.
6. **Resize:** drag the window smaller, then maximize. The chat keeps its width (it only shrinks in a narrow window) and the board reflows.
7. **The board:** today plus the next four days; a to-do ticks; Coppice, Game Art Kit and One Night Press tiles.

If anything is off, set `CHAT_DOCK.on` to `false` in config.json and restart, or ask HQ to roll back.

## What couldn't be wired to real data, or tested

- **One Night Press:** there's no entry in business-status.json, so the tile shows Not launched with "Nothing tracked yet" in all four sections. Real deadlines, accounts, launch tasks and needs have to be added to the file.
- **Coppice and Game Art Kit** have no optional fields yet.
- **No buttons on Needs-you items.** The mockup's Review/Open buttons weren't built, because there's nothing to wire them to and they'd be dead controls.
- **Future-day columns** show calendar events only. Routines and the workout stay on today.
- **The docked chat and the WinForms docking couldn't be run.** The brief forbids running app.py, so they were checked by reading the code.
  - Re-parenting the board's own WebView2 into a panel is new. It uses the same Remove/Add that `embed_tabs` already uses for the chat and Discord views.
- **Native colors:** the tab underline goes cream when docked. These stay brass, as now: the nudge dot, the toast edge, the banners' brass rule, the Allow button and the HUD's hot-mic color.
- **Default-mode quirk, left as is:** when the default page is narrow enough for its list view, a calendar error message is dropped. B shows the message.

## Test evidence (`test/`)

- `harness.html`: TEST ONLY.
  - It loads the staged (or, with `src=live`, the current) page with a fake runtime.
  - Calendar events and to-dos are all titled "TEST …". Business data is today's real business-status.json.
  - It answers `dayboard-hello` like app.py, then sends the page's own preview clock (10:42).
  - Render command: the brief's Edge command, plus `--allow-file-access-from-files` (to read the page file) and `--virtual-time-budget=6000` (so the messages and timers settle before the shot). Pass `&w=…&h=…` to match `--window-size`.
- **Screenshots** (window 1920×1080; board area 1359×1045 in B, at zoom 1.06):

  | File | What it shows |
  |---|---|
  | `b-1920x1080.png` | Layout B with real business data |
  | `b-fields-1920x1080.png` | B with TEST-only optional fields and an approval, to check rendering and the accent rule |
  | `b-1440x900.png` | B in a smaller window (zoom 0.8) |
  | `default-1920x1080.png` | Staged page, old app (no layout key) |
  | `off-1920x1080.png` | Staged page, new app with the dock off |
  | `flip-1920x1080.png` | B, then back to the usual layout |
  | `live-default-1920x1080.png` | The current page, for comparison |

- **Pixel diff** of default, off and flip against live, below the harness bar: max channel difference 7/255 (the random grain); 0 pixels differ by more than 12.
- **Compile:** `py_compile` with the DayBoard venv passes.
- **Lint:** pyflakes reports one warning, an unused `Region` import that's also in the live app.py, and no undefined names.
