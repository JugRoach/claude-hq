# Close-out: restructure, steps 1–6 (2026-11-16 evening)

Matt was in WoW the whole time, so nothing on screen was touched.

## Decisions (Matt, one batch of questions plus two follow-ups)

- **The 7 channels, as corrected by Matt:** Finances, Taste Dossier, Businesses, Career & Transition, Daily Life, Games & Hobbies, PC & Tools.
- **Desktop projects:** handled later by computer use, scheduled, with HQ checking for SIG and games before taking the screen.
- **Syncs and the Drive workspace:** likely obsolete, so retire them rather than building a new sync.
- **Approved:** pause the BG3 routine, summaries replacing the full docs (with a quality system), archive the Drive notes, turn off the old syncs.
- **Permissions:** set up in one change so HQ works without prompts, except for money, sends, deletes and protected data.

## Done

1. **Desktop projects (steps 1–2):** no tool reaches them and the screen was off-limits, so the job is written up in `HQ/work/desktop-projects-pass.md`, with deconfliction checks, and scheduled as a one-time job for Tue 11/17 11:07 (also listed in `HQ/start-here.md`). The BG3 routine pause is in the same pass, since the routines API lists only 20 routines, all SIG reminders.
2. **PC folders (step 3):**
   - Added `Daily-Life/`.
   - Renamed Money-and-Home → `Finances/`, Career → `Career-and-Transition/`, My-Business → `Businesses/`, Games → `Games-and-Hobbies/`.
   - Fixed the root `CLAUDE.md` (channel, slug and folder table; Finances in the purchase and protection rules), `.gitignore` (`Finances/*`, `HQ/archive/`), `rules/routing.md` and the pass file in one commit, `652f75e`.
   - Businesses holds One Night Press's business side only.
3. **Full files local, summaries in the cloud (step 4):**
   - **Taste Dossier:** the full v1 is in `Taste-Dossier/full/` (docx plus text, git-ignored).
   - **Summary:** written, and it passed the new `HQ/tools/check-summary.ps1`, which checks freshness, section coverage, pointers, keep-out terms and counts. It caught a miscount (52 vs 58 questions), which was fixed.
   - The summary was uploaded to Drive, and the full v1 doc moved to Drive trash (30-day undo).
   - **Still open:** the newer master in the Taste Dossier desktop project, and the **Budget**, which isn't in Drive and whose location Matt doesn't remember. Both go to the computer-use pass.
4. **Old syncs and Drive (step 5):**
   - No new nightly sync, per Matt.
   - **Day Board's Drive mirror:** turned off live with `reload.go`, no restart; backup in `DayBoard-backup-2026-11-16-nodrive`.
   - **`routedump-upload`:** marked RETIRED. Its stuck run (started 21:13, waiting on a prompt) was stopped.
   - **Drive folder:** READ ME and Archive folder created. Moving 100+ old files is in the computer-use pass as one drag, since doing it through the API would mean 100+ permission prompts.
5. **Open items handed down (step 6):** to Businesses, Finances, Taste Dossier, Games & Hobbies and PC & Tools (`start-here.md` in each). HQ keeps only the computer-use pass and the post-reboot check.
6. **Permissions (Matt's request mid-job):** recorded in `HQ/facts.md`. Restarting the Day Board is now `HQ/tools/restart-dayboard.ps1`, allowed without a prompt.

## Notes

- **Other Drive files still hold full taste detail,** for example the 11/12 Spotify signals note and the dossier rebuild notes. They go into Archive with the rest, and are still in the cloud. Trash them once the master export is done, if Matt wants zero full taste text in Drive.
- **Day Board:** single copy, business card live, nothing else changed tonight.
