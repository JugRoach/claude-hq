# Close-out: Day Board restart into layout B (2026-11-16, 21:08)

Done by HQ at Matt's request.

## Restart

- **Stopped both running copies:**
  - one started 13:25 (PIDs 11824 + 40648)
  - one started 15:10 (PIDs 39624 + 8004)
  - Each copy is a `.venv` launcher plus its Python 3.12 process.
- **Profile released:** within 15 s, no WebView2 helper still held `DayBoard\webdata`, so nothing had to be force-stopped.
- **Started one fresh copy** at 21:08:31, the same way the Startup shortcut does (`.venv\Scripts\pythonw.exe app.py`, started in the DayBoard folder).
  - One copy is running now (launcher 27816 + process 37612).
- **Startup log:** no errors. It recorded:
  - `chat dock: Claude Duet docked on the DAY BOARD tab (CHAT_DOCK width 560); tabs: DAY BOARD | DISCORD`
  - `started; ptt=f12 shot=f11 sounds=True`
  - `discord keys: mode=ptt ptt=` mute=` toggle=ctrl+alt+d`
  - `discord loaded; mic gate … open: False`
  - `reply chime watcher installed`
  - `business status sent`
  - `board fit: view 1359x950 -> zoom 1.06`
- **Window:** maximized on the second monitor (1936×1048 at 1598,1432), never minimized.

## Checklist (STAGING.md)

All screenshots were taken with PrintWindow or a screen copy, without focusing or moving anything. They're kept out of git because they show real calendar and chat content.

| Item | Result |
|---|---|
| **Layout B loads** | **Pass.** DAY BOARD \| DISCORD tab bar. Week band with today plus Tue–Fri, from the real Google Calendar. To-do strip. Businesses: One Night Press (Not launched, four "Nothing tracked yet"), Coppice and Game Art Kit with their real lines. Claude Duet chat docked on the right. No brass anywhere, since nothing needs Matt. |
| **Discord tab** | **Pass.** `discord.go`: Discord fills the whole window and DISCORD is the active tab. `discord.go` again returns to DAY BOARD, which re-docks and re-fits (zoom 1.06). |
| **Toasts / banners** | **Pass.** `toast.go` on the DISCORD tab: three TEST banners hang from the DAY BOARD tab label, stacked with "Clear all". Back on DAY BOARD they're hidden, because the chat is on screen. **Matt:** they show again next time DISCORD is open; one "Clear all" removes them. |
| **Resize** | **Pass.** Resized to 1280×820 without activating. The chat shrank to half the width, the band dropped to today + 2 days and the business tiles stacked. Restored to 1936×1048 maximized. The foreground window never changed. |
| **F12** | **Hooked, not live-tested.** F12/F11 are registered and the chat page's watcher is installed. `selftest.go` would send a real transcribed clip into Matt's Claude Duet chat, so it wasn't used. **Matt:** press F12, say something, check it lands in the docked chat. |
| **Backtick** | **Hooked, not live-tested.** Backtick is registered and the Discord mic gate is loaded and closed. `discordtest.go` samples the mic inside Discord (Matt may be in a call), so it wasn't used. **Matt:** tap backtick in a call and check the hot-mic light, then that it mutes itself after he stops talking. |

**No rollback needed:** `CHAT_DOCK.on` stays `true`.

## Also

- Deleted the worker's throwaway Edge profile `%TEMP%\dayboard-layoutB-edge` (279 files, 12.6 MB, not in use), with Matt's OK.
- **Where the duplicate copies came from:** not a double auto-start. The Startup folder has one Day Board shortcut, and the copies started at 13:25 and 15:10, not at boot. Each later launch, by hand or by a restart, ran while an older copy was still up.
