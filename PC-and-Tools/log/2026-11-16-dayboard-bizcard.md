# Close-out: Day Board business card, staged (2026-11-16)

Matt asked for one big business card that cycles through Coppice, Game Art Kit and One Night Press. It's staged like layout B and **waits for Matt's OK to restart.**

- **Routing:** scored 6 (stakes 1, ambiguity 1, taste 1, size 1, redo 0, checking 1, novelty 1), which is Opus high. That's HQ's own tier, and the brief would have been as long as the job, so HQ built it directly.
- **Backup first:** `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-bizcard` (38 files, 2.2 MB, hashes checked). It covers the code, config, data and page as they were with layout B live.
- **Built:**
  - The page shows one big card, with a 20 s cross-fade, a hold on mouse-over and clickable dots. One Night Press shows only its four business-side sections.
  - `app.py` sends `bizcard` from config `BIZ_CARD`.
  - Details: `work/dayboard-bizcard/STAGING.md`.
- **Checks:**
  - app.py compiles.
  - Diffs: app.py +11 lines; the page +65 / −2, and both changed lines are gated on the flag.
  - Headless renders with 0 script errors: the card on each business, optional fields with overflow, a smaller window, the flag off (tiles), and the old app's default page (unchanged).
  - Two fixes came from those renders:
    - The card didn't fill the business area; its grid row now takes the full height.
    - Dots overlaid long content; they now have their own strip at the bottom of the card.
- **Installed for the next restart (21:3x):**
  - Board artifact republished as version 30 (capabilities unchanged). The running app doesn't send `bizcard`, so the board keeps showing tiles until the restart.
  - `board\day-board.html` and `app.py` copied in (hashes match).
  - `BIZ_CARD {"on": true, "seconds": 20}` and `BIZ_CARD_HELP` merged into config.json, which is valid; all other keys are unchanged.
- **Not done:** no restart, per Matt.
- **Found:** a second Day Board copy has been running since 21:18:34, started from a shortcut via Explorer (not by HQ, not by auto-start). There are now two copies: 21:08:31 (HQ's restart) and 21:18:34.
  - Both hook F12 and backtick. F12 presses were logged at 21:19, 21:22 and 21:26.
  - Close both before the restart.
- **Rollback:**
  - `BIZ_CARD.on: false`, then restart: back to the tiles.
  - Full: the backup above, then republish the artifact from the backup page.
- **Housekeeping:** HQ's throwaway headless-Edge profile `%TEMP%\dayboard-bizcard-edge`, made for these renders, was deleted afterwards.

## Live (restart 2026-11-16 21:30, Matt's OK)

- **Stopped all four Day Board processes,** which were both copies (21:08 and 21:18). The WebView profile was released with no force-stops.
- **Started one fresh copy at 21:30:52** (launcher 1536 + process 42292). The log shows no errors, the chat docked, and F12, F11 and backtick hooked.
- **The business card is live:**
  - At about 21:31:05 the capture (PrintWindow, no focus change) showed Coppice, with three dots.
  - At about 21:31:40 it showed One Night Press (third dot), with its four business-side sections reading "Nothing tracked yet".
  - So it cycled by itself at 20 s per business.
- **F12 worked live on the single copy** (Matt, 21:31:00): it recorded, sent 47 characters into the docked chat, and the reply chime played. Reply banners were skipped because the chat is docked and on screen, as designed.
- **Focus:**
  - Before the restart, focus was on Day Board (Matt's 21:18 copy). After the old copies closed it went to World of Warcraft, and the new copy did not take it (checked 12 s after start).
  - About 30 s later the foreground was Day Board again. Day Board's log shows no tab switch or raise at that point, and HQ only read the window. This happened after Matt's F12 message and the replies, so it was most likely Matt's own click. Unconfirmed.
