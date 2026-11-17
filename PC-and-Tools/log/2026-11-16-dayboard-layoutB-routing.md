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
