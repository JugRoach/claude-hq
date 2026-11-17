# Staging: Day Board business card (2026-11-16)

Matt's words, 11/16:
> Replace the separate business tiles with ONE big business card, same size and style as the current tiles (I like them big), that slowly cycles through every business: Coppice, Game Art Kit and One Night Press. Slow fade every ~20 seconds, pause while the mouse is over it, and small dots showing which business is up. One Night Press shows the business side only (deadlines, accounts, launch tasks, what's waiting on me), never content. Stage it like layout B with a backup and rollback flag, then tell me it's ready before restarting the board.

Built by HQ directly. It scored 6 by `rules/routing.md` (Opus high, HQ's own tier), and the brief would have been as long as the job.

## What it does (layout B only, config `BIZ_CARD.on: true`)

- **One card:** the business area becomes one big card, the full width and height the tiles used, with the same panel, fonts and colors.
- **Slides:** one per business, in this order: the businesses in `business-status.json` (today Coppice, then Game Art Kit), then One Night Press.
  - Each slide is the same content the tiles showed: name, state, status line, and any optional sections.
  - One Night Press always shows its four business-side sections (Deadlines, Accounts, Launch tasks, Needs you), with "Nothing tracked yet" where empty. No content of any kind.
- **Cycling:** every `BIZ_CARD.seconds` (20) it cross-fades to the next business over 1.2 s.
  - It **holds while the mouse is over the card**, and "Paused" shows in the corner.
  - The 20 s count restarts when the mouse leaves.
- **Dots:** in a strip at the bottom of the card, one per business; the filled one is the business that's up.
  - Clicking a dot jumps to that business and restarts the count.
  - A dot is brass only for a business that needs Matt, keeping layout B's rule that the accent marks only what needs him.
- **Unchanged:** the header ("3 businesses · nothing needs you · as of …") and the approval box above the card.
- **Overflow:** a slide with more rows than fit scrolls inside the card, above the dots, never under them.
- **Reduced-motion setting:** the slides switch without the fade.

## Files

| File | Installs to |
|---|---|
| `staged/board/day-board.html` | `DayBoard\board\day-board.html`, and the board artifact is republished from it (same URL) |
| `staged/app.py` | `DayBoard\app.py`. New `bizcard_cfg()`, and `board_cfg()` sends `"bizcard"` |
| `staged/config-additions.json` | merged into `config.json`: `BIZ_CARD {"on": true, "seconds": 20}` plus `BIZ_CARD_HELP` |

## Why each step is safe before the restart

- **The page shows the card only when the app sends `bizcard.on: true`.** The app running now (layout B app.py) doesn't send it, so the republished page keeps showing the tiles, even if it reloads.
- **The running app reads config.json only at start, and keeps its in-memory code,** so copying in the config and app.py changes nothing until a restart.
- **The old app's default page is unaffected** (checked by rendering it with the card flag sent).

## Rollback

- **Flag:** set `BIZ_CARD.on` to `false` in config.json, then restart (or `reload.go` once the new app is running). That brings back the separate tiles. Layout B itself stays.
- **Full:** copy `app.py`, `board\day-board.html` and `config.json` back from `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-bizcard`, republish the artifact from that page, then restart.

## Test evidence (`test/`)

The harness is layout B's, plus `card=1` (send what the new app sends) and `cardsec=N`. Headless Edge, 1920×1080 unless noted, 0 script errors in every render.

| File | What it shows |
|---|---|
| `card-1-coppice.png`, `card-2-gameartkit.png`, `card-3-onepress.png` | The card cycling with real business data (5 s per slide for the test) |
| `card-fields-coppice.png`, `card-fields-onp.png` | TEST-only optional fields plus an approval: brass "Needs you" state, rows scroll above the dot strip |
| `card-narrow-1440.png` | A smaller window (1440×900) |
| `flag-off-tiles.png` | `BIZ_CARD` off: the separate tiles, as now |
| `old-app-default.png` | The old app's default page with the flag sent: unchanged |

## After the restart (Matt)

1. Businesses show as one big card. After about 20 s it fades to the next business, and the dots move with it.
2. Rest the mouse on the card: "Paused" shows and it stays put. Move away and it resumes 20 s later.
3. Click a dot: that business shows.
