# Routing: Day Board layouts (2026-11-16)

Scored by HQ with `rules/routing.md`.

## Overrides

- **Matt in the loop?** No. He picks a layout afterwards, but making the two options doesn't need him.
- **Brief longer than the job?** No.
- **Money, sends, posts or deletes?** No. The Drive upload goes to Matt's own private folder, which he asked for, and HQ does it after checking the images.
- **Shared resource?** The screen. The worker renders with headless Edge using its own temporary profile, so it never touches the screen or the running board.

## Score

| Factor | Score | Why |
|---|---|---|
| Stakes | 1 | These are mockups only, but Matt will pick one to build. |
| Ambiguity | 1 | The style brief is specific; the layout is open. |
| Taste | 2 | The whole job is visual judgment. |
| Size | 1 | Two HTML mockups plus rendering. |
| Redo cost | 0 | Cheap to regenerate. |
| Checking | 2 | Only Matt's eye can judge it. |
| Novelty | 1 | A new style and the first department pilot. |
| **Total** | **8** | |

## Tier

- **From the table:** a total of 6–8 gives Opus at high effort.
- **Bump:** taste scored 2 and the total is 7 or more, so the job goes to Fable.
- **Tier used:** Fable at high effort (`--model fable`, `CLAUDE_CODE_EFFORT_LEVEL=high`).

## How the run went (HQ)

- **19:26:31, worker 1 (`7393d6ec`):** stopped at a permission prompt for a git worktree it chose under `PC-and-Tools\.claude\worktrees\`. HQ stopped it and removed the empty worktree it had made.
- **19:29:43, worker 2 (`b9ac7f60`):** told not to use a worktree. Claude Code's guard for background jobs then refused file writes in the shared folder, and the worker asked whether to get around it with shell writes or a settings change. HQ declined both and stopped it.
- **19:33:58, worker 3 (`b0f4b942`):** used a worktree in the default location. It finished at 19:41 (7m 38s of work) with no prompts.
- **19:42:** HQ checked both PNGs by eye, copied the six files out (hashes match), and uploaded the PNGs to Drive folder `1ECQpwRMhrm3--ue-PMHzrUGX3cq1M4AF`:
  - "Day Board layout A": file id `1WEqPrvycqNZOzutGiWhKbEEgiMtBtE5h`
  - "Day Board layout B": file id `1y5AjY39dVKUSShkWyo9FnSn2MrMT-WNE`
- **Cleanup:** the worker and its worktree are removed.
- **Total wall time:** about 16 minutes from first launch to upload.
- **Lesson for `rules/routing.md`:** a background worker in this repo must use a worktree at the default location, and work that isn't committed yet has to be committed before launch so the worker can see it.
  - The worktree branched from `origin/master`, not local master, so the worker read the newer files from the main checkout.
