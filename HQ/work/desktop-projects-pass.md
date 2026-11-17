# HQ job: Claude desktop projects pass, by computer use (restructure steps 1–2)

Queued 2026-11-16 22:xx at Matt's request ("later, by computer use, and schedule it in case I forget").

Not done that night: there's no tool for desktop projects, and Matt was in WoW, so the screen was off-limits.

## Before touching the screen (deconfliction)

Do every check. If any one fails, don't start: wait an hour and check again (one-shot CronCreate, or note it in `HQ/start-here.md`).

1. **Matt isn't in a game or full-screen app.**
   - Read the foreground window title (read-only, as in `HQ/tools/restart-dayboard.ps1`).
   - If it's World of Warcraft, Cyberpunk, Skyrim/Nolvus or any game, wait.
2. **SIG isn't using the PC.** SIG often runs overnight.
   - If `C:\SIG`'s app or engine is running with work queued, wait. Check counts only, never content.
   - Don't steal focus from a SIG window.
3. **Nothing else is driving the screen:** no other Claude session or worker is using computer use. Check `claude agents --json` and `ListAgents`.
4. **Tell Matt first, in one line through Claude Duet,** that HQ is about to use the screen for about 5 minutes. Go ahead unless he says stop.

## The job (in the Claude desktop app)

**The 7 Duet channels** (confirmed by Matt 2026-11-16) are: **Daily Life, PC & Tools, Money & Home, Career, Taste Dossier, My Business, Games.** One Night Press and SIG stay as their own private projects, untouched.

1. **List every desktop project** as it appears. Names seen in Drive notes: Daily Ops, Taste Dossier, Personal Taste Profile, Side Quest, Coppice, WoW Forever, SIG — Main, BG3 Builds, Spotify Stuff, Claude-efficiency.
2. **Rename** each existing project that clearly matches a channel. Likely matches, to confirm on screen:
   - WoW Forever → **Games**
   - Coppice → **My Business**
   - Taste Dossier → **Taste Dossier** (keep)
   - Daily Ops → see the next step
3. **Create the missing channels:** at least **Daily Life** and **PC & Tools**, and any of the 7 that don't exist after the renames.
4. **Archive** (don't delete) **BG3 Builds**, **Spotify Stuff** and **Claude-efficiency**.
5. **Pause the "BG3 Builds daily Drive check" routine** (claude.ai routines). The routines API only lists 20 routines, all SIG reminders, so it couldn't be reached that night. Pause it; don't delete it.
6. **Ask Matt in one batched Duet message** about any project not covered above (for example Daily Ops, Side Quest, Personal Taste Profile): which channel it becomes, or whether to archive it. Don't guess.

## When done

- Log it in `HQ/log/`, update `HQ/start-here.md` and `HQ/facts.md` (project names), commit and push.
- Give Matt one line through Duet.
