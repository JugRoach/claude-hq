# PC job: apply the routing plan (Matt approved 11/17/2026, "apply it")

Run by the Remote control session. Text files and scripts only, no screen takeover. Do the steps in order. Spend nothing outside the existing API credit, create no API keys, change no billing, delete nothing.

## 1. Rotate Remote control first (it is ~908k of 1M context)
- Write a handoff to `HQ\start-here.md`: what's running, what's queued, open jobs, and "next: steps 2-8 of HQ\work\routing-audit\pc-job.md".
- Start the replacement Remote control session the way the current one was started, if you can do it hidden and without Matt. If it needs Matt at the PC, end your turn with exactly one line for HQ: what he has to do (one click or one paste).
- The fresh session reads `HQ\start-here.md`, then carries on from step 2. Old session: stop taking jobs once the new one confirms it's connected.

## 2. Merge the new routing rules
- `git fetch origin claude/project-thread-3a2srp` and merge it into master. It replaces `rules/routing.md` with one task-type table and adds this file.
- If local `rules/routing.md` has uncommitted edits from today's model-split update, keep the new version (it already includes the split) and fold in anything local that it lacks. Commit and push master.

## 3. Check which usage the dispatcher bills (read-only)
- Read `HQ\tools\dispatch-job.ps1` and the environment it passes to `claude -p`.
- Run one tiny Haiku low job with JSON output and report whether it ran on the weekly plan login or on an API key (look for the API key source in the output, or an API key variable in the job's environment). Change nothing.

## 4. Build the lean lane (dispatcher, Opus medium to build, Haiku low to test)
- Run `claude --help` and confirm which of these flags exist: `--bare`, `--strict-mcp-config`, `--mcp-config`, `--tools`, `--allowedTools`, `--setting-sources`, `--disable-slash-commands`, `--system-prompt`. Use only confirmed ones.
- Make `HQ\lean\` with a CLAUDE.md of about 10 lines: who Matt is in one line, the stop-for-yes list, "report model + effort", nothing else. No dates in it, so it stays byte-stable for caching.
- Add a `-Lean` switch to `dispatch-job.ps1`: runs the job from `HQ\lean\` with no connectors (empty MCP config, strict), only the tools the job tag needs, no user settings, plugins or slash commands.
- Add a `-Lane plan|api` switch, but leave it on `plan` and disabled for `api` until Matt picks which API key it uses (HQ will tell you).
- Revert = delete `HQ\lean\` and the two switches.

## 5. Measure
- Re-run the same 4 one-line test prompts from today's model test (Haiku, Sonnet, Opus, Fable) with `-Lean`.
- Today's full-workspace costs: Haiku $0.008, Sonnet $0.18, Opus $0.16, Fable $0.76. Report the lean cost and input tokens for each next to these.

## 6. Job log columns
- Add to each `HQ\jobs\` log entry: department, task type, model, effort, lane, input/output/cached tokens, cost, pass/fail.

## 7. Effort defaults
- In the dispatcher, set effort explicitly on every job (Sonnet defaults to high if unset). Default by tier: Haiku low, Sonnet medium, Opus medium, Fable high, unless the job tag says otherwise.

## 8. Close-out
- Write `PC-and-Tools\log\2026-11-17-routing-plan.md` and rewrite the HQ and PC & Tools `start-here.md`.
- Send HQ one short report: rotation done (or Matt's one step), billing lane found, lean costs vs the old ones, anything that failed.
