# Screen-control queue: rules (Matt, 2026-11-16)

**Chain of command:** Claude Duet is HQ, and every command comes from there. The HQ Opus session in `C:\Claude's Workspace` owns this queue: it decides what takes over Matt's screen, and when.

## Rules

1. **Every job that takes over the screen goes in `screen-queue.md` first**, from any project or desktop session.
   - Other sessions don't take the screen themselves; they hand their job to this queue.
2. **One job at a time, oldest first.**
   - Never run two at once.
   - Never start a job while another row says `running`.
3. **Before a job:** set its row to `running` with the start time.
4. **After a job:**
   - Set its row to `done` or `blocked`, with the finish time and a one-line result in notes.
   - Write a close-out in `HQ\log\YYYY-MM-DD-<job>.md`.
5. **If Matt is gaming** (check the foreground window, read-only) and the job is about 15 minutes or less, ask him first: "quick one if you've got a second to pull over?"
   - If he says "not now", wait and ask again later.
   - Longer jobs wait until he isn't gaming.
6. **Always:**
   - never click in, type into or close a game window
   - never touch the SIG app, and check SIG isn't using the screen
   - give the screen back as soon as the job is done

## Who does the clicking

The HQ Opus session is a Claude Code CLI session. On Windows it has **no computer-use tools** (docs: "Computer use in the CLI is not available on Linux or Windows"). So:

- **HQ owns the queue:** ordering, the pull-over ask, the running/done log and the close-out.
- **The clicking is done by a computer-use session,** one at a time:
  - Claude Duet, through this PC's device "jugroach-dt"
  - or one desktop-app chat with Computer use on
- **HQ hands over** with "SCREEN JOB READY: <job>" plus the job's steps, and logs the result when the executor reports back.
- **If HQ ever gets its own computer-use tools** (for example by running as a desktop-app Code session; see `HQ\work\computer-use-setup.md`), HQ runs the jobs itself under the same rules. (Checked 11/16: the move to the desktop app failed and HQ is still the hidden CLI with no such tools, so Duet does the clicking. See `HQ\log\2026-11-16-computer-use-test.md`.)

## Job file

Each job's steps live in `HQ\work\screen-jobs\<job>.md` (or a linked file). Every job file includes:
- the estimated minutes
- the deconfliction checks
- a done-check
