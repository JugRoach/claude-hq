# Routing: Day Board layout B, real build (2026-11-16)

Scored by HQ with `rules/routing.md`.

## Overrides

- **Matt in the loop?** No. He has already picked B and answered the open questions.
- **Brief longer than the job?** No.
- **Money, sends, posts or deletes?**
  - Republishing the board artifact is HQ's step, not the worker's. The page is built so the running board keeps its current layout.
  - Deleting `%TEMP%\dayboard-mockup-edge` was approved by Matt.
- **Shared resource:** the Day Board files. One worker only. It writes only in its worktree, and HQ stages the files into the live folder.

## Score

| Factor | Score | Why |
|---|---|---|
| Stakes | 2 | Matt's always-on board, with F12, Discord and audio running through it. |
| Ambiguity | 1 | The layout is chosen, but docking the chat and wiring real data are open. |
| Taste | 1 | The look was approved; this is faithful build-out. |
| Size | 2 | `app.py` (180 KB) plus the board page (72 KB), across several files. |
| Redo cost | 1 | There's a backup, but a bad restart costs Matt his board. |
| Checking | 1 | Static checks and stub renders are possible; the live check is Matt's after restart. |
| Novelty | 2 | Docking the chat into the board tab hasn't been done before. |
| **Total** | **10** | |

## Tier

- **From the table:** a total of 9–10 gives Opus at xhigh effort.
- **Bumps:** none apply, because taste is 1.
- **Tier used:** Opus at xhigh effort (`--model opus`, `CLAUDE_CODE_EFFORT_LEVEL=xhigh`).

## Backup

- Taken by HQ before anything else, at `C:\Users\mattt\Documents\DayBoard-backup-2026-11-16-layoutB`: 38 files, 2 MB, hashes checked.
- It covers code, config, data and the page.
- Left out: `whisper\` (model), `webdata\` (sign-in profile, in use), `.venv\` and the old `backup-*` folders.

## How the run went (HQ)

- **Worker:** `e9e46d20` (Opus xhigh) ran from 19:58 to 20:28 (30 min of work) in a default-location worktree, with no permission prompts.
  - HQ's watcher loop was stopped by Claude Code at about 20:00 because the PC was low on memory (a game was running). The worker itself wasn't affected.
  - HQ checked it by hand when Matt asked.
- **HQ review:**
  - Read the full app.py diff. Every change is gated on `dock_on()` / `chat_in_view()`, and every use of `views["today"]` is still valid once it becomes the dock panel.
  - Checked that the page's default-mode lines are gated on `LAYOUT==='B'`.
  - Looked at the B and B-with-fields renders: real names, accent only on Needs-you items.
  - Checked hashes against STAGING.md.
- **21:05, page:** republished artifact `1eYpnzMrkWkP5L8LXkfyQr` as version 29 to the same URL.
  - Capabilities carried forward unchanged.
  - Read-back is identical to the staged file except for the one blank line the service adds after `<body>`, which the previous version had too.
- **21:07, Day Board folder:**
  - Checked that the live files still matched the backup.
  - Copied `board\day-board.html`.
  - Merged `CHAT_DOCK` and `CHAT_DOCK_HELP` into config.json as text, keeping its formatting. The JSON is valid, and every other key is unchanged.
  - Copied `app.py`. Hashes match, and it compiles (in-memory check, nothing written).
- **Not done:** no restart, no trigger files. The running board's processes are unchanged.
- **Found:** two Day Board instances are running (13:25 and 15:10). Close one before the restart.
