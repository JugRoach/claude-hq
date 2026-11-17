# Routing: picking the model and effort

Only HQ edits this file.

## 1. Overrides (check these first)

- **Do it yourself, without launching a worker,** if the job needs Matt in the loop, or if writing the brief would take longer than doing the job.
- **Money, sends, public posts and deletes wait for Matt's yes,** at any tier.
- **One worker at a time per shared resource.** The screen, the WoW files and the GPU are shared resources.

## 2. Score the job

Score each of these 0, 1 or 2:

| Factor | 0 | 2 |
|---|---|---|
| Stakes | nothing much rides on it | a mistake really costs |
| Ambiguity | the brief is exact | the right answer is unclear |
| Taste | no design, visual or wording judgment | judgment is the whole job |
| Size | a few steps | many steps or files |
| Redo cost | cheap to redo | expensive or slow to redo |
| Checking | easy to verify | only Matt's eye can judge |
| Novelty | done before | never done before |

## 3. Pick the tier from the total

| Total | Model | Effort |
|---|---|---|
| 0–2 | Haiku | low |
| 3–5 | Sonnet | medium |
| 6–8 | Opus | high |
| 9–10 | Opus | xhigh |
| 11–14 | Fable | high |

## 4. Bumps

- **Taste-heavy jobs go to Fable.** If taste scores 2 and the total is 7 or more, use Fable.
- **Failed twice:** go up one tier.
- **A saved template exists for the job:** go down one tier.
- **Fable max** is only for a job Fable high has already missed once.

## 5. How to launch

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
