# PC & Tools: start here

_Rewritten 2026-11-16 by the PC & Tools worker, after the Day Board layouts job._

## Current

- **Day Board redesign: two layout mockups are done.** Fake sample data only. The running board is untouched.
  - **Layout A, "Three Columns":** calendar left, Claude Duet chat in the middle, businesses stacked on the right. `work/dayboard-layouts/layout-a.png`
  - **Layout B, "Week Band and Chat Dock":** calendar band across the top, businesses in a grid below, chat docked full height on the right. `work/dayboard-layouts/layout-b.png`
  - The HTML sources sit beside the PNGs. Close-out, colors and open questions: `log/2026-11-16-dayboard-layouts.md`.
  - The brief was `work/dayboard-layouts/brief.md`; Matt's words are in `facts.md`; routing is in `log/2026-11-16-dayboard-layouts-routing.md`.
- **HQ copied the files out** (hashes checked) and removed the worktree.
- **Both PNGs are in Matt's Drive folder:**
  - "Day Board layout A": https://drive.google.com/file/d/1WEqPrvycqNZOzutGiWhKbEEgiMtBtE5h/view
  - "Day Board layout B": https://drive.google.com/file/d/1y5AjY39dVKUSShkWyo9FnSn2MrMT-WNE/view

## Waiting on Matt

- Choose layout A or B, or ask for changes.
- No live change goes into the board until he says yes.
- Small questions for when he picks (details in the close-out):
  - "Waiting on Matt" or the tracker's current "Needs you"?
  - Should "Open with Claude", the Focus view or the note box come back?

## Next

- Once Matt picks, plan the live change:
  - Back up to `DayBoard-backup-YYYY-MM-DD-<name>` first.
  - Then edit `board\day-board.html` and the theme.
- Check whether four running `app.py` copies is intended (see `facts.md`).
- Leftover: the throwaway Edge profile at `%TEMP%\dayboard-mockup-edge` can be deleted once Matt says yes.
