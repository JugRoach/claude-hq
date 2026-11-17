# Routing: who does the job, on which model, at what effort

Only HQ edits this file. One table for every department, in Duet and on the PC (Matt, 11/17/2026).

## 1. Overrides (check first)

- **Money, sends as Matt, public posts, deletes, new accounts and anything that can't be undone wait for Matt's yes,** at any tier.
- **One worker at a time per shared resource.** The screen, the game files and the GPU are shared resources.
- **Do it yourself, without a worker,** when writing the brief would take longer than the job. Taste calls are the exception: they always go to Fable.

## 2. Who does it

| Situation | Who |
|---|---|
| Talk, routing, relays, short lookups, read-only questions about a department | HQ itself (it reads the department's files) |
| Multi-step work over ~5 steps or ~10 minutes | A thread, one per job |
| Changes a department's own records, routines or files, or needs its long context | That department, in one batched message |
| Unattended, heavy, local files only, no connectors | PC job on the API lane |
| Text in, text out, no tools (rewrite, classify, judge, summarize a file) | One-shot API runner, once built |
| Takes over the screen | HQ screen queue (`HQ/queue/`) |

## 3. Model and effort by task type

| Task type | Model | Effort |
|---|---|---|
| Taste, design, visuals, wording in Matt's voice, purchases ("would he like it?"), high-stakes judgment, business decisions, health or science verdicts | Fable | high; xhigh only after high missed once |
| Deep analysis, plans, code, debugging, system and config design | Opus | medium; high for builds, money, security, deletes, public output |
| Research, drafting, summaries, source checks for the Verifier | Sonnet | medium; low for simple lookups. Always set it: Sonnet defaults to high |
| Mechanical or bulk: counts, renames, inventories, log parsing, formatting, pre-filtering inbound mail or research before a bigger model reads it | Haiku | low |

Bumps:
- **Unsure which row:** go one tier up. Matt wants the best result first, then the least usage.
- **Failed once:** one tier up. **Failed twice:** stop and tell HQ.
- **A saved template exists and the result can be checked mechanically:** one tier down.
- **The Verifier uses a different model from the maker:** at least Sonnet; Fable for taste or high-stakes claims.

## 4. Lanes (whose usage pays)

- **Needs Matt, connectors or Duet posting:** Duet, on weekly plan usage. Spend freely to 75% of the week, then spread the rest.
- **Unattended and local-only:** PC API lane, on the API credit. The API priority order is in the shared core.
- Never create API keys, add payment methods, turn on auto-reload or top up without Matt's yes.

## 5. Keep fixed costs low

- Small PC jobs run in the lean lane (`dispatch-job.ps1 -Lean`, once built), not the full workspace.
- Keep shared prompt files byte-stable (no dates or timestamps at the top), and run similar jobs back to back within 5 minutes so later jobs read the cache.
- Nightly and weekly sweeps that can wait up to 24 hours go through the Batch API at half price.
- Departments reply to HQ once, at the end. Progress stays on their own status.
- Long-lived sessions rotate past ~50% context or monthly, after `start-here.md` is updated, never mid-job.

## 6. Proof

- Every result names the model and effort behind its key step.
- The job log (`HQ\jobs\`) records: date, department, task type, model, effort, lane, input/output/cached tokens, cost, pass/fail.
- Untagged jobs are refused.
- The weekly HQ review checks the log and 10 close-outs against this table.

## 7. How to launch a PC job

1. **Write the brief to a file** in the department's `work\<job>\` folder.
   - The department is the one for the job's Duet channel; the channel-to-folder table is in the root `CLAUDE.md`.
   - Finances and Taste Dossier work stays in their local-only folders.
2. **Commit and push first.** A worker's git worktree starts from `origin/master`, not local master, so anything unpushed (the brief, new facts) is missing inside it.
3. **Launch:**
   ```powershell
   cd "<department folder>"
   $env:CLAUDE_CODE_EFFORT_LEVEL = "<low|medium|high|xhigh|max>"
   claude --bg --model <haiku|sonnet|opus|fable> "Read work\<job>\brief.md and carry it out. Enter a git worktree at the default location first (no custom path)."
   ```
   - Background workers in this repo can only write inside a git worktree.
   - A worktree at the default location (`.claude\worktrees\` at the repo root, which git ignores) needs no permission tap.
   - A custom path triggers a permission prompt that nobody can answer.
   - Never tell a worker to get around the write guard with shell writes or a settings change.
4. **Watch it** with `claude agents --json`:
   - Plain `claude agents` refuses to run when its output is piped.
   - In PowerShell 5.1, pipe through `Out-String` before `ConvertFrom-Json`, then unwrap the array with `ForEach-Object { $_ }`.
   - Check `state` (`working`, `blocked`, `done`) and `waitingFor`.
   - Read the screen with `claude logs <id>`.
5. **When it's done, HQ:**
   - checks the work
   - copies the files out of the worktree into the main folder, checking hashes
   - commits
   - runs `claude rm <id>`, which also removes the worktree once it has no changes left
6. **If it gets stuck on a prompt,** `claude stop <id>`, fix the brief and relaunch. There's no way to answer the prompt from outside the session.
