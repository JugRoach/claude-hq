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

```powershell
cd "<department folder>"
$env:CLAUDE_CODE_EFFORT_LEVEL = "<low|medium|high|xhigh|max>"
claude --bg --model <haiku|sonnet|opus|fable> "<brief>"
```

- Watch it with `claude agents --json`. Plain `claude agents` refuses to run when its output is piped.
- Read its output with `claude logs <id>`.
- Remove it with `claude rm <id>` once it's done.
