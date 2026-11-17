# HQ: start here

_Rewritten 2026-11-16 ~22:50 by HQ, after the restructure (steps 1–6)._

## Current

- **The company folder is `C:\Claude's Workspace`** (git: private `JugRoach/claude-hq`).
  - 7 departments match the Duet channels: Finances, Taste Dossier, Businesses, Career & Transition, Daily Life, Games & Hobbies, PC & Tools.
  - Plus HQ and One-Night-Press (private).
  - The channel table is in the root `CLAUDE.md`.
- **This PC is the home for all files.** The Google Drive "Claude Duet" folder is retired: READ ME at the top, and old notes go to its Archive folder.
- **HQ runs hidden at logon** (`Claude HQ.lnk` → `HQ\tools\start-hq-hidden.vbs`). Permissions are in the user `settings.json` (2026-11-16): auto mode, with prompts only for money, sends and posts, deletes, and Finances or Taste Dossier work outside their folders.
- **HQ tools:**
  - `tools/restart-dayboard.ps1`: safe Day Board restart or `-Status`.
  - `tools/check-summary.ps1`: the quality gate for cloud summaries.
  - `tools/hq-window.ps1`: show or hide HQ windows.

## Waiting on Matt

- Nothing blocking. Department items are in each department's `start-here.md`.

## Next

- **HQ's computer-use pass, scheduled Tue 11/17 11:07** (this session's one-time job; if HQ restarted, do it from here). Follow `work/desktop-projects-pass.md`, starting with its deconfliction checks:
  1. Rename or create the 7 channel projects.
  2. Archive BG3 Builds, Spotify Stuff and Claude-efficiency.
  3. Pause the BG3 daily Drive check routine.
  4. Export the Taste Dossier master and the Budget to the PC.
  5. Turn off the routedump-upload schedule.
  6. Move the old Drive notes into Archive.
- **After the next PC restart,** confirm "HQ Opus" shows in Claude Duet and takes a test job.
- **Route jobs from Duet to departments** with `rules/routing.md`.
