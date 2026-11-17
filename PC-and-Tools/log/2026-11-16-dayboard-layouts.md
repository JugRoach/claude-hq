# Close-out: Day Board layouts A and B (2026-11-16)

Mockups only. Nothing in `C:\Users\mattt\Documents\DayBoard\` was changed, the running board and the screen were not touched, and nothing was uploaded, committed or pushed.

## What was done

Two layout options for the Day Board redesign, each as a self-contained HTML file and a 1920×1080 PNG rendered with headless Edge. Both show one window with two tabs (`DAY BOARD | DISCORD`, Day Board active), the calendar, the Claude Duet chat, and four business tiles. All data is fake.

- **Layout A, "Three Columns":** calendar down the left (today's list, then the next four days, then to-do), Claude Duet chat full height in the middle, businesses stacked down the right.
- **Layout B, "Week Band and Chat Dock":** calendar as a band across the top (today plus the next four days side by side), a one-line to-do strip, businesses in a grid below (One Night Press wide, in four quarters), and the chat docked full height on the right edge.

Shared by both:

- **Tabs:** the active tab is taller, page-colored, cream-labeled and has a cream top bar. Discord is a dimmer tab with its `Ctrl+Alt+D` shortcut.
- **Chat:** six short fake messages, a message box, a `Send` button, and the hint "F12 talks into this box, from any tab."
- **Business states:** exactly the four from the brief. One Night Press is "Waiting on Matt", Brass Key Supply is "Earning", Ledger Lane is "Running", Slow Tide Goods is "Not launched". Each state has its own marker shape as well as its label, so it doesn't rely on color.
- **One Night Press tile:** business side only. Deadlines, accounts ("Payout account: pending verification"), launch tasks ("Launch checklist 4 / 9") and what's waiting on Matt. No content of any kind.
- **Extra section:** "To-do today", kept small. It is the only section taken from the current board (read-only look at `board\day-board.html` for its section list; no data copied).

## Files

Written in the worktree `C:\Claude's Workspace\.claude\worktrees\sequential-drifting-corbato\` (branch `worktree-sequential-drifting-corbato`), at these paths under `PC-and-Tools\`:

| File | Path |
|---|---|
| Layout A image | `work\dayboard-layouts\layout-a.png` |
| Layout B image | `work\dayboard-layouts\layout-b.png` |
| Layout A source | `work\dayboard-layouts\layout-a.html` |
| Layout B source | `work\dayboard-layouts\layout-b.html` |
| This close-out | `log\2026-11-16-dayboard-layouts.md` |
| Start-here | `start-here.md` |

Full PNG paths until HQ copies them out:

- `C:\Claude's Workspace\.claude\worktrees\sequential-drifting-corbato\PC-and-Tools\work\dayboard-layouts\layout-a.png`
- `C:\Claude's Workspace\.claude\worktrees\sequential-drifting-corbato\PC-and-Tools\work\dayboard-layouts\layout-b.png`

## Colors, with CIELCh L and C

Computed from sRGB, D65 white point. Both layouts use the same palette.

**Base colors (limit: L ≤ 35, C ≤ 12). All six pass.**

| Role | Hex | L | C |
|---|---|---|---|
| Tab strip | `#0E0D0E` | 3.7 | 0.6 |
| Page | `#141213` | 5.7 | 1.1 |
| Panels and tiles | `#1B191A` | 9.0 | 1.3 |
| Raised (buttons, Matt's messages) | `#242122` | 13.1 | 1.7 |
| Hairline | `#302C2D` | 18.4 | 2.0 |
| Stronger edge | `#4B4544` | 29.8 | 2.8 |

**Text and accent (not bases, listed for the record).**

| Role | Hex | L | C | Contrast on panel |
|---|---|---|---|---|
| Cream text | `#E8E2D6` | 90.0 | 6.6 | 13.6 : 1 |
| Secondary text, control edges | `#A8A297` | 66.8 | 6.5 | 6.9 : 1 |
| Muted text (past items, small notes) | `#8A847A` | 55.4 | 6.2 | 4.7 : 1 |
| Accent | `#B08D57` | 60.8 | 34.3 | 5.7 : 1 |

Cream and the accent are unchanged from the current theme. The bases are a hair warmer than the current ones so they sit with the cream. Secondary and muted text are lighter than the current theme's (`#A39E94`, `#6B6760`) for arm's-length reading.

## Self-check against the brief

Both PNGs opened and checked after the last render.

- Nothing clipped; both are exactly 1920×1080 with a 24 px margin at the bottom.
- Body text is 16 to 18 px, section titles 21 to 26 px, the smallest notes 14 px.
- No gradients, glows, glass, blur or shadows. Corners are 2 px. No emoji, icons or badges. No pure white.
- The accent appears only on "now" in the calendar (the now line and "Next, in 18 min") and on what's waiting on Matt (the state, the section label, two bullets, and the count in the Businesses heading).
- Every button (`Send`, `Review`, `Open`, `Details`) has a label and a visible edge. `Send` is the largest and has the heaviest edge.
- Self-contained: inline CSS, system fonts only (Segoe UI, Cambria), no network requests.

## Unsure of

1. **The worktree is one commit behind.** EnterWorktree branched from `origin/master` (726293b), which doesn't have HQ's local commit afb64e2. So in the worktree `facts.md` is empty and `brief.md` and the routing log are missing. I read those from the main checkout, read-only. **When copying out, take only the six files above. Don't copy the worktree's empty `facts.md` over the real one.**
2. **Taste card is still a stub** ("Pending: the Taste Dossier writes this card"). The style follows the brief's Quiet Villain rules only.
3. **State names.** The brief says "Waiting on Matt"; the live tracker (`business-status.json`, per `facts.md`) calls it "Needs you". The mockups use the brief's wording. The live change will need one or the other.
4. **Accent has two jobs** ("now" and "waiting on Matt"). I read "exactly one accent" as one color used sparingly. If Matt wants it in a single spot only, the calendar's now line can go cream.
5. **Control edges use the secondary text color** (L 66.8), so buttons and the message box read as controls. If control edges count as base colors, they are over L 35 and would need rethinking.
6. **F12 hint wording.** I don't know whether F12 is hold-to-talk or a toggle, so the hint says only "F12 talks into this box, from any tab."
7. **Sections left out.** The current board also has "Open with Claude", the Focus view and the jot-a-note box. None are in the mockups; the chat is assumed to replace the note box. Matt may want some back.
8. **Empty space.** The chat has blank room above the first message in both layouts, and the coming-days columns in B are mostly empty with this sample data. Real data may fill them differently.
9. **Fixed size.** The mockups are drawn for 1920×1080 only. The real board scales and reflows (`BOARD_FIT`); that isn't modeled.
10. **Fake business names** (Brass Key Supply, Ledger Lane, Slow Tide Goods) are made up and weren't checked against real companies.
11. **Housekeeping.** The throwaway Edge profile is still at `%TEMP%\dayboard-mockup-edge`; I left it because deletes wait for Matt. Early on I adjusted a few font sizes in `layout-a.html` with one `sed` command inside the worktree; every other write went through the Write and Edit tools.

## Waiting on Matt

- Choose layout A or B, or ask for changes.

## Next

- HQ checks the two PNGs, copies the files out of the worktree, uploads to Drive, and removes the worktree.
- After Matt picks: plan the live change (back up first, then `board\day-board.html` and the theme).
