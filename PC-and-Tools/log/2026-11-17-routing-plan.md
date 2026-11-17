# 2026-11-17: routing plan applied (Remote control / Screen Desk, replacement session)

Done:
- Step 2: merged `origin/claude/project-thread-3a2srp` into local master (branch routing.md kept; section 7 added with the dispatcher line, Duet-to-API job list and API priority from the local model-split edit). **Committed locally, not pushed: HQ decides, after the pre-push hook.**
- Step 3: billing. No ANTHROPIC_API_KEY / AUTH_TOKEN in the process, user or machine environment; a Haiku probe reports `apiKeySource: none`, so the dispatcher runs on the **weekly plan login**, not an API key. Do not use `--bare` on the plan lane (it skips the login).
- Step 4: lean lane. `HQ\lean\CLAUDE.md` (7 lines, no dates) + `empty-mcp.json`. `dispatch-job.ps1` got `-Lean`, `-Tools`, `-Lane plan|api` (api refused, exit 2, until HQ names the key), `-Dept`, `-TaskType`. Confirmed flags used: `--strict-mcp-config`, `--mcp-config`, `--tools`, `--setting-sources`, `--disable-slash-commands`, `--append-system-prompt-file`. `--setting-sources project` loads the parent company CLAUDE.md (defeats lean) and `user` loads memory, so lean uses `""` and passes the lean rules as an appended system prompt. Revert: delete `HQ\lean\` and the new switches (backup of old script is in the session scratch).
- Step 5: lean vs full (one-line model-id prompt): Haiku $0.0006 vs $0.008 (~7.0k input tokens); Sonnet $0.018 vs $0.18 (~6.2k); Opus $0.041 vs $0.16 (~6.3k); Fable $0.10 vs $0.76 (~7.7k). All four answered on their own model.
- Step 6: every log now has dept, task type, lane, token lines and a one-line SUMMARY (dept, type, model, effort, lane, tokens, cost, pass/fail).
- Step 7: effort always explicit. If the tag has a model but no effort, tier default is used (Haiku low, Sonnet/Opus medium, Fable high) and logged "(tier default)". A missing model is still refused. (This relaxes the old "no effort = refuse" rule; HQ can undo.)

Known small gap: the log's `folder` line shows the requested folder, not HQ\lean, for lean jobs.
