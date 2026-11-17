# Brief: Day Board layouts A and B (2026-11-16)

You are the PC & Tools worker. Make **two layout options** for Matt's Day Board redesign, as PNG screenshots. These are mockups only: no live change.

Read `../../facts.md` first. It covers how Day Board is built, its current theme and Matt's own words.

## What goes on the page

- **One window, two tabs** across the top: `DAY BOARD | DISCORD`. The Claude Duet chat moves onto the Day Board page; Discord stays its own tab.
  - Draw the tab strip so it's obvious which tab is active.
- **The Day Board page has three parts:**
  1. **Calendar:** today, plus what's coming (the next few days).
  2. **Claude Duet chat:** a short fake conversation, a message box, an obvious Send button, and a small hint that F12 talks into it.
  3. **Business tiles:** one per business. Each shows its state as one of exactly four: **Running, Earning, Not launched, Waiting on Matt**. Use 3 or 4 fake businesses.
- **The One Night Press tile covers the business side only:**
  - deadlines
  - accounts (e.g. "Payout account: pending verification")
  - launch tasks (e.g. "Launch checklist 4 / 9")
  - what's waiting on Matt
- **Fake sample data everywhere.** Never put story titles, characters, plots, art or anything creative in the One Night Press tile; generic business items only. Don't copy any real data from Day Board.
- **Optional:** for other sections Matt already relies on, you may read `C:\Users\mattt\Documents\DayBoard\board\day-board.html`, **read-only**. Keep any of those sections small.

## Style: "Quiet Villain"

- **Base colors:** dark and low-chroma, with every base at CIELCh L ≤ 35 and C ≤ 12. Compute and list the L and C values in your close-out.
- **Text:** cream, never pure white.
- **Accent:** exactly one small warm accent, used only where the eye should land. The current accent `#B08D57` is a fine starting point.
- **Finish:** matte. That means:
  - no gradients, glows, glass or blur
  - no drop shadows beyond a hairline
  - no neon
- **Nothing that looks like generic AI design.** That means:
  - no purple or blue gradients
  - no sparkle or robot icons
  - no emoji icons
  - no rounded-pill-everything
  - no "AI assistant" badge
  - no oversized hero text
- **Every control obvious:** buttons look like buttons, with a visible label and edge. Readable at arm's length.
- **The two layouts must differ in structure,** not just in color: a different arrangement of calendar, chat and businesses. Name and describe each in one line.

## How to render (never touch the screen)

- Write `layout-a.html` and `layout-b.html` in this folder. Each must be self-contained: inline CSS, no network fonts. Use system fonts; Segoe UI and Cambria are fine.
- Render each at 1920×1080 with headless Edge and a throwaway profile outside the repo:
  ```
  & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$env:TEMP\dayboard-mockup-edge" --window-size=1920,1080 --screenshot="<abs path>\layout-a.png" "file:///<abs path>/layout-a.html"
  ```
- Open each PNG with the Read tool and check it yourself: nothing clipped, text readable, rules above met. Fix and re-render until both pass.

## Hard limits

- **Use a git worktree:** background jobs in this repo must write inside one.
  - Create it with EnterWorktree at its **default location**. Don't pass a custom path; it goes under the repo root's `.claude\worktrees\`.
  - Inside the worktree, write to the same relative paths as below (`PC-and-Tools\work\dayboard-layouts\`, `PC-and-Tools\log\`, `PC-and-Tools\start-here.md`).
  - Don't commit, push or merge. HQ copies your files out and removes the worktree.
  - Don't write files through the shell to get around the write guard, and don't change any settings.
- **Write only inside `C:\Claude's Workspace\PC-and-Tools\`.**
- **Never touch the running Day Board.** Don't:
  - open its window or focus it
  - minimize it
  - restart it
  - take desktop screenshots
  - use computer use
  - change anything in `C:\Users\mattt\Documents\DayBoard\`
- **Don't read** `config.json`, `webdata\`, logs or anything else there except `board\day-board.html`.
- **Don't upload anything.** HQ uploads to Drive after checking your images.

## When done

1. Write the close-out to `../../log/2026-11-16-dayboard-layouts.md`:
   - what each layout is
   - the base colors with their L and C values
   - the PNG paths
   - anything you're unsure of
2. Rewrite `../../start-here.md` (Current / Waiting on Matt / Next) to reflect the result.
3. Stop.
