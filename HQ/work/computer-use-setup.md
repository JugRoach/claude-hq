# Computer use on Matt's PC: what's on, what isn't, and the fewest steps left

_Checked by HQ on 2026-11-16 ~23:10: installed versions, desktop-app settings and logs (read-only), and the current docs (via a docs agent). Nothing was changed on screen._

## What's already working (verified on this PC)

| Piece | State | Evidence |
|---|---|---|
| Claude desktop app | **Installed, running, starts with Windows** | Microsoft Store (MSIX) build **5.11492.5.0**; the `ClaudeStartup` startup task is enabled (state 2) |
| Computer use in the desktop app | **ON, and it has been used** | Preference `chicagoEnabled: true`; app log `chicago_config … "enabled":true`; computer-use screenshots and clicks logged today at 14:35 and 16:15 |
| This PC as a remote device for Claude chats (Claude Duet) | **ON, registered as "jugroach-dt"** | `ant-device-registry.json` holds a device key; the log shows the bridge offering `computer_screenshot`, `computer_left_click`, `computer_type`, `computer_key`, `computer_scroll`, `computer_open_application`, `computer_request_access` and the rest, plus the built-in browser and device file tools. It answered device-info requests at 21:41 and 21:45. |
| Staying reachable | **ON** | `remoteControlStayReachable: true`; `keepAwakeEnabled: true` (keeps the PC awake while a remote job runs) |
| Desktop app Remote Control for the company folder | **ON** | `remote-control-state.json` serves `C:\Claude's Workspace`, `Documents\DayBoard` and `Coppice\coppice`; `ccRemoteControlDefaultEnabled: true` |
| Browser control | **ON** (built-in browser) | `coworkBrowserToolsEnabled: true`, preferred browser `built_in` |

**So Claude Duet can already control this PC's screen and desktop apps,** through the "jugroach-dt" device, whenever the desktop app is running (it starts at login).

## What isn't possible, and why

- **HQ, as it runs now, can't have computer use.** HQ is a Claude Code command-line session (`claude --remote-control "HQ Opus"`, hidden). The docs say plainly: "Computer use in the CLI is not available on Linux or Windows. On Windows, use computer use in Desktop instead." There's no flag, setting or bridge for it.
  - Source: https://code.claude.com/docs/en/computer-use.md
- **Pre-approving apps for unattended runs isn't possible either.** Each app needs "Allow for this session" the first time in a session (30 minutes for Dispatch-started sessions); an unanswered prompt is denied after 10 minutes. That's a safety feature, and it fits Matt's ask-first rule.

## The setup: screen jobs go to a session that has the tools

HQ plans and checks; a computer-use session does the clicking.

1. **HQ writes the screen job** as a file in `HQ\work\screen-jobs\` (steps, a done-check and the deconfliction checks). It estimates the length and follows the "Screen jobs" rule in `CLAUDE.md`: ask Matt first ("quick one if you've got a second to pull over"); never touch a game window; give the screen back fast.
2. **HQ tells Claude Duet, in its reply,** that a screen job is ready and pastes the job text.
3. **Claude Duet** (which has the "jugroach-dt" device tools) asks Matt, runs it with computer use, and replies "done" plus what it saw. HQ logs it.

**Nothing to install, no settings to change. This works from tonight.**

## The fewest steps for Matt

### Step 1: one paste into Claude Duet (once)

Paste this into the Claude Duet chat:

> Standing rule for screen jobs: when HQ says "SCREEN JOB READY", run it on my PC (device jugroach-dt) with computer use, following the steps it gives. Before touching the screen, ask me "quick one if you've got a second to pull over?" (if I'm mid-dungeon I'll say not now). Never click, type into or close a game window (WoW, Skyrim/Nolvus, Cyberpunk, Battle.net), never touch the SIG app, and hand the screen back the moment you're done. Then tell HQ what you did and what you saw.

### Step 2: optional safety net (about 1 minute, once)

In the Claude desktop app: **Settings → This computer → Computer use → Denied apps**. Add World of Warcraft, Battle.net, Skyrim / Nolvus / Vortex, Cyberpunk 2077, and the SIG app window.

Computer use can then never act inside them, even by mistake. (Approval is per app anyway; this makes "never" a hard block.) It's a settings screen only Matt should click through, so HQ hasn't touched it.

### Step 3: optional, later: give HQ its own hands

To have HQ itself hold the tools instead of going through Duet, HQ would run as a desktop-app Code session instead of a hidden terminal.
- **Test,** when Matt has 5 minutes and isn't in a game: in a normal terminal, `cd "C:\Claude's Workspace"` and then `claude --desktop --continue`. This should open this HQ conversation in the desktop app's Code tab, where computer use is documented to work.
- **Trade-offs:** HQ would live in the desktop app's window instead of being fully hidden, and the hidden-CLI autostart would be retired.
- **Not documented** is whether Remote Control from Duet behaves the same there. That's why it's a test, not tonight's default.

## First screen job in the queue

`HQ\work\desktop-projects-pass.md`. It's longer than 15 minutes: renames, archives, the routine pause, two exports and one Drive drag. So under the rule it waits until Matt is free, or gets split into short pieces that are each asked for. When Matt says go, HQ sends it to Duet as "SCREEN JOB READY".
