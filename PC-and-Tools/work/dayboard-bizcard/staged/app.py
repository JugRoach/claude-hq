"""Day Board: two always-on-top windows (Day Board + Claude Duet chat) on the second
monitor, with hold-F12 push-to-talk that types into the chat window from inside the page.

Changes from the 11/13 handoff note:
- The focus-flip fallback is OFF by default (FLIP_FALLBACK), never taps Alt, and only types
  after confirming the chat window really is in front. Otherwise it aborts with an error beep.
- Speech is allowed without a click (WebView2 autoplay flag), so voice replies work after a reboot.
- Windows are placed on the second monitor automatically when BOARD/CHAT are left at 0.
- Trigger files in this folder (probe.go, selftest.go, reload.go, place.go) let Claude run the
  selector probe and the push-to-talk self-test without touching the keyboard.
- The log records events and timings only: never keystrokes and never what you said.

11/13 additions:
- F11 quick-send: screenshot of the active window (the game) goes into the Duet box. Hold F12
  within SHOT_WAIT seconds to send your spoken question with it; otherwise it sends alone.
  F11 is swallowed globally, so no other app (Steam, the Claude app) also reacts to it.
- F12 is a toggle (PTT_MODE "toggle"; "hold" brings back hold-to-talk): press to start recording,
  press again to stop and send. Esc while recording throws it away; Esc is only grabbed then.
- F12 types into whichever text box in the chat is focused (reply boxes included), then sends.
- Reply chime (11/14): one soft two-note chime when Claude's reply lands in the chat window, one per
  5-second burst, never on load or reload. CHIME_ON / CHIME_VOLUME (0-1, default 0.25) in config.json.
- F12 auto-send (11/14): in toggle mode, recording stops and sends by itself after PTT_SILENCE_SECONDS
  (6) with no clear speech, or at PTT_MAX_SECONDS (120) no matter what; both send. The pill counts
  down the last PTT_COUNTDOWN_SECONDS (3). F12 still sends at once, Esc still cancels.
  Clear speech is measured against the room: the first PTT_NOISE_CAL_SECONDS (0.5) set the noise
  floor (it can only fall after that), and speech must be over max(PTT_SILENCE_RMS 120,
  floor x PTT_NOISE_MULT 4) for PTT_SPEECH_MS (200 ms).
- Graphite colours (11/14): THEME in config.json (page, panel, hairline, text, secondary, muted,
  accent) colours the listening pill and the board's listening edge and dot. The board page itself
  carries the same Graphite values in its :root block (and reads an optional db doc meta/theme).
- Day bar sleep window (11/14): SLEEP_SCHEDULE in config.json sets the day bar's wake and lights-out
  times by date (held before the first date and after the last, sliding evenly between). Sent to the
  board page by message along with THEME (see BOARD_CFG_JS).
- Pre-alerts (11/14): the board's Next line turns into a heads-up before each event, with the chime at
  each warning stage (Api.prealert). Rules: PREALERT in config.json, sent to the page with the schedule.
- Routine blocks (11/14): ROUTINES in config.json (start "wake", "wake+N", "lights_out-N", "HH:MM" or
  "after:Name"; minutes; days "daily" or ["Mon",...]; workout true) are drawn on the board timeline and
  count as booked; a real calendar block in the same slot wins. WORKOUT_KEY (Ctrl+Alt+W) marks today's
  workout Done; the page keeps Done per day in its db (collection 'workouts') for the week tally.
- Live motion and business tracker (11/14): the board re-reads the calendar every
  MOTION.calendar_refresh_seconds and animates changes (MOTION.on / ms / glint). business-status.json in
  this folder drives the board's Businesses squares and the approval alert; biz_watch sends it the moment
  it is saved. The board reads the Drive mirror (BUSINESS_DRIVE_FILE_ID) every 60 s and Day Board writes
  it here when it is newer (Api.business_from_drive).
- Listening indicator: soft rising/falling clicks (PTT_SOUNDS), a click-through pill at the top
  centre of the main monitor (pill.py), and a pulsing dot + brick-red edge on the Day Board window.

11/16 layout B (CHAT_DOCK):
- config.json CHAT_DOCK {"on": true, "width": 560} (needs EMBED_TABS) docks the Claude Duet view on the right of the
  DAY BOARD tab, beside the board; the tab bar shows DAY BOARD | DISCORD and DISCORD still covers the whole area. The
  board page is told layout "B" in its config message. Everything that meant "the Claude Duet tab" (opening it, the
  unread mark, where banners hang, "no banner while it's in front") now means the DAY BOARD tab. Off or missing: the
  three tabs exactly as before. Decided at start (restart to switch); reload.go re-applies the width only.
"""
import json, os, re, sys, queue, threading, time, wave, subprocess, ctypes, winsound, logging, base64, math
from ctypes import wintypes

# Day Board's own taskbar identity, so Windows groups its window under dayboard.ico, not python's icon.
# Must run before any window exists. The Start menu and Startup shortcuts carry the same ID.
APP_ID = "Matt.DayBoard"
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
except Exception:
    pass

# Per-monitor DPI awareness so window positions are real screen pixels on both monitors.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

# Let pages speak without a click first (Chromium blocks speech until a click otherwise).
# Keep hidden tabs (a Discord stream while the Day Board tab is in front) from being throttled or backgrounded:
# the three flags below, plus switches that also turn off intensive wake-up throttling and native-window
# occlusion tracking (11/15 stream-frozen-after-tab-switch fix).
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = " ".join([
    "--autoplay-policy=no-user-gesture-required",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-backgrounding-occluded-windows",
    "--disable-features=IntensiveWakeUpThrottling,CalculateNativeWinOcclusion",
])

import numpy as np, sounddevice as sd, keyboard, webview
from webview.menu import Menu, MenuAction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capture
from pill import Pill, set_theme as pill_theme
import pill as pill_mod


def find_root():
    here = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
    for d in (here, os.path.dirname(os.path.dirname(here))):   # dist\Day Board\ -> DayBoard\
        if os.path.exists(os.path.join(d, "config.json")):
            return d
    return here


ROOT = find_root()
logging.basicConfig(filename=os.path.join(ROOT, "dayboard.log"), level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dayboard")


def load_cfg():
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8-sig") as f:
        return json.load(f)


CFG = load_cfg()
WAV = os.path.join(ROOT, "ptt.wav")
OUT = os.path.join(ROOT, "ptt")
RATE = 16000
state = {"rec": False, "busy": False, "frames": [], "stream": None, "voice": CFG["VOICE_ON"],
         "on_top": CFG["ON_TOP"], "hidden": False,
         # F11 quick-send
         "shot_t": 0.0, "shot_gen": 0, "shot_claimed": False, "shot_done": None, "shot_ok": False,
         "with_shot": False, "f11_held": False, "last_ext": None, "shot_names": [],
         # toggle mode: F12 held (ignore key repeat), Esc grabbed only while recording
         "f12_held": False, "esc_remove": None, "esc_held": False, "rec_gen": 0,
         # test hook: the next F12 uses this WAV instead of the mic
         "fake_wav": None}
shot_lock = threading.Lock()
user32 = ctypes.windll.user32
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
for _f in ("IsWindow", "IsWindowVisible", "IsIconic"):
    getattr(user32, _f).argtypes = [wintypes.HWND]
PID = os.getpid()


# ---------- windows and monitors ----------

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]


MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
ENUMWINDOWSPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def monitors():
    out = []

    def cb(h, hdc, r, lp):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(h, ctypes.byref(mi))
        w, m = mi.rcWork, mi.rcMonitor
        out.append({"primary": bool(mi.dwFlags & 1), "x": w.left, "y": w.top, "w": w.right - w.left,
                    "h": w.bottom - w.top, "full_w": m.right - m.left, "full_h": m.bottom - m.top})
        return 1

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    return out


def layout():
    b, c = CFG["BOARD"], CFG["CHAT"]
    if b.get("w") and b.get("h") and c.get("w") and c.get("h"):
        return b, c
    mons = monitors()
    log.info("monitors: %s", json.dumps(mons))
    sec = [m for m in mons if not m["primary"]]
    m = max(sec, key=lambda m: m["w"] * m["h"]) if sec else next(m for m in mons if m["primary"])
    if not sec:  # no second monitor: use the right-hand quarter of the main one
        m = dict(m, x=m["x"] + m["w"] * 3 // 4, w=m["w"] // 4)
    if m["h"] > m["w"] or m["w"] < 1920:   # portrait or narrow: stack top/bottom
        bh = int(m["h"] * 0.6)
        b = {"x": m["x"], "y": m["y"], "w": m["w"], "h": bh}
        c = {"x": m["x"], "y": m["y"] + bh, "w": m["w"], "h": m["h"] - bh}
    else:                                    # wide: side by side
        bw = int(m["w"] * 0.6)
        b = {"x": m["x"], "y": m["y"], "w": bw, "h": m["h"]}
        c = {"x": m["x"] + bw, "y": m["y"], "w": m["w"] - bw, "h": m["h"]}
    log.info("layout board=%s chat=%s", b, c)
    return b, c


def own_window(title):
    """HWND of this process's top-level window with this exact title (0 if none)."""
    found = []

    def cb(hwnd, lp):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == PID:
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if buf.value == title:
                found.append(hwnd)
                return False
        return True

    user32.EnumWindows(ENUMWINDOWSPROC(cb), 0)
    return found[0] if found else 0


def window_title(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def place(startup=False):
    """Put the board, chat and Discord windows on their spots without stealing focus, then
    let apply_z() stack them (pinned unless a prompt is over them). The Day Board window itself is
    only moved at start (and by place.go); after that its size is Matt's - maximized or whatever he
    drags it to - and page loads never resize it (11/15: it used to snap back from maximized)."""
    SWP_NOZORDER, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x0004, 0x0010, 0x0040
    spots = [("Day Board", B)] if startup else []
    if not tabs.get("views"):                  # before / without one-window mode
        if dcfg()["on"]:
            spots.append((DISCORD_TITLE, B))
        spots.append((CLAUDE_TITLE, B))
    for title, r in spots:
        h = own_window(title)
        if h and user32.IsZoomed(h):
            log.info("%s is maximized: left as it is", title)
        elif h:
            user32.SetWindowPos(h, None, r["x"], r["y"], r["w"], r["h"], SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            rc = RECT()
            user32.GetWindowRect(h, ctypes.byref(rc))
            log.info("placed %s at %s,%s %sx%s", title, rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top)
        else:
            log.warning("window not found: %s", title)
    if startup and CFG.get("BOARD_START_MAXIMIZED", True):
        hb = own_window("Day Board")
        if hb and not user32.IsZoomed(hb):
            user32.ShowWindow(hb, 3)                   # SW_MAXIMIZE, on the monitor it was just placed on
    apply_z(raise_=True)


def set_on_top(on):
    state["on_top"] = bool(on)
    apply_z(raise_=True)


def toggle_on_top():
    """Ctrl+Alt+T or the Day Board menu: pin both windows on top, or let other windows cover them."""
    state["on_top"] = not state["on_top"]
    set_on_top(state["on_top"])
    beep(1200 if state["on_top"] else 400, 80)
    log.info("always on top %s", "on" if state["on_top"] else "off")
    try:   # remember the choice for next launch
        cfg = load_cfg()
        cfg["ON_TOP"] = state["on_top"]
        with open(os.path.join(ROOT, "config.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        log.error("could not save ON_TOP: %s", e)


def toggle_hidden():
    """Ctrl+Alt+H or the Day Board menu: hide both windows, or bring them back."""
    SW_HIDE, SW_SHOWNOACTIVATE = 0, 4
    state["hidden"] = not state["hidden"]
    titles = ("Day Board",) if tabs.get("views") else ("Day Board", "Claude Duet", DISCORD_TITLE, CLAUDE_TITLE)
    for title in titles:
        h = own_window(title)
        if h:
            user32.ShowWindow(h, SW_HIDE if state["hidden"] else SW_SHOWNOACTIVATE)
    if not state["hidden"]:
        set_on_top(state["on_top"])
    log.info("windows %s", "hidden" if state["hidden"] else "shown")


# ---------- stacking: never cover a prompt, and the Discord view over the board ----------
# The board and chat are pinned on top (ON_TOP). A pinned window used to sit over Windows and
# Claude access prompts that opened on the same screen. guard_loop() now watches for another
# app's window over ours (the window in front, a dialog, a Claude prompt) and drops the pin until
# it is gone. apply_z() is the one place that decides the order of our three windows.

DISCORD_TITLE = "Discord · Day Board"
CLAUDE_TITLE = "Claude Duet \u00b7 Day Board"      # the Claude Duet tab (claude.ai/messages)


def ccfg():
    return dict({"on": True, "url": "https://claude.ai/messages"}, **(CFG.get("CLAUDE_TAB") or {}))
HWND_TOP, HWND_TOPMOST, HWND_NOTOPMOST = wintypes.HWND(0), wintypes.HWND(-1), wintypes.HWND(-2)
Z_FLAGS = 0x1 | 0x2 | 0x10            # SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE
WS_EX_TOPMOST, WS_EX_TRANSPARENT = 0x8, 0x20
zlock = threading.RLock()
state.update({"discord": False, "tabwin": "today", "yield_to": 0, "d_mute": False})
dwmapi = ctypes.WinDLL("dwmapi")
kernel32 = ctypes.WinDLL("kernel32")
user32.GetWindowLongW.restype = ctypes.c_long
user32.GetWindow.restype = wintypes.HWND
kernel32.OpenProcess.restype = wintypes.HANDLE
PROMPT_PROCS = {"claude.exe", "consent.exe", "credentialuibroker.exe", "applicationframehost.exe"}
NOT_PROMPT_CLASSES = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "NotifyIconOverflowWindow",
                      "#32768", "tooltips_class32", "DayBoardPill", "Windows.UI.Core.CoreWindow",
                      "TopLevelWindowForOverflowXamlIsland", "XamlExplorerHostIslandWindow", "IME", "MSCTFIME UI"}
_proc_names = {}


def dcfg():
    d = dict({"on": True, "url": "https://discord.com/app", "mode": "ptt", "ptt_key": "`", "mute_key": "`",
              "toggle_key": "ctrl+alt+d"}, **(CFG.get("DISCORD") or {}))
    if d.get("mode") not in ("ptt", "voice", "open"):
        d["mode"] = "ptt"
    return d


def proc_name(pid):
    if pid in _proc_names:
        return _proc_names[pid]
    name = ""
    h = kernel32.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
    if h:
        buf, n = ctypes.create_unicode_buffer(520), wintypes.DWORD(520)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            name = os.path.basename(buf.value).lower()
        kernel32.CloseHandle(h)
    if len(_proc_names) > 500:
        _proc_names.clear()
    _proc_names[pid] = name
    return name


def rect_of(h):
    r = RECT()
    user32.GetWindowRect(h, ctypes.byref(r))
    return r


def overlaps(a, b):
    return min(a.right, b.right) - max(a.left, b.left) > 8 and min(a.bottom, b.bottom) - max(a.top, b.top) > 8


def our_rects():
    out = []
    for t in ("Day Board", "Claude Duet", DISCORD_TITLE, CLAUDE_TITLE):
        h = own_window(t)
        if h and user32.IsWindowVisible(h) and not user32.IsIconic(h):
            out.append(rect_of(h))
    return out


def cloaked(h):
    v = ctypes.c_int(0)
    dwmapi.DwmGetWindowAttribute(h, 14, ctypes.byref(v), ctypes.sizeof(v))   # DWMWA_CLOAKED
    return v.value != 0


def prompt_over_us():
    """Another app's window that should be in front of ours: the window Matt (or Windows) put in
    front, a standard dialog, a window owned by another one (a popup/prompt), or a non-maximized
    Claude / UAC / credential window, and it overlaps one of our windows. 0 if none."""
    mine = our_rects()
    if not mine:
        return 0
    fg = user32.GetForegroundWindow()
    found = []

    def cb(h, lp):
        if not user32.IsWindowVisible(h) or user32.IsIconic(h):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == PID:
            return True
        root = user32.GetAncestor(h, 3)                 # GA_ROOTOWNER: WebView2 popups of our own windows
        if root and root != h:
            rp = wintypes.DWORD()
            user32.GetWindowThreadProcessId(root, ctypes.byref(rp))
            if rp.value == PID:
                return True
        cls = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(h, cls, 64)
        if cls.value in NOT_PROMPT_CLASSES:
            return True
        ex = user32.GetWindowLongW(h, -20)
        if ex & WS_EX_TRANSPARENT:
            return True
        r = rect_of(h)
        if r.right - r.left < 60 or r.bottom - r.top < 40 or not any(overlaps(r, m) for m in mine):
            return True
        if cloaked(h):
            return True
        why = None
        if h == fg:
            why = "in front"
        elif cls.value == "#32770":
            why = "dialog"
        elif user32.GetWindow(h, 4):                    # GW_OWNER: a popup owned by another window
            why = "popup"
        elif proc_name(pid.value) in PROMPT_PROCS and not user32.IsZoomed(h):
            why = "prompt"
        if why:
            found.append((h, why, proc_name(pid.value), cls.value))
            return False
        return True

    user32.EnumWindows(ENUMWINDOWSPROC(cb), 0)
    if found:
        state["yield_why"] = found[0][1:]
        return found[0][0]
    return 0


TAB_TITLES = {"today": "Day Board", "discord": DISCORD_TITLE, "claude": CLAUDE_TITLE}


def tab_windows():
    return {k: own_window(t) for k, t in TAB_TITLES.items()}


def tab_windows_ordered():
    if tabs.get("views"):                      # one window: only the Day Board window itself
        return [own_window("Day Board")]
    w = tab_windows()
    act = state.get("tabwin", "today")
    return [w.get(act)] + [h for k, h in w.items() if k != act]


def embed_on():
    return bool(CFG.get("EMBED_TABS", True))


def embed_tabs():
    """ONE window: move the Discord and Claude Duet web views (WinForms WebView2 controls) into the Day
    Board window and hide their own, now empty, windows. One taskbar button, one Alt+Tab entry, and
    resize / move / minimize / maximize are just the Day Board window's. Each page keeps running (a
    Discord call, the Claude Duet chat F12 sends into); a tab switch only changes which view is visible."""
    import System.Windows.Forms as WF
    from System import Action
    main = board.native

    def run():
        views = {"today": main.webview}
        for key, w in (("discord", discord_win()), ("claude", claude_win())):
            if not w:
                continue
            f = w.native
            wv = f.webview
            f.Controls.Remove(wv)
            main.Controls.Add(wv)
            wv.Dock = WF.DockStyle.Fill
            wv.Visible = True                   # never Visible=False: a hidden WebView2 gets backgrounded and a stream freezes
            views[key] = wv
            f.Hide()
        main.webview.Visible = True
        main.webview.BringToFront()            # the fill control docks last, under the tab bar
        tabs["views"] = views
        # every view stays Visible and docked Fill; the front one just covers the others (z-order)
        if dock_cfg()["on"] and "claude" in views:
            try:
                dock_build(main, views)        # CHAT_DOCK: board + Claude Duet side by side on the DAY BOARD tab
            except Exception as e:
                log.exception("chat dock failed, keeping the Claude Duet tab: %s", e)

    main.Invoke(Action(run))
    log.info("one window: %s now inside the Day Board window", ", ".join(k for k in tabs.get("views", {}) if k != "today"))
    if dock_on():
        log.info("chat dock: Claude Duet docked on the DAY BOARD tab (CHAT_DOCK width %s); tabs: DAY BOARD | DISCORD", dock_cfg()["width"])


# ---------- chat dock (11/16, layout B) ----------
# config.json CHAT_DOCK {"on": true, "width": 560}, with EMBED_TABS on. The DAY BOARD tab becomes one panel holding the
# board view (left, fills what's left) and the Claude Duet view (right, `width` logical pixels, never more than half the
# panel), with a 1 px hairline between. DISCORD still covers the whole area, so the chat never changes size on a tab
# switch. Both views stay Visible, as before (covered, never hidden). Decided once at start; if docking fails, the
# Claude Duet view goes back to being its own tab and the page is not told layout B.

def dock_cfg():
    d = dict({"on": False, "width": 560}, **(CFG.get("CHAT_DOCK") or {}))
    try:
        d["width"] = max(240, int(d.get("width") or 560))
    except Exception:
        d["width"] = 560
    d["on"] = bool(d.get("on")) and embed_on()
    return d


def dock_on():
    """True once the Claude Duet view really sits docked on the DAY BOARD tab."""
    return bool(tabs.get("dock"))


def chat_in_view():
    """The Claude Duet chat is the tab in front: its own tab, or (docked) the DAY BOARD tab. Minimized / hidden is
    checked separately where it matters, as before."""
    t = state.get("tabwin", "today")
    return t == "claude" or (t == "today" and dock_on())


def ui_post(fn):
    """Run fn on the UI thread without waiting for it."""
    try:
        from System import Action
        board.native.BeginInvoke(Action(fn))
    except Exception as e:
        log.error("ui post: %s", e)


def dock_build(main, views):
    """UI thread, from embed_tabs. On any error both views go back to where embed_tabs put them (three tabs)."""
    import System.Windows.Forms as WF
    from System import EventHandler
    from System.Drawing import ColorTranslator
    th = theme()
    bwv, cwv = views["today"], views["claude"]
    panel = WF.Panel()
    panel.Name = "dbDayTab"
    panel.BackColor = ColorTranslator.FromHtml(th["page"])
    panel.Dock = WF.DockStyle.Fill
    edge = WF.Panel()
    edge.Name = "dbDockEdge"
    edge.BackColor = ColorTranslator.FromHtml(th["hairline"])
    edge.Dock = WF.DockStyle.Right
    edge.Width = 1
    try:
        main.Controls.Add(panel)
        main.Controls.Remove(cwv)
        main.Controls.Remove(bwv)
        bwv.Dock = WF.DockStyle.Fill
        cwv.Dock = WF.DockStyle.Right
        panel.Controls.Add(bwv)
        panel.Controls.Add(edge)
        panel.Controls.Add(cwv)
        edge.SendToBack()
        cwv.SendToBack()                       # docked first: the right-hand strip, then the hairline beside it
        bwv.BringToFront()                     # docked last: fills what's left
        bwv.Visible = cwv.Visible = True
        panel.BringToFront()                   # the DAY BOARD tab in front, as at start
        tabs["dock"] = {"panel": panel, "board": bwv, "chat": cwv, "edge": edge}
        dock_layout()
        panel.SizeChanged += EventHandler(dock_layout)
    except Exception:
        tabs.pop("dock", None)
        for wv in (bwv, cwv):
            try:
                if panel.Controls.Contains(wv):
                    panel.Controls.Remove(wv)
                if not main.Controls.Contains(wv):
                    main.Controls.Add(wv)
                wv.Dock = WF.DockStyle.Fill
                wv.Visible = True
            except Exception:
                pass
        try:
            main.Controls.Remove(panel)
        except Exception:
            pass
        bwv.BringToFront()
        raise
    views.pop("claude")
    views["today"] = panel                     # the DAY BOARD tab is the panel now; DISCORD stays as it was


def dock_layout(*a):
    """UI thread: keep the docked chat at CHAT_DOCK width (logical pixels, scaled for DPI), never more than half the
    panel, so the board keeps the larger share when the window is narrow. Runs on every panel resize."""
    d = tabs.get("dock")
    if not d:
        return
    try:
        pw = d["panel"].ClientSize.Width
        if pw < 100:                           # minimized or not laid out yet: keep the last width
            return
        dpi = max(1.0, board.native.DeviceDpi / 96.0)
        w = max(1, min(int(dock_cfg()["width"] * dpi), pw // 2))
        if d["chat"].Width != w:
            d["chat"].Width = w
    except Exception as e:
        log.error("chat dock layout: %s", e)


def show_tab(key):
    views = tabs.get("views")
    if key == "claude" and dock_on():
        key = "today"                          # CHAT_DOCK: the chat lives on the DAY BOARD tab
    if views:                                  # one-window mode: swap the visible view, nothing else
        if key not in views:
            log.warning("tab not available: %s", key)
            return False
        from System import Action
        import System.Windows.Forms as WF

        def run():
            for k, v in views.items():
                if k == key:
                    v.Visible = True
                    v.BringToFront()               # others stay Visible, just covered (keeps Discord streaming)
                    # a view hidden during a resize keeps its old size (WinForms skips hidden docked
                    # controls): re-dock it so it fills the window as it is now, then re-fit (11/15)
                    try:
                        d = v.Dock
                        v.Dock = getattr(WF.DockStyle, "None")
                        v.Dock = d
                        board.native.PerformLayout()
                    except Exception as e:
                        log.error("tab re-dock: %s", e)
                    if k == "today" and dock_on():
                        dock_layout()
                    if k == "today" and tabs.get("fit"):
                        tabs["fit"]()
                    try:
                        # docked: the DAY BOARD tab stands in for the Claude Duet tab, so typing goes to the chat
                        (tabs["dock"]["chat"] if (k == "today" and dock_on()) else v).Focus()
                    except Exception:
                        pass
                else:
                    v.Visible = True                # covered, not hidden: no throttling/backgrounding of the page

        board.native.Invoke(Action(run))
        state["tabwin"], state["discord"] = key, key == "discord"
        if key == "today":
            nudge_clear()
        update_tabbars()
        push_board_cfg("tab " + key)
        log.info("tab shown: %s", key)
        return True
    return show_tab_windows(key)


def show_tab_windows(key):
    """Bring one tab's window to the front over the others (Day Board, Discord, Claude Duet all sit
    on the same rectangle). Nothing is hidden, so a Discord call keeps going behind."""
    w = tab_windows()
    h = w.get(key)
    if not h:
        log.warning("tab window not found: %s", key)
        return False
    state["tabwin"] = key
    state["discord"] = key == "discord"
    if key != "today" and not user32.IsZoomed(h):
        user32.SetWindowPos(h, HWND_TOP, B["x"], B["y"], B["w"], B["h"], 0x40)
    user32.SetForegroundWindow(h)
    apply_z(raise_=True)
    update_tabbars()
    push_board_cfg("tab " + key)
    log.info("tab shown: %s", key)
    return True


def group_sync():
    """Make the three tab windows act as one: when the front one is minimized, maximized or
    restored, the other two follow; clicking another tab window's taskbar entry makes it the tab."""
    if state.get("hidden") or not CFG.get("TAB_GROUP_SYNC", False) or tabs.get("views"):
        return                                # off: windows keep their own minimize/maximize (as before)
    w = tab_windows()
    fg = user32.GetForegroundWindow()
    newly, state["last_fg"] = fg != state.get("last_fg"), fg      # only a window that just came to the front
    if time.time() < state.get("sync_quiet", 0):
        newly = False                         # focus moved because of our own sync: not a tab switch
    for k, h in w.items():
        if newly and h and h == fg and k != state.get("tabwin") and not user32.IsIconic(h):
            state["tabwin"], state["discord"] = k, k == "discord"
            apply_z(raise_=True)
            update_tabbars()
            log.info("tab shown: %s (from the taskbar)", k)
    act = w.get(state.get("tabwin", "today"))
    if not act:
        return
    a_min, a_max = bool(user32.IsIconic(act)), bool(user32.IsZoomed(act))
    changed = False
    for k, h in w.items():
        if not h or h == act:
            continue
        o_min, o_max = bool(user32.IsIconic(h)), bool(user32.IsZoomed(h))
        if a_min and not o_min:
            user32.ShowWindow(h, 7)                     # SW_SHOWMINNOACTIVE
            changed = True
        elif not a_min and o_min:
            user32.ShowWindow(h, 3 if a_max else 4)     # maximize or restore without stealing focus
            changed = True
        elif not a_min and a_max != o_max:
            user32.ShowWindow(h, 3 if a_max else 9)     # SW_MAXIMIZE / SW_RESTORE
            changed = True
    if changed:
        state["sync_quiet"] = time.time() + 1.0
    if changed and not a_min:
        user32.SetForegroundWindow(act)
        state["last_fg"] = act
        apply_z(raise_=True)
    if changed:
        log.info("tab windows follow the front one: %s", "minimized" if a_min else ("maximized" if a_max else "restored"))


def apply_z(raise_=False):
    """Order: Discord above the board while it's shown, else tucked right under it. Pinned on top
    when ON_TOP is on, unless a prompt is over us; then all three sit just below the prompt."""
    with zlock:
        hc = own_window("Claude Duet")
        stack = [h for h in tab_windows_ordered() if h]   # the three tab windows, active tab first
        allw = stack + ([hc] if hc else [])
        y = state["yield_to"]
        if y and user32.IsWindow(y):
            for h in allw:
                user32.SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, Z_FLAGS)
            if not user32.GetWindowLongW(y, -20) & WS_EX_TOPMOST:
                after = y
                for h in allw:
                    user32.SetWindowPos(h, wintypes.HWND(after), 0, 0, 0, 0, Z_FLAGS)
                    after = h
            return
        if state["on_top"]:
            for h in ([hc] if hc else []) + list(reversed(stack)):
                user32.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, Z_FLAGS)
        else:
            for h in allw:
                user32.SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, Z_FLAGS)
            if raise_:
                for h in ([hc] if hc else []) + list(reversed(stack)):
                    user32.SetWindowPos(h, HWND_TOP, 0, 0, 0, 0, Z_FLAGS)
            else:
                for upper, lower in zip(stack, stack[1:]):
                    user32.SetWindowPos(lower, upper, 0, 0, 0, 0, Z_FLAGS)


def guard_loop():
    while True:
        time.sleep(0.3)
        try:
            if state.get("hidden"):
                continue
            group_sync()
            y = prompt_over_us()
            if y != state["yield_to"]:
                state["yield_to"] = y
                if y:
                    log.info("stepping back for %s (%s)", window_title(y)[:60] or "(untitled)", state.get("yield_why"))
                else:
                    log.info("prompt gone, back on top")
                apply_z()
        except Exception as e:
            log.error("guard: %s", e)
            time.sleep(2)


# ---------- WebView2 hardening: dark while loading, reload a crashed page, Discord mic only ----------

def webview_hook(win, core):
    """Runs once per window on the UI thread, right after WebView2 is ready and before the first page."""
    from Microsoft.Web.WebView2.Core import CoreWebView2PermissionState
    name = win.title

    def failed(sender, args):
        kind = str(args.ProcessFailedKind)
        log.warning("%s: page process failed (%s)", name, kind)
        if "Browser" in kind:
            threading.Timer(2.0, restart).start()
        elif "Render" in kind or "Unresponsive" in kind:
            try:
                sender.Reload()
                log.info("%s: reloaded after %s", name, kind)
            except Exception as e:
                log.error("%s: reload failed: %s", name, e)

    def permission(sender, args):
        try:
            host = (re.match(r"^[a-z]+://([^/:]+)", str(args.Uri) or "") or [None, ""])[1].lower()
            kind = str(args.PermissionKind)
            ok = (host == "discord.com" or host.endswith(".discord.com")) and kind in ("Microphone", "Camera")
            if ok:
                args.State = CoreWebView2PermissionState.Allow
            log.info("%s: %s asked for %s -> %s", name, host, kind, "allowed" if ok else "Windows/WebView prompt")
        except Exception as e:
            log.error("%s: permission handler: %s", name, e)

    core.ProcessFailed += failed
    core.PermissionRequested += permission
    if name == DISCORD_TITLE:
        core.AddScriptToExecuteOnDocumentCreatedAsync(discord_script())
    log.info("%s: WebView2 hooks on", name)


def install_webview_hooks():
    from webview.platforms import edgechromium as edge
    orig = edge.EdgeChrome.on_webview_ready

    def ready(self, sender, args):
        try:
            if args.IsSuccess:
                webview_hook(self.pywebview_window, sender.CoreWebView2)
        except Exception as e:
            log.exception("webview hooks: %s", e)
        return orig(self, sender, args)

    edge.EdgeChrome.on_webview_ready = ready


# ---------- Discord view ----------
# discord.com/app in its own window over the board (Discord refuses iframes). The page script
# gates the microphone at the source: every audio track Discord gets from getUserMedia (and its
# clones) only carries sound while the gate is open, so push-to-talk works from any app,
# WoW included. Discord itself stays on Voice Activity.

DISCORD_JS = r"""
(function(mode){
  if (window.__dbGate) return;
  const desc = Object.getOwnPropertyDescriptor(MediaStreamTrack.prototype, 'enabled');
  const G = window.__dbGate = {mode: mode, held: false, muted: false, tracks: new Set(),
    open() { return G.mode === 'ptt' ? G.held : G.mode === 'voice' ? !G.muted : true; },
    push(t) { try { desc.set.call(t, !!t.__dbWant && G.open()); } catch (e) {} },
    add(t) {
      if (!t || t.kind !== 'audio' || G.tracks.has(t)) return;
      t.__dbWant = desc.get.call(t);
      Object.defineProperty(t, 'enabled', {configurable: true,
        get() { return t.__dbWant; }, set(v) { t.__dbWant = !!v; G.push(t); }});
      G.tracks.add(t); t.addEventListener('ended', () => G.tracks.delete(t)); G.push(t);
    },
    set(o) { for (const k of ['mode', 'held', 'muted']) if (o && k in o) G[k] = o[k];
      G.tracks.forEach(G.push); return G.state(); },
    state() { return {mode: G.mode, held: G.held, muted: G.muted, open: G.open(),
      tracks: [...G.tracks].filter(t => t.readyState === 'live').length}; }
  };
  const md = navigator.mediaDevices;
  if (md && md.getUserMedia) {
    const gum = md.getUserMedia.bind(md);
    md.getUserMedia = function(c) { return gum(c).then(s => { try { s.getAudioTracks().forEach(G.add); } catch (e) {} return s; }); };
  }
  const clone = MediaStreamTrack.prototype.clone;
  MediaStreamTrack.prototype.clone = function() { const c = clone.call(this); if (G.tracks.has(this)) G.add(c); return c; };
})(__MODE__)
"""


def discord_script():
    return DISCORD_JS.replace("__MODE__", json.dumps(dcfg()["mode"]))


def claude_win():
    return next((w for w in webview.windows if w.title == CLAUDE_TITLE), None)


def discord_win():
    return next((w for w in webview.windows if w.title == DISCORD_TITLE), None)


def discord_gate(o):
    w = discord_win()
    if not w:
        return None
    try:
        return w.evaluate_js("window.__dbGate ? window.__dbGate.set(%s) : 'nogate'" % json.dumps(o))
    except Exception as e:
        log.error("discord gate: %s", e)
        return None


def discord_show(on=None):
    """Discord tab on (on) or back to the Day Board (off); Ctrl+Alt+D toggles. Never hides Discord,
    so a call and its sound keep going while another tab is in front."""
    on = (state.get("tabwin") != "discord") if on is None else bool(on)
    return show_tab("discord" if on else "today")


DISCORD_EXTRA = os.path.join(ROOT, "discord_extra.js")


def discord_extra(why=""):
    """Run discord_extra.js (Day Board's own tweaks to Discord's page, e.g. hiding non-video tiles)
    inside the Discord window. Runs on every Discord page load and on every config reload, so it
    can be changed live without a restart. The script must be safe to run more than once."""
    w = discord_win()
    if not w or not os.path.exists(DISCORD_EXTRA):
        return
    try:
        r = w.evaluate_js(open(DISCORD_EXTRA, encoding="utf-8").read())
        log.info("discord extra (%s): %s", why, r)
    except Exception as e:
        log.error("discord extra: %s", e)


def on_discord_loaded():
    state["discord_hwnd"] = own_window(DISCORD_TITLE)
    threading.Timer(1.5, discord_extra, args=("page loaded",)).start()
    d = dcfg()
    r = discord_gate({"mode": d["mode"], "held": False, "muted": state["d_mute"]})
    if r == "nogate":
        w = discord_win()
        r = w.evaluate_js(discord_script()) if w else None
        r = discord_gate({"mode": d["mode"], "held": False, "muted": state["d_mute"]})
    log.info("discord loaded; mic gate %s", r)


dq = queue.Queue()


def discord_key_hook(e):
    """Runs inside the Windows keyboard hook, like F12: the key is swallowed (returning False
    keeps it from reaching Discord, WoW or any other app) and only drives the mic gate."""
    dq.put(("key", e.event_type))
    return False


def discord_live(on, why=""):
    """Open or close the Discord mic gate, with the pill as a small live/muted indicator."""
    state["d_live"] = on
    if not on:
        state["d_auto"] = False
    discord_gate({"held": on})
    log.info("discord mic %s%s", "live" if on else "muted", (" (%s)" % why) if why else "")


class SpeechTest:
    """The same speech test F12 uses (on_audio): the first PTT_NOISE_CAL_SECONDS set the room's
    noise floor (20th percentile), the floor can only fall afterwards, and speech is a level above
    max(PTT_SILENCE_RMS, floor x PTT_NOISE_MULT) for PTT_SPEECH_MS in a row."""
    def __init__(self):
        self.t, self.cal, self.recent, self.floor, self.thr, self.loud = 0.0, [], [], None, None, 0.0
        self.last_voice = None                    # set only by Matt's own speech

    def feed(self, block):
        ms = 1000.0 * len(block) / RATE
        rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))
        self.t += ms
        self.recent.append(rms)
        mult, low = CFG.get("PTT_NOISE_MULT", 4.0), CFG.get("PTT_SILENCE_RMS", 120)
        skip = listen_floor_delay_ms()
        if self.t <= skip:                        # speakers still turning down: not used for the floor
            self.recent.clear()
        elif self.t <= skip + 1000.0 * CFG.get("PTT_NOISE_CAL_SECONDS", 0.5):
            self.cal.append(rms)                  # measuring the room
        else:
            if self.floor is None:
                self.floor = float(np.percentile(self.cal, 20)) if self.cal else 0.0
                self.thr = max(low, self.floor * mult)
                self.recent.clear()
            if len(self.recent) >= int(1000 / ms):
                m = float(np.percentile(self.recent, 20))
                self.recent.clear()
                if m < self.floor:
                    self.floor, self.thr = m, max(low, m * mult)
        # speech counts from the first block (plain minimum threshold until the room is measured)
        if rms > (self.thr if self.thr is not None else low):
            self.loud += ms
            if self.loud >= CFG.get("PTT_SPEECH_MS", 200):
                self.last_voice = time.time()
        else:
            self.loud = max(0.0, self.loud - ms)


def discord_auto_watch(gen):
    """After a backtick press: Discord stays hot until LISTEN quiet_seconds pass with no clear
    speech, or LISTEN max_seconds in all - the same rule and numbers as F12 for Claude. While the
    key is held, and right after it is pressed again, counts as talking (the quiet clock restarts)."""
    if not listen_auto_stop():
        return                                         # ` keeps the mic live until tapped again
    quiet, cap = listen_cfg()
    started = state.get("d_down") or time.time()      # the clock starts at the key press
    st = SpeechTest()
    try:
        with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=RATE // 20,
                            callback=lambda i, f, t, s: st.feed(i[:, 0])):
            grace, wait = listen_grace(), listen_voice_wait()
            while state.get("d_auto") and state.get("d_gen") == gen:
                now = time.time()
                if state.get("d_held") or state.get("d_again", 0.0) > started:
                    st.last_voice = max(st.last_voice or 0.0, now if state.get("d_held") else state["d_again"])
                el = now - started
                if el >= cap:
                    discord_live(False, "hit %.0f s max" % cap)
                    return
                if el >= grace:                   # never auto-stop in the first start_grace_seconds
                    if st.last_voice is None:
                        if el >= wait:            # waited voice_wait_seconds for his voice
                            discord_live(False, "none of your speech in the first %.0f s" % wait)
                            return
                    elif now - st.last_voice >= quiet:
                        discord_live(False, "%.0f s quiet after your speech" % quiet)
                        return
                time.sleep(0.05)
    except Exception as e:
        log.error("discord auto-off: %s", e)
        if state.get("d_auto") and state.get("d_gen") == gen:
            discord_live(False, "mic watch failed")


def discord_worker():
    """` (DISCORD.ptt_key), swallowed like F12 (11/15 evening, Matt: "press once, talk, it turns
    itself off when I'm done"):
    press -> mic live at once; it mutes itself after LISTEN quiet_seconds with no speech from you
             (or max_seconds in all). Hold length doesn't matter (held counts as talking).
    press again while live -> stays live (the quiet clock restarts); a press never mutes.
    Key repeat is ignored; a key-up that Windows lost can't swallow the next press."""
    held, last_down = False, 0.0
    state.update({"d_live": False, "d_auto": False, "d_gen": 0, "d_down": 0.0, "d_held": False, "d_again": 0.0})
    while True:
        kind, ev = dq.get()
        try:
            if kind == "key":
                down = ev == "down"
                now = time.time()
                if down:
                    repeat = held and now - last_down < 1.0    # repeats come every ~30 ms while held
                    last_down = now
                    if repeat:
                        continue
                elif not held:
                    continue                 # stray key-up
                held = down
                state["d_held"] = down
                mode = dcfg()["mode"]
                if mode == "voice":
                    if down:
                        dq.put(("mute", None))
                    continue
                if mode != "ptt":
                    continue
                if not down:
                    continue                 # release changes nothing; the watch mutes after the quiet spell
                if state["d_live"] and state["d_auto"]:
                    if not listen_auto_stop():
                        state["d_gen"] += 1
                        discord_live(False, "pressed again")   # only with LISTEN auto_stop false
                    else:
                        state["d_again"] = now
                        log.info("discord mic stays live (pressed again; quiet clock restarted)")
                    continue
                state["d_down"] = now
                state["d_gen"] += 1
                discord_live(True, "key down")
                state["d_auto"] = True
                threading.Thread(target=discord_auto_watch, args=(state["d_gen"],), daemon=True).start()
            elif kind == "mute":
                # open-mic mode: ` taps mute/unmute. No beep (it would go out over the speakers);
                # the pill stays up while muted and flashes "live" on unmute.
                state["d_mute"] = not state["d_mute"]
                discord_gate({"muted": state["d_mute"]})
                log.info("discord mic %s", "muted" if state["d_mute"] else "open")
        except Exception as e:
            log.error("discord key: %s", e)


def discord_keys():
    d = dcfg()
    if not d["on"]:
        return
    taken = {str(CFG.get(k, "")).lower() for k in ("PTT_KEY", "SHOT_KEY")}
    key = d.get("ptt_key") if d["mode"] == "ptt" else d.get("mute_key") if d["mode"] == "voice" else None
    if key:
        if str(key).lower() in taken:
            log.error("Discord key %s clashes with Day Board's own keys; not hooked", key)
        else:
            keyboard.hook_key(key, discord_key_hook, suppress=True)
    if d.get("toggle_key"):
        keyboard.add_hotkey(d["toggle_key"], lambda: threading.Thread(target=discord_show, daemon=True).start())
    log.info("discord keys: mode=%s ptt=%s mute=%s toggle=%s", d["mode"], d.get("ptt_key"), d.get("mute_key"), d.get("toggle_key"))


DISCORD_TEST_JS = r"""
(function(){
  window.__dbTest = {status: 'starting'};
  navigator.mediaDevices.getUserMedia({audio: true}).then(s => {
    const t = s.getAudioTracks()[0]; let pk = 0;
    const reader = new MediaStreamTrackProcessor({track: t}).readable.getReader();
    (async () => { for (;;) { const r = await reader.read(); if (r.done) break; const f = r.value;
      const a = new Float32Array(f.numberOfFrames); f.copyTo(a, {planeIndex: 0, format: 'f32-planar'}); f.close();
      for (let i = 0; i < a.length; i++) { const v = Math.abs(a[i]); if (v > pk) pk = v; } } })();
    window.__dbTest = {status: 'ok', label: t.label, take() { const p = pk; pk = 0; return p; },
      stop() { s.getTracks().forEach(x => x.stop()); }};
  }).catch(e => { window.__dbTest = {status: 'error', error: String(e)}; });
  try { const ac = new AudioContext(); window.__dbPlay = ac.state; setTimeout(() => { window.__dbPlay2 = ac.state; ac.close(); }, 800); } catch (e) { window.__dbPlay = String(e); }
  return 'started';
})()
"""


def discord_selftest():
    """discordtest.go: mic permission, the gate and the push-to-talk key, measured inside Discord.
    Samples the gated mic every 0.2 s for DISCORD_TEST_SECONDS (default 6) into discordtest.json."""
    w = discord_win()
    out = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "samples": []}
    try:
        out["start"] = w.evaluate_js(DISCORD_TEST_JS)
        for _ in range(25):
            time.sleep(0.2)
            st = w.evaluate_js("window.__dbTest && window.__dbTest.status")
            if st in ("ok", "error"):
                break
        out["status"] = st
        out["label"] = w.evaluate_js("window.__dbTest && (window.__dbTest.label || window.__dbTest.error)")
        if st == "ok":
            w.evaluate_js("window.__dbTest.take()")
            t0 = time.time()
            while time.time() - t0 < float(CFG.get("DISCORD_TEST_SECONDS", 6)):
                time.sleep(0.2)
                g = w.evaluate_js("window.__dbGate.state()")
                pk = w.evaluate_js("window.__dbTest.take()")
                out["samples"].append([round(time.time() - t0, 1), g.get("open"), round(float(pk or 0), 5)])
            w.evaluate_js("window.__dbTest.stop()")
        out["autoplay"] = w.evaluate_js("[window.__dbPlay || 'pending', window.__dbPlay2 || 'pending']")
        out["gate"] = w.evaluate_js("window.__dbGate.state()")
    except Exception as e:
        out["error"] = str(e)
    with open(os.path.join(ROOT, "discordtest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log.info("discord self-test: %s, %s samples", out.get("status"), len(out["samples"]))


# ---------- one tab bar: Day Board | Focus | Discord ----------
# A native strip docked at the top of the Day Board window AND the Discord window (same size,
# same spot, since both windows share one rectangle), so it never moves between views and no web
# page can cover it. Quiet Villain colours from theme(); the active tab gets the brass underline.

# 11/16 CHAT_DOCK: the CLAUDE DUET label is built as always but hidden while the chat is docked (paint()), so the bar
# reads DAY BOARD | DISCORD; if docking fails at start it simply stays visible.
TABS = [("today", "Day Board"), ("discord", "Discord"), ("claude", "Claude Duet")]
TAB_W, TAB_H, TAB_GAP, TAB_LEFT = 150, 34, 4, 12
tabs = {"view": "today", "focus": "", "bars": {}}


def tab_text(key):
    label = dict(TABS)[key]
    if key == "focus" and tabs["focus"]:
        label = "Focus · " + tabs["focus"]
    return "   ".join(" ".join(w) for w in label.upper().split(" "))


def tab_active():
    return state.get("tabwin", "today")


def tab_click(key):
    try:
        show_tab(key)
    except Exception as e:
        log.error("tab %s: %s", key, e)


def build_tabbar(win):
    import System.Windows.Forms as WF
    from System import Action
    from System.Drawing import Color, Font, FontStyle, Size, Point, ContentAlignment, GraphicsUnit

    th = theme()
    col = lambda hx: Color.FromArgb(255, int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16))
    C_PAGE, C_PANEL, C_LINE = col(th["page"]), col(th["panel"]), col(th["hairline"])
    C_TEXT, C_SEC, C_ACC = col(th["text"]), col(th["secondary"]), col(th["accent"])

    def make():
        form = win.native
        font = Font("Bahnschrift SemiBold SemiConden", 10.5, FontStyle.Regular, GraphicsUnit.Point)
        if font.Name != "Bahnschrift SemiBold SemiConden":
            font = Font("Bahnschrift", 10.5, FontStyle.Bold, GraphicsUnit.Point)
        bar = WF.Panel()
        bar.Name = "dbTabs"
        bar.Dock = WF.DockStyle.Top
        bar.Height = TAB_H + 1
        bar.BackColor = C_PAGE
        line = WF.Panel()
        line.Dock = WF.DockStyle.Bottom
        line.Height = 1
        line.BackColor = C_LINE
        bar.Controls.Add(line)
        items = {}
        for i, (key, _) in enumerate(TABS):
            lab = WF.Label()
            lab.AutoSize = False
            lab.AutoEllipsis = True
            lab.Size = Size(TAB_W, TAB_H - 3)
            lab.Location = Point(TAB_LEFT + i * (TAB_W + TAB_GAP), 0)
            lab.TextAlign = ContentAlignment.MiddleCenter
            lab.Font = font
            lab.Cursor = WF.Cursors.Hand
            lab.Text = tab_text(key)
            under = WF.Panel()
            under.Size = Size(TAB_W, 3)
            under.Location = Point(TAB_LEFT + i * (TAB_W + TAB_GAP), TAB_H - 3)

            def click(s, e, k=key):
                threading.Thread(target=tab_click, args=(k,), daemon=True).start()

            def enter(s, e, k=key):
                if k != tab_active():
                    s.ForeColor = C_TEXT

            def leave(s, e, k=key):
                if k != tab_active():
                    s.ForeColor = C_SEC

            lab.Click += click
            lab.MouseEnter += enter
            lab.MouseLeave += leave
            bar.Controls.Add(lab)
            bar.Controls.Add(under)
            items[key] = (lab, under)
        if win is board:
            build_nudge_ui(bar, items, font, (C_PANEL, C_PAGE, C_TEXT, C_SEC, C_ACC))
        # mic status at the right end of the bar: Discord fixed at the edge, Claude just left of it
        status = {}
        bar.Width = form.ClientSize.Width      # size the bar first so right-anchored labels sit at its edge
        for key, w, right in (("claude", 200, 12), ("disc", 200, 12 + 200 + 8)):
            st = WF.Label()
            st.AutoSize = False
            st.Size = Size(w, TAB_H - 3)
            st.Location = Point(form.ClientSize.Width - right - w, 0)
            st.Anchor = WF.AnchorStyles.Top | WF.AnchorStyles.Right
            st.TextAlign = ContentAlignment.MiddleRight
            st.Font = font
            st.BackColor = C_PAGE
            bar.Controls.Add(st)
            status[key] = st
        items["_status"] = status
        for c in form.Controls:              # pywebview's menu strip: dark to match
            if isinstance(c, WF.MenuStrip):
                c.BackColor, c.ForeColor = C_PAGE, C_SEC
        form.Controls.Add(bar)
        bar.SendToBack()                      # docks before the page, which then fills the rest
        tabs["bars"][win.title] = (form, items, (C_PANEL, C_PAGE, C_TEXT, C_SEC, C_ACC))
        paint(win.title)

    win.native.Invoke(Action(make))


def paint(title):
    form, items, (C_PANEL, C_PAGE, C_TEXT, C_SEC, C_ACC) = tabs["bars"][title]
    act = tab_active()
    st = items.get("_status")
    if st:
        from System.Drawing import Color
        acc, grey = C_ACC, Color.FromArgb(255, 107, 103, 96)
        disc, claude = hud.get("disc"), hud.get("claude")
        st["disc"].Text = ("●  " + spaced("DISCORD HOT MIC")) if disc == "live" else ("○  " + spaced("DISCORD MUTED")) if disc else ""
        st["disc"].ForeColor = acc if disc == "live" else grey
        st["claude"].Text = ("●  " + spaced("CLAUDE HOT MIC")) if claude else ("○  " + spaced("CLAUDE MUTED"))
        st["claude"].ForeColor = acc if claude else grey
    dock, shown = dock_on(), 0
    for key, val in items.items():
        if key == "_status":
            continue
        lab, under = val
        on = key == act
        vis = not (dock and key == "claude")   # CHAT_DOCK: DAY BOARD | DISCORD only (the chat is on DAY BOARD)
        lab.Visible = under.Visible = vis      # (set every time: Visible reads False while the window is hidden)
        shown += 1 if vis else 0
        lab.Text = tab_text(key)
        lab.BackColor = C_PANEL if on else C_PAGE
        lab.ForeColor = C_TEXT if on else C_SEC
        under.BackColor = ((C_TEXT if dock else C_ACC) if on else C_PAGE)   # docked (layout B): cream, as in the mockup
    N = tabs.get("nudge")
    if N and title == "Day Board":                # the nudge toast slides out just right of the last tab shown
        x = TAB_LEFT + shown * (TAB_W + TAB_GAP) + 8
        if N["toast"].Left != x:
            N["toast"].Left = N["edge"].Left = x


def update_tabbars():
    from System import Action
    for title, (form, items, _) in list(tabs["bars"].items()):
        try:
            form.Invoke(Action(lambda t=title: paint(t)))
        except Exception as e:
            log.error("tab bar %s: %s", title, e)


def ncfg():
    return dict({"on": True, "lead_minutes": 10, "toast_seconds": 6}, **(CFG.get("NUDGE") or {}))


def build_nudge_ui(bar, items, font, colours):
    """Event nudges for when another tab (Discord, Claude Duet) is in front: a small brass dot on the
    DAY BOARD tab label (pulsing once the event starts; it stays until the Day Board tab is opened) and a
    quiet toast that slides out in the tab bar, top left, then slides back. Inside the Day Board window
    only: no sound, no focus change, nothing over other windows. Runs on the UI thread."""
    import System.Windows.Forms as WF
    from System.Drawing import Color, Font, FontStyle, GraphicsUnit, Size, Point, ContentAlignment, Region
    from System.Drawing.Drawing2D import GraphicsPath
    C_PANEL, C_PAGE, C_TEXT, C_SEC, C_ACC = colours
    dim = Color.FromArgb(255, int(C_ACC.R * .45 + C_PAGE.R * .55), int(C_ACC.G * .45 + C_PAGE.G * .55), int(C_ACC.B * .45 + C_PAGE.B * .55))
    today_lab = items["today"][0]
    dot = WF.Panel()
    dot.Size = Size(8, 8)
    dot.Location = Point(TAB_W - 18, 8)
    dot.BackColor = C_ACC
    path = GraphicsPath()
    path.AddEllipse(0, 0, 8, 8)
    dot.Region = Region(path)
    dot.Visible = False
    today_lab.Controls.Add(dot)
    toast = WF.Label()
    toast.AutoSize = False
    toast.AutoEllipsis = True
    toast.TextAlign = ContentAlignment.MiddleLeft
    toast.Font = Font("Bahnschrift", 9.5, FontStyle.Regular, GraphicsUnit.Point)
    toast.BackColor = C_PANEL
    toast.ForeColor = C_TEXT
    toast.Location = Point(TAB_LEFT + len(TABS) * (TAB_W + TAB_GAP) + 8, 5)
    toast.Size = Size(0, TAB_H - 10)
    toast.Padding = WF.Padding(8, 0, 6, 0)
    toast.Visible = False
    bar.Controls.Add(toast)
    toast.BringToFront()
    edge = WF.Panel()                         # brass rule on the toast's left edge
    edge.Size = Size(2, TAB_H - 10)
    edge.Location = toast.Location
    edge.BackColor = C_ACC
    edge.Visible = False
    bar.Controls.Add(edge)
    edge.BringToFront()
    # Unread mark on the CLAUDE DUET tab (11/16): a small glowing orange dot (with a soft ring) for a new Claude Duet
    # reply or approval card that Matt has not opened yet, shown on every tab but Claude Duet. See unread_mark().
    claude_lab = items["claude"][0]
    ring = WF.Panel()
    ring.Size = Size(15, 15)
    ring.Location = Point(TAB_W - 21, 5)
    rpath = GraphicsPath()
    rpath.AddEllipse(0, 0, 15, 15)
    ring.Region = Region(rpath)
    ring.Visible = False
    cdot = WF.Panel()
    cdot.Size = Size(9, 9)
    cdot.Location = Point(TAB_W - 18, 8)
    cpath = GraphicsPath()
    cpath.AddEllipse(0, 0, 9, 9)
    cdot.Region = Region(cpath)
    cdot.Visible = False
    claude_lab.Controls.Add(ring)
    claude_lab.Controls.Add(cdot)
    cdot.BringToFront()
    # CHAT_DOCK (11/16): the same mark on the DAY BOARD tab instead, at its left end (the nudge dot keeps the right end),
    # because the chat lives on that tab then. Only one of the two marks is ever shown.
    tring = WF.Panel()
    tring.Size = Size(15, 15)
    tring.Location = Point(5, 5)
    tpath = GraphicsPath()
    tpath.AddEllipse(0, 0, 15, 15)
    tring.Region = Region(tpath)
    tring.Visible = False
    tdot = WF.Panel()
    tdot.Size = Size(9, 9)
    tdot.Location = Point(8, 8)
    tdpath = GraphicsPath()
    tdpath.AddEllipse(0, 0, 9, 9)
    tdot.Region = Region(tdpath)
    tdot.Visible = False
    today_lab.Controls.Add(tring)
    today_lab.Controls.Add(tdot)
    tdot.BringToFront()
    N = {"dot": dot, "toast": toast, "edge": edge, "w": 0.0, "until": 0.0, "text": "", "dot_on": False,
         "pulse": False, "col": (C_ACC, dim), "cdot": cdot, "ring": ring, "tdot": tdot, "tring": tring}
    TW = 250

    def tick(s, e):
        now = time.time()
        target = TW if now < N["until"] else 0
        if N["w"] != target:
            step = TW / 5.0 if target > N["w"] else TW / 8.0      # out in ~0.15 s, back in ~0.25 s
            N["w"] = min(target, N["w"] + step) if target > N["w"] else max(target, N["w"] - step)
        w = int(N["w"])
        if toast.Text != N["text"]:
            toast.Text = N["text"]
        toast.Width = w
        toast.Visible = edge.Visible = w > 2
        if dot.Visible != N["dot_on"]:
            dot.Visible = N["dot_on"]
        if N["dot_on"]:
            on = (not N["pulse"]) or int(now * 2) % 2 == 0
            dot.BackColor = N["col"][0] if on else N["col"][1]
        try:
            un = bool(tabs.get("unread")) and not chat_in_view()
            if not un:
                tabs["unread"] = False                         # opening the Claude Duet tab clears it (docked: DAY BOARD)
            pair = ("tdot", "tring") if dock_on() else ("cdot", "ring")
            for m in ("cdot", "ring", "tdot", "tring"):
                if m not in pair and N[m].Visible:
                    N[m].Visible = False
            mdot, mring = N[pair[0]], N[pair[1]]
            if mdot.Visible != un:
                mdot.Visible = mring.Visible = un
            if un:
                k = (math.sin(now * 3.2) + 1.0) / 2.0          # slow glow, about 2 s a cycle
                mdot.BackColor = Color.FromArgb(255, 255, int(150 + 50 * k), int(40 + 20 * k))
                mring.BackColor = Color.FromArgb(255, int(70 + 70 * k), int(36 + 30 * k), 10)
        except Exception:
            pass

    timer = WF.Timer()
    timer.Interval = 30
    timer.Tick += tick
    timer.Start()
    N["timer"] = timer
    tabs["nudge"] = N


nudge_timers = {}


def nudge(phase, title, mins, at=0, from_timer=False):
    """From the board page: an event is lead_minutes away ('soon') or starting ('now'). With 'soon'
    the page also sends the start time, and the app fires 'now' itself exactly then, because the board
    page's own timers run up to a minute late while another tab is in front."""
    c = ncfg()
    title = str(title or "").strip()[:60] or "Event"
    key = (title, int(at or 0))
    if phase == "soon" and at and key not in nudge_timers:
        delay = float(at) / 1000.0 - time.time()
        if 0 < delay < 3 * 3600:
            t = threading.Timer(delay, nudge, args=("now", title, 0, at, True))
            t.daemon = True
            nudge_timers[key] = t
            t.start()
    if phase == "now" and at and not from_timer and key in nudge_timers:
        return                                         # the app already fired this one on time
    log.info("nudge %s: %s (%s min)%s", phase, title, mins, "" if state.get("tabwin", "today") != "today" else " - on the Day Board tab, the page glows")
    N = tabs.get("nudge")
    if not c["on"] or not N or state.get("tabwin", "today") == "today":
        return
    N["text"] = ("Now: %s" % title) if phase == "now" else ("In %s min: %s" % (max(1, int(mins or 0)), title))
    N["until"] = time.time() + float(c["toast_seconds"])
    N["dot_on"] = True
    N["pulse"] = N["pulse"] or phase == "now"


def nudge_clear():
    N = tabs.get("nudge")
    if N:
        N["dot_on"], N["pulse"], N["until"] = False, False, 0.0


def board_fit_cfg():
    return dict({"on": True, "base_w": 1280, "base_h": 820, "min": 0.8, "max": 1.6}, **(CFG.get("BOARD_FIT") or {}))


def board_fit_install():
    """Scale the Day Board page to the window: zoom = the smaller of width/base_w and height/base_h
    (CSS pixels, so DPI is accounted for), kept between min and max. Re-done on every resize and
    page load. Only the Day Board view; Discord and Claude Duet keep their own zoom."""
    from System import Action, EventHandler
    f = board.native
    wv = f.webview

    def fit(*a):
        try:
            c = board_fit_cfg()
            if not c["on"] or str(f.WindowState) == "Minimized":   # minimized: keep the last zoom
                return
            dpi = max(1.0, f.DeviceDpi / 96.0)
            w, h = wv.Width / dpi, wv.Height / dpi
            if w < 50 or h < 50:
                return
            z = max(float(c["min"]), min(float(c["max"]), w / float(c["base_w"]), h / float(c["base_h"])))
            z = round(z, 2)
            if abs(wv.ZoomFactor - z) > 0.005:
                wv.ZoomFactor = z
                state["board_zoom"] = z
                log.info("board fit: view %dx%d -> zoom %.2f", w, h, z)
        except Exception as e:
            log.error("board fit: %s", e)

    def run():
        wv.SizeChanged += EventHandler(fit)
        wv.NavigationCompleted += lambda s, e: fit()
        fit()

    f.Invoke(Action(run))
    tabs["fit"] = fit


def tabbars_on():
    return bool(CFG.get("TAB_BAR", True))


def build_tabbars():
    if not tabbars_on():
        return
    for w in ((board,) if embed_on() else (board, discord_win(), claude_win())):
        if w:
            try:
                build_tabbar(w)
                log.info("tab bar on %s", w.title)
            except Exception as e:
                log.exception("tab bar on %s failed: %s", w.title, e)


# ---------- mic status HUD: is a mic hot? ----------
# A click-through, always-on-top strip at the top centre of the main monitor (over windowed-
# fullscreen WoW too), plus the same status at the right end of the tab bar.
#   [ DISCORD LIVE ]  red outline; solid red while voice is actually going out
#   [ DISCORD MUTED ] grey
#   [ CLAUDE LISTENING ]  only while F12 is recording, to the right, so the two never mix
# The Discord segment never moves; the Claude one appears beside it.

hud = {"form": None, "disc": None, "speak": False, "claude": False, "test_claude": 0.0}


def hcfg():
    return dict({"on": True, "corner": "top-center", "top_offset": 44, "margin": 6, "light_px": 10, "label_px": 170, "label_pt": 9,
                 "label_seconds": 3}, **(CFG.get("MIC_HUD") or {}))


def hud_state():
    d = dcfg()
    if not d["on"]:
        disc = None
    elif d["mode"] == "voice":
        disc = "muted" if state.get("d_mute") else "live"
    elif d["mode"] == "ptt":
        disc = "live" if state.get("d_live") else "muted"
    else:
        disc = "live"
    claude = bool(state.get("rec")) or time.time() < hud["test_claude"]
    return disc, False, claude


def build_hud():
    """Mic status as two small lights tucked into a corner of the main monitor (Discord on top,
    Claude below), in the same colours as before: brass = hot mic, grey = muted. When a light changes,
    its label slides out beside it for label_seconds, then slides back in; hovering a light shows its
    label too. Everything around the lights is see-through and click-through (colour-key layered
    window), so the windows behind stay usable; the lights never take focus."""
    import System.Windows.Forms as WF
    from System import Action
    from System.Drawing import (Color, Font, FontStyle, GraphicsUnit, SolidBrush, Pen, Rectangle,
                                StringFormat, StringAlignment, RectangleF, Region)
    from System.Drawing.Drawing2D import SmoothingMode
    from System.Drawing.Text import TextRenderingHint
    c = hcfg()
    th = theme()
    col = lambda hx: Color.FromArgb(255, int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16))
    KEY = Color.FromArgb(255, 1, 1, 1)                 # this exact colour is invisible and click-through
    C = {"page": col(th["page"]), "line": col(th["hairline"]), "text": col(th["text"]),
         "muted": col(th["muted"]), "acc": col(th["accent"])}
    D = int(c.get("light_px", 10))                     # light diameter
    PAD, GAP = 3, 6                                    # edge margin, gap between the two rows
    ROW = D + 6                                        # row height (label pill is a bit taller than the light)
    LW = int(c.get("label_px", 170))                   # label pill width
    if str(c.get("corner", "top-center")) == "top-center":   # side by side, labels slide outward
        MID = 14                                         # gap between the two lights
        W, H = PAD + LW + 4 + D + MID + D + 4 + LW + PAD, PAD + ROW + PAD
        lx_d = PAD + LW + 4
        lights = {"disc": {"x": lx_d, "y": PAD, "dir": -1, "p": 0.0},
                  "claude": {"x": lx_d + D + MID, "y": PAD, "dir": 1, "p": 0.0}}
    else:                                                # a corner: stacked, labels slide right
        W, H = PAD + D + 6 + LW + PAD, PAD + 2 * ROW + GAP + PAD
        lights = {"disc": {"x": PAD, "y": PAD, "dir": 1, "p": 0.0},
                  "claude": {"x": PAD, "y": PAD + ROW + GAP, "dir": 1, "p": 0.0}}
    hud["lights"], hud["pop_until"], hud["hover"] = lights, {"disc": 0.0, "claude": 0.0}, None

    def label(key):
        if key == "disc":
            return spaced("DISCORD HOT MIC" if hud.get("disc") == "live" else "DISCORD MUTED") if hud.get("disc") else ""
        return spaced("CLAUDE HOT MIC" if hud.get("claude") else "CLAUDE MUTED")

    def hot(key):
        return hud.get("disc") == "live" if key == "disc" else bool(hud.get("claude"))

    def make():
        f = WF.Form()
        f.FormBorderStyle = getattr(WF.FormBorderStyle, "None")
        f.ShowInTaskbar = False
        f.TopMost = True
        f.StartPosition = WF.FormStartPosition.Manual
        f.BackColor = KEY
        f.TransparencyKey = KEY
        f.Text = "Day Board mic status"
        f.Width, f.Height = W, H
        font = Font("Bahnschrift SemiBold SemiConden", float(c.get("label_pt", 9)), FontStyle.Regular, GraphicsUnit.Point)
        if font.Name != "Bahnschrift SemiBold SemiConden":
            font = Font("Bahnschrift", float(c.get("label_pt", 9)), FontStyle.Bold, GraphicsUnit.Point)
        sf = StringFormat()
        sf.Alignment = StringAlignment.Near
        sf.LineAlignment = StringAlignment.Center

        def on_paint(s, e):
            g = e.Graphics
            g.Clear(KEY)
            g.TextRenderingHint = TextRenderingHint.AntiAliasGridFit
            for key, L in lights.items():
                if key == "disc" and not hud.get("disc"):
                    continue
                y, lx, on = L["y"], L["x"], hot(key)
                # label pill, revealed outward from the light by p (0 = tucked in, 1 = fully out)
                p = L["p"]
                if p > 0.01:
                    lw = int(LW * p)
                    if L["dir"] > 0:
                        x0, full = lx + D + 4, lx + D + 4
                        sf.Alignment = StringAlignment.Near
                    else:
                        x0, full = lx - 4 - lw, lx - 4 - LW
                        sf.Alignment = StringAlignment.Far
                    g.SmoothingMode = getattr(SmoothingMode, "None")
                    g.FillRectangle(SolidBrush(C["page"]), Rectangle(x0, y, lw, ROW))
                    g.DrawRectangle(Pen(C["acc"] if on else C["line"], 1.0), Rectangle(x0, y, lw - 1, ROW - 1))
                    g.SetClip(Rectangle(x0, y, lw, ROW))
                    g.DrawString(label(key), font, SolidBrush(C["text"] if on else C["muted"]),
                                 RectangleF(float(full + 6), float(y), float(LW - 12), float(ROW)), sf)
                    g.ResetClip()
                # the light: a small filled dot with a dark rim (the rim hides colour-key fringes)
                g.SmoothingMode = SmoothingMode.AntiAlias
                cy = y + (ROW - D) // 2
                g.FillEllipse(SolidBrush(C["page"]), lx - 1, cy - 1, D + 2, D + 2)
                g.FillEllipse(SolidBrush(C["acc"] if on else C["muted"]), lx, cy, D, D)

        def which(px, py):
            for key, L in lights.items():
                if key == "disc" and not hud.get("disc"):
                    continue
                y, lx = L["y"], L["x"]
                ext = int(LW * L["p"]) + 4 if L["p"] > 0.01 else 0
                lo, hi = (lx - 3, lx + D + 3 + ext) if L["dir"] > 0 else (lx - 3 - ext, lx + D + 3)
                if lo <= px <= hi and y - 2 <= py <= y + ROW + 2:
                    return key
            return None

        def on_move(s, e):
            hud["hover"] = which(e.X, e.Y)

        def on_leave(s, e):
            hud["hover"] = None

        def tick(s, e):
            """30 ms animation step on the UI thread: slide each label toward shown / hidden."""
            now, changed = time.time(), False
            for key, L in lights.items():
                target = 1.0 if (hud.get("hover") == key or now < hud["pop_until"].get(key, 0)) else 0.0
                if L["p"] != target:
                    step = 0.03 / (0.15 if target > L["p"] else 0.25)   # out in 0.15 s, back in 0.25 s
                    L["p"] = min(target, L["p"] + step) if target > L["p"] else max(target, L["p"] - step)
                    changed = True
            if changed or hud.pop("repaint", False):
                f.Invalidate()

        f.Paint += on_paint
        f.MouseMove += on_move
        f.MouseLeave += on_leave
        timer = WF.Timer()
        timer.Interval = 30
        timer.Tick += tick
        timer.Start()
        hud["timer"] = timer
        hud["form"], hud["dims"] = f, (W, H)
        f.Handle  # create the window without showing (and without taking focus)
        h = int(f.Handle.ToInt64())
        ex = user32.GetWindowLongW(h, -20)
        # keep WinForms' colour-key layering; add no-activation + tool window (no Alt-Tab, no taskbar).
        # Not WS_EX_TRANSPARENT: the lights themselves take hover, the see-through rest passes clicks on.
        user32.SetWindowLongW(h, -20, (ex | 0x08000000 | 0x80 | 0x8 | 0x80000) & ~0x20)
        hud["hwnd"] = h

    board.native.Invoke(Action(make))
    log.info("mic HUD ready (corner lights)")


def spaced(text):
    return "   ".join(" ".join(w) for w in text.split(" "))


def hud_place():
    """The lights' window in a corner of the main monitor (MIC_HUD corner/margin)."""
    from System import Action
    f = hud.get("form")
    if not f:
        return
    W, H = hud["dims"]
    c = hcfg()
    m = next((m for m in monitors() if m["primary"]), {"x": 0, "y": 0, "w": 1920, "h": 1080})
    corner, mg = str(c.get("corner", "top-center")), int(c.get("margin", 6))
    if corner == "top-center":                         # centred, below a maximized window's title bar row
        x = m["x"] + (m["w"] - W) // 2
        y = m["y"] + int(c.get("top_offset", 44))
    else:
        x = m["x"] + mg if "left" in corner else m["x"] + m["w"] - W - mg
        y = m["y"] + mg if "top" in corner else m["y"] + m["h"] - H - mg

    def run():
        user32.SetWindowPos(hud["hwnd"], HWND_TOPMOST, x, y, W, H, 0x10 | 0x40)   # NOACTIVATE | SHOWWINDOW
        hud["repaint"] = True

    f.Invoke(Action(run))


def hud_loop():
    last = None
    n = 0
    while True:
        time.sleep(0.08)
        try:
            cur = hud_state()
            n += 1
            if cur != last or n % 25 == 0:          # also re-assert topmost every 2 s
                hud["disc"], hud["speak"], hud["claude"] = cur
                if last is not None and cur != last:
                    secs = float(hcfg().get("label_seconds", 3))
                    if cur[0] != last[0]:
                        hud["pop_until"]["disc"] = time.time() + secs
                    if cur[2] != last[2]:
                        hud["pop_until"]["claude"] = time.time() + secs
                hud_place()
                if last is None or cur != last:
                    update_tabbars()
                if last is not None and cur != last:
                    log.info("mic status: discord=%s claude=%s", cur[0], "hot" if cur[2] else "muted")
                last = cur
        except Exception as e:
            log.error("mic HUD: %s", e)
            time.sleep(2)


def start_hud():
    if not hcfg()["on"]:
        return
    try:
        build_hud()
        threading.Thread(target=hud_loop, daemon=True).start()
    except Exception as e:
        log.exception("mic HUD failed: %s", e)


def hud_test():
    """hudtest.go: shows CLAUDE HOT MIC for 4 s (display only; nothing records)."""
    hud["test_claude"] = time.time() + 4


# ---------- audio mirror: everything on the Magni also plays on the monitor speakers ----------
# Windows can't send one output to two devices, so Day Board copies it: a WASAPI loopback of the
# "from" device (what Matt hears on the headphones) is played into the "to" device in 10 ms blocks.
# Matt controls each side himself (headphones off, monitor volume knob). If "from" disappears it
# falls back to the Windows default output; it never mirrors a device into itself.

def acfg():
    return dict({"on": True, "from": "Magni", "to": "ARZOPA", "block_ms": 10}, **(CFG.get("AUDIO_MIRROR") or {}))


MAGNI_FLAG = os.path.join(ROOT, "magni-muted-by-dayboard.flag")
magni_state = {"was_muted": None}


def magni_mute(endpoint_id, on):
    """Mute the headphones for an F12 recording; on release, unmute only if Day Board muted them
    (if Matt had muted them himself, they stay muted). A flag file lets a restart undo a mute
    left behind by a crash."""
    import endpoint_mute
    try:
        if on:
            magni_state["was_muted"] = endpoint_mute.get_mute(endpoint_id)
            if not magni_state["was_muted"]:
                endpoint_mute.set_mute(endpoint_id, True)
                open(MAGNI_FLAG, "w").write(endpoint_id)
        else:
            if magni_state["was_muted"] is False:
                endpoint_mute.set_mute(endpoint_id, False)
            magni_state["was_muted"] = None
            if os.path.exists(MAGNI_FLAG):
                os.remove(MAGNI_FLAG)
    except Exception as e:
        log.error("magni mute %s: %s", on, e)


def audio_mirror():
    import warnings
    try:
        warnings.simplefilter("ignore")          # soundcard warns on every silent gap ("discontinuity")
        import soundcard as sc
    except Exception as e:
        log.exception("audio mirror could not start: %s", e)
        return
    log.info("audio mirror thread up")
    if os.path.exists(MAGNI_FLAG):                    # left muted by a crash mid-recording: undo it
        try:
            import endpoint_mute
            endpoint_mute.set_mute(open(MAGNI_FLAG).read().strip(), False)
            os.remove(MAGNI_FLAG)
            log.info("audio mirror: headphones unmuted (left muted by an earlier crash)")
        except Exception as e:
            log.error("magni unmute at start: %s", e)
    while True:
        try:
            c = acfg()
            if not c["on"]:
                time.sleep(5)
                continue
            spk = sc.all_speakers()
            src = next((x for x in spk if c["from"].lower() in x.name.lower()), None) or sc.default_speaker()
            dst = next((x for x in spk if c["to"].lower() in x.name.lower()), None)
            if not dst or dst.name == src.name:
                log.warning("audio mirror: no target %r (or same as source %s)", c["to"], src.name)
                time.sleep(15)
                continue
            n = int(48000 * float(c["block_ms"]) / 1000)
            lb = sc.get_microphone(id=str(src.name), include_loopback=True)
            log.info("audio mirror on: %s -> %s", src.name, dst.name)
            with lb.recorder(samplerate=48000, channels=2, blocksize=n) as rec,                     dst.player(samplerate=48000, channels=2, blocksize=n) as play:
                check = time.time()
                gain = 1.0
                mode = "full"
                magni = src.id if "magni" in src.name.lower() else None
                while True:
                    data = rec.record(numframes=n)
                    # While F12 (Claude) is hot: ALL sound stops - the Magni is muted at Windows' own
                    # mute switch and the Odyssey copy goes silent - so Claude hears only Matt.
                    # While ` (Discord) is hot: the Odyssey copy drops to duck_db (-16 dB, about 15%);
                    # the Magni is untouched. Everything returns the moment the mic stops.
                    disc, _, claude = hud_state()
                    cfg = acfg()
                    if claude and cfg.get("claude_mutes_all", True):
                        want, target = "silent", 0.0
                    elif disc == "live":
                        want, target = "duck", 10 ** (float(cfg.get("duck_db", -16)) / 20.0)
                    else:
                        want, target = "full", 1.0
                    if want != mode:
                        if want == "silent" and magni:
                            magni_mute(magni, True)
                        elif mode == "silent" and magni:
                            magni_mute(magni, False)
                        log.info("audio mirror: %s", {"silent": "all sound off (claude mic hot)",
                                                      "duck": "speakers down to %s dB (discord mic hot)" % cfg.get("duck_db", -16),
                                                      "full": "all sound back (both mics muted)"}[want])
                        mode = want
                    if gain != target:
                        step = max(1.0 - target, 1.0 - gain, 0.05) * len(data) / (48.0 * max(1.0, float(cfg.get("fade_ms", 40))))
                        nxt = max(target, gain - step) if target < gain else min(target, gain + step)
                        data = data * np.linspace(gain, nxt, len(data), dtype=np.float32)[:, None]
                        gain = nxt
                    elif gain != 1.0:
                        data = data * gain
                    play.play(data)
                    if time.time() - check > 5:
                        check = time.time()
                        c2 = acfg()
                        names = [x.name for x in sc.all_speakers()]
                        if not c2["on"] or dst.name not in names or src.name not in names                                 or c2["from"] != c["from"] or c2["to"] != c["to"]                                 or (c["from"].lower() not in src.name.lower() and any(c["from"].lower() in x.lower() for x in names)):
                            log.info("audio mirror: devices or settings changed, restarting")
                            break
        except Exception as e:
            log.error("audio mirror: %s", e)
            time.sleep(3)


class DiscordApi:
    def show_board(self):
        threading.Thread(target=discord_show, args=(False,), daemon=True).start()
        return True


# ---------- push to talk ----------

def beep(f, ms):
    threading.Thread(target=winsound.Beep, args=(f, ms), daemon=True).start()


# ---------- sounds and the listening indicator ----------

SOUND_DIR = os.path.join(ROOT, "sounds")
SOUNDS = {   # name: (start Hz, end Hz, ms, volume) - short sine sweeps with a soft attack
    "press": [(520, 980, 55, 0.20)],
    "release": [(980, 520, 55, 0.20)],
    "sent": [(880, 880, 40, 0.13), (1320, 1320, 55, 0.13)],
    "fail": [(420, 300, 90, 0.16)],
    "shot": [(1500, 1500, 25, 0.12), (1900, 1900, 30, 0.12)],
    "cancel": [(700, 520, 40, 0.16), (480, 340, 60, 0.16)],
}


def make_sounds():
    os.makedirs(SOUND_DIR, exist_ok=True)
    sr = 44100
    for name, parts in SOUNDS.items():
        out = []
        for f0, f1, ms, vol in parts:
            n = int(sr * ms / 1000)
            t = np.arange(n) / sr
            phase = 2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / sr
            env = np.minimum(1.0, t / 0.004) * np.exp(-t / (ms / 1000 / 3.0))
            out += [np.sin(phase) * env * vol, np.zeros(int(sr * 0.012))]
        y = (np.concatenate(out) * 32767).astype(np.int16)
        with wave.open(os.path.join(SOUND_DIR, name + ".wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


def sound(name):
    """Soft click/tick (PTT_SOUNDS on). With PTT_SOUNDS off: silent press/release, old beeps otherwise."""
    if CFG.get("PTT_SOUNDS", True):
        try:
            winsound.PlaySound(os.path.join(SOUND_DIR, name + ".wav"),
                               winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as e:
            log.error("sound %s failed: %s", name, e)
    elif name == "sent":
        beep(1200, 60)
    elif name == "fail":
        beep(300, 200)


# ---------- Claude Duet banners (11/16) ----------
# A new Claude Duet reply, or an approval card asking Matt to Allow / Deny a message to a Claude Code session,
# drops down from the CLAUDE DUET tab in the top tab strip like a drawer hung on that tab, over whatever tab is
# in front (Discord included). Each banner is a small borderless window owned by the Day Board window, shown
# without taking focus, no sound of its own. The orange unread dot on the tab stays until Claude Duet is opened,
# or (11/16) until the pointer moves onto a banner or a banner is clicked: that reads the notification.
# Reply banner: NEVER times out; it slides away when the pointer enters it (read) or it is clicked (read, and the
# Claude Duet tab opens), or when Claude Duet is opened; several replies stack as "(N)". Approval
# banner: stays until Matt clicks Allow or Deny, or the card is gone from the tab (hovering it only clears the
# dot, so he can reach the buttons); it never clicks by itself:
# only Matt's click on a banner button presses the matching button on the real card (window.__dbChime.clickCard
# in the chat page). If the card or its button can't be found, or the click doesn't take, it says so and opens
# the Claude Duet tab. Neither shows while the Claude Duet tab itself is in front.
# 11/16 sticky: reply banners are now a stack of cards that stay until closed, each with Reply (see 'reply banners').
# config.json REPLY_TOAST: on, chars (200), width (480), max_cards (4), listen. (min_seconds and max_seconds are no longer used.)
# config.json APPROVAL_TOAST: on, width (500), preview_chars (220).
# 11/16 CHAT_DOCK: with the chat docked, "the CLAUDE DUET tab" above means the DAY BOARD tab: banners hang from it, the
# unread mark sits on its left end, and nothing shows (and no mark lights) while it is in front, because the chat is on
# screen then. Clicking a banner, or a failed Allow/Deny, opens the DAY BOARD tab.
rt = {"form": None, "cards": [], "shown": False, "h_full": 0, "h_now": 0.0}
apr = {"pending": {}, "form": None, "shown": False, "expanded": False, "status": "", "fail_until": 0.0, "ctl": {},
       "h_full": 0, "h_now": 0.0}
banner_timer = {"t": None}


def clean_text(s):
    """Drop what the board's font can't draw (icon-font private-use characters, emoji, arrows and boxes, format and
    variation characters): they showed up as hollow squares. Plain letters, digits and punctuation stay."""
    import unicodedata
    out = []
    for ch in str(s or ""):
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat in ("Co", "Cn", "Cs", "Cf") or ch == "�" or 0xFE00 <= cp <= 0xFE0F or cp >= 0x1F000:
            continue
        if cat == "So" and cp >= 0x2190:
            continue
        out.append(" " if ch in "   " else ch)
    return "".join(out)


def clean_lines(s):
    lines = [re.sub(r"[ \t]+", " ", clean_text(x)).strip() for x in str(s or "").split("\n")]
    return "\n".join(x for x in lines if x)


def unread_mark(why):
    """A new Claude Duet reply or approval card while another tab is in front: light the dot on the CLAUDE DUET tab
    (CHAT_DOCK: on the DAY BOARD tab, and never while that tab, with the chat on it, is in front)."""
    if not chat_in_view():
        if not tabs.get("unread"):
            log.info("unread mark on: %s", why)
        tabs["unread"] = True


def rtcfg():
    return dict({"on": True, "chars": 200, "min_seconds": 6.0, "max_seconds": 12.0, "width": 480}, **(CFG.get("REPLY_TOAST") or {}))


def aprcfg():
    return dict({"on": True, "width": 500, "preview_chars": 220}, **(CFG.get("APPROVAL_TOAST") or {}))


def banner_anchor():
    """Screen position just under the CLAUDE DUET tab label (left edge of the tab, bottom of the tab strip).
    CHAT_DOCK: under the DAY BOARD tab label, where the chat lives then."""
    from System.Drawing import Point
    b = tabs.get("bars", {}).get("Day Board")
    if not b:
        return None
    lab = b[1]["today" if dock_on() else "claude"][0]
    bar = lab.Parent
    p = lab.PointToScreen(Point(0, 0))
    q = bar.PointToScreen(Point(0, bar.Height))
    return int(p.X), int(q.Y)


def banner_gone():
    """True while no banner should be up: Claude Duet is in front (CHAT_DOCK: the DAY BOARD tab), the board is hidden
    or minimized."""
    return chat_in_view() or bool(state.get("hidden")) or str(board.native.WindowState) == "Minimized"


def banner_make(width):
    """A borderless, no-focus window owned by the Day Board window, with a full-size 'page' panel that holds the
    content (the window itself is only as tall as the slide so far, which clips the page)."""
    import System.Windows.Forms as WF
    from System.Drawing import ColorTranslator, Size
    th = theme()
    f = WF.Form()
    f.FormBorderStyle = getattr(WF.FormBorderStyle, "None")
    f.ShowInTaskbar = False
    f.StartPosition = WF.FormStartPosition.Manual
    f.BackColor = ColorTranslator.FromHtml(th["hairline"])            # shows as a 1 px border round the page
    f.Opacity = 0.98
    f.Size = Size(int(width), 2)
    page = WF.Panel()
    page.BackColor = ColorTranslator.FromHtml(th["panel"])
    f.Controls.Add(page)
    f.CreateControl()
    h = int(f.Handle.ToInt64())
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    u.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
    u.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    u.SetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
    u.SetWindowLongPtrW(h, -20, u.GetWindowLongPtrW(h, -20) | 0x08000000 | 0x00000080)     # NOACTIVATE | TOOLWINDOW
    u.SetWindowLongPtrW(h, -8, int(board.native.Handle.ToInt64()))                       # owned: above the Day Board only
    return f, page, h


def banner_label(page, bold=False, size=10.0, colour="text", hand=False):
    import System.Windows.Forms as WF
    from System.Drawing import ColorTranslator, Font, FontStyle, GraphicsUnit
    th = theme()
    l = WF.Label()
    l.AutoSize = False
    l.Font = Font("Bahnschrift", size, FontStyle.Bold if bold else FontStyle.Regular, GraphicsUnit.Point)
    l.ForeColor = ColorTranslator.FromHtml(th[colour])
    l.BackColor = ColorTranslator.FromHtml(th["panel"])
    if hand:
        l.Cursor = WF.Cursors.Hand
    page.Controls.Add(l)
    return l


def banner_tab_mark(page, width):
    """The top edge that ties the banner to its tab: a brass rule as wide as the tab, a hairline for the rest."""
    import System.Windows.Forms as WF
    from System.Drawing import ColorTranslator
    th = theme()
    rest = WF.Panel(); rest.BackColor = ColorTranslator.FromHtml(th["hairline"]); rest.SetBounds(0, 0, width, 1)
    mark = WF.Panel(); mark.BackColor = ColorTranslator.FromHtml(th["accent"]); mark.SetBounds(0, 0, TAB_W, 2)
    page.Controls.Add(rest)
    page.Controls.Add(mark)
    mark.BringToFront()


def banner_step(b, want, y_off=0):
    """Every 30 ms: slide the banner down (about 0.2 s) or back up (0.25 s), keep it under the tab, show/hide it."""
    f = b["form"]
    if f is None:
        return
    full = float(b["h_full"])
    if want and full > 0:
        b["h_now"] = min(full, b["h_now"] + max(6.0, full / 6.0))
    else:
        b["h_now"] = max(0.0, b["h_now"] - max(6.0, full / 8.0))
    if b["h_now"] < 3.0:
        b["h_now"] = 0.0
        if b["shown"]:
            b["shown"] = False
            f.Hide()
        return
    a = banner_anchor()
    if not a:
        return
    from System.Drawing import Point, Size
    f.Location = Point(a[0], a[1] + int(y_off))
    f.Size = Size(f.Width, int(b["h_now"]))
    if not b["shown"]:
        b["shown"] = True
        user32.ShowWindow(wintypes.HWND(b["h"]), 4)                              # SW_SHOWNOACTIVATE: no focus change
        banner_raise(b)
    elif time.time() - b.get("raised", 0.0) > 0.5:
        banner_raise(b)


_zu = ctypes.WinDLL("user32")
_zu.GetWindow.restype = ctypes.c_void_p
_zu.GetWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
_zu.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
_zu.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]


def banner_raise(b):
    """11/16 fix: keep a banner just above the Day Board window, never above anything else. The board is often
    always-on-top (ON_TOP), and a banner that isn't sat behind it, unseen. So: topmost while the board is topmost,
    otherwise placed directly over the board in the normal stack (an app covering the board still covers the banner)."""
    b["raised"] = time.time()
    bh = int(board.native.Handle.ToInt64())
    me = b["h"]
    flags = 0x0001 | 0x0002 | 0x0010                                           # NOSIZE | NOMOVE | NOACTIVATE
    if _zu.GetWindowLongW(bh, -20) & 0x8:                                       # WS_EX_TOPMOST on the board
        _zu.SetWindowPos(me, -1, 0, 0, 0, 0, flags)                             # HWND_TOPMOST
        return
    if _zu.GetWindowLongW(me, -20) & 0x8:
        _zu.SetWindowPos(me, -2, 0, 0, 0, 0, flags)                             # HWND_NOTOPMOST
    prev = _zu.GetWindow(bh, 3)                                                 # GW_HWNDPREV: the window just above the board
    if prev and int(prev) == int(me):
        return                                                                  # already right above it
    if prev and _zu.GetWindowLongW(prev, -20) & 0x8:
        prev = None                                                             # an always-on-top window: the board leads the normal stack
    _zu.SetWindowPos(me, prev or 0, 0, 0, 0, 0, flags)                          # below 'prev' = right above the board


def mark_read(why):
    """Hover or click on a banner: that notification counts as seen, so the orange dot on the tab goes out."""
    if tabs.get("unread"):
        log.info("unread cleared: %s", why)
    tabs["unread"] = False


def banner_hover(b):
    """True on the tick the mouse pointer moves INTO a shown banner from outside. A pointer already resting where the
    banner lands (tested against its full size, not the part slid out so far) does not count until it leaves and
    comes back, so a banner never dismisses itself the moment it appears."""
    from System.Windows.Forms import Control
    f = b["form"]
    if f is None or not b["shown"] or b["h_now"] < 6.0:
        b["hv_ready"] = False
        return False
    p = Control.MousePosition
    now_in = f.Left <= p.X < f.Left + f.Width and f.Top <= p.Y < f.Top + int(b["h_full"])
    if not b.get("hv_ready"):
        b["hv_ready"] = True
        b["inside"] = now_in
        return False
    entered = now_in and not b.get("inside", False)
    b["inside"] = now_in
    return entered


def banner_tick(s=None, e=None):
    try:
        gone = banner_gone()
        failing = time.time() < apr["fail_until"]
        banner_step(apr, aprcfg()["on"] and (failing or (bool(apr["pending"]) and not gone)))
        r_want = bool(rt["cards"]) and not gone                  # sticky: up until Matt closes it (x or Clear all)
        banner_step(rt, r_want, (apr["h_now"] + 4) if apr["shown"] else 0)
        if banner_hover(rt):
            mark_read("reply banner hover")                     # hover reads it (the dot goes out); the card stays
        if banner_hover(apr):
            mark_read("approval banner hover")                  # approval banner stays until Allow or Deny, but is read
    except Exception as ex:
        if time.time() - banner_timer.get("err", 0) > 30:
            banner_timer["err"] = time.time()
            log.error("banner tick: %s", ex)


def banner_timer_start():
    if banner_timer["t"] is None:
        import System.Windows.Forms as WF
        t = WF.Timer()
        t.Interval = 30
        t.Tick += banner_tick
        t.Start()
        banner_timer["t"] = t


# ---- reply banners (11/16 sticky): one card per new Claude Duet message, stacked, each stays until closed ----
# Matt, 11/16: every incoming message banner stays up until he closes it; several stack (newest on top), each with a
# close x, plus "Clear all" once 2 or more are up. Shown on every tab except CLAUDE DUET (they wait while that tab is
# in front and come back after), only inside the Day Board window. Each card has Reply: it records exactly like F12
# (same mic, speech test, mute-all while hot, Esc cancels, cancel if nothing heard) with REPLY_TOAST.listen timing
# (1 s start grace, 3 s to start talking, stops 1 s after he goes quiet), then sends his words as a Duet reply to
# THAT message (the message's own Reply button, checked by the "Replying to" chip), never as a new message. If that
# message can't be found, his words are left unsent in the Claude Duet box. A small "Sent" tick shows after.
# config.json REPLY_TOAST: on, chars (200), width (480), max_cards (4), listen {start_grace_seconds, voice_wait_seconds,
# quiet_seconds}. Calm look: no flashing, no sound of its own.

def rt_listen():
    L = dict({"start_grace_seconds": 1.0, "voice_wait_seconds": 3.0, "quiet_seconds": 1.0}, **(rtcfg().get("listen") or {}))
    return {k: float(v) for k, v in L.items()}


def reply_toast(text, mid="", row="", test=False):
    c = rtcfg()
    text = re.sub(r"\s+", " ", clean_text(text)).strip()
    if not text:
        return
    if not test:
        unread_mark("reply")
    if not c["on"]:
        return
    n = int(c["chars"])
    if len(text) > n:
        text = text[:n].rsplit(" ", 1)[0].rstrip(",;:-") + "…"
    vis = chat_in_view()                       # the Claude Duet tab in front (CHAT_DOCK: the DAY BOARD tab)
    log.info("reply banner: %d chars, message %s%s", len(text), str(mid)[-8:] or "-",
             (" (skipped: Claude Duet is docked on the DAY BOARD tab)" if dock_on() else " (skipped: on the Claude Duet tab)")
             if vis and not test else "")
    if vis and not test:
        return
    card = {"key": "k%d" % int(time.time() * 1000 + len(rt["cards"])), "mid": str(mid)[:120], "row": str(row)[:140],
            "text": text, "at": time.strftime("%I:%M %p").lstrip("0"), "status": "", "phase": "idle", "test": bool(test)}
    rt_poke(lambda: rt_add(card))


def rt_add(card):
    """UI thread. Newest on top; the same message arriving twice only refreshes its text."""
    for old in rt["cards"]:
        if card["mid"] and old["mid"] == card["mid"]:
            old["text"] = card["text"]
            rt_layout()
            return
    rt["cards"].insert(0, card)
    log.info("reply banner up until closed (%d stacked)", len(rt["cards"]))
    rt_layout()


def rt_poke(fn=None):
    """Run fn (or a re-layout) on the UI thread without waiting for it."""
    try:
        from System import Action
        board.native.BeginInvoke(Action(fn or rt_layout))
    except Exception as e:
        log.error("reply banner: %s", e)


def rt_card(key):
    return next((c for c in rt["cards"] if c["key"] == key), None)


def rt_set(key, status, phase):
    """Any thread: set one card's status line ('Listening…', 'Sent', ...) and re-lay out."""
    def go():
        c = rt_card(key)
        if c:
            c["status"], c["phase"] = status, phase
            rt_layout()
    rt_poke(go)


def rt_close(key):
    if state.get("reply_to") == key and state["rec"]:
        events.put(("esc", "down")); events.put(("esc", "up"))       # closing a card mid-reply cancels that reply
    rt["cards"] = [c for c in rt["cards"] if c["key"] != key]
    mark_read("reply banner closed")
    log.info("reply banner closed (%d left)", len(rt["cards"]))
    rt_layout()


def rt_clear_all():
    if state.get("reply_to") and state["rec"]:
        events.put(("esc", "down")); events.put(("esc", "up"))
    n = len(rt["cards"])
    rt["cards"] = []
    mark_read("reply banners cleared")
    log.info("reply banners: clear all (%d)", n)
    rt_layout()


def rt_reply_click(key):
    c = rt_card(key)
    if not c:
        return
    if state["rec"] and state.get("reply_to") == key:
        events.put(("reply_stop", key))                               # Reply again while listening: send now
    else:
        events.put(("reply", key))


def rt_build():
    c = rtcfg()
    f, page, h = banner_make(int(c["width"]))
    rt.update({"form": f, "page": page, "h": h})
    banner_timer_start()


def rt_layout():
    try:
        _rt_layout()
    except Exception as e:
        if time.time() - rt.get("err_t", 0) > 30:
            rt["err_t"] = time.time()
            log.exception("reply banner layout: %s", e)


def _rt_layout():
    """UI thread: rebuild the stack's controls from rt['cards'] (only when something changes, so it stays cheap)."""
    import System.Windows.Forms as WF
    from System.Drawing import ColorTranslator, ContentAlignment, Font, FontStyle, GraphicsUnit, Size
    c = rtcfg()
    if rt["form"] is None:
        if not rt["cards"]:
            return
        rt_build()
    th = theme()
    col = lambda k: ColorTranslator.FromHtml(th[k])
    w = int(c["width"])
    page = rt["page"]
    page.SuspendLayout()
    old = list(page.Controls)
    page.Controls.Clear()
    for x in old:
        try:
            x.Dispose()
        except Exception:
            pass
    banner_tab_mark(page, w - 2)
    pad, inner = 14, w - 2 - 28
    cards = rt["cards"]
    shown = cards[:max(1, int(c.get("max_cards", 4)))]
    y = 4
    if len(cards) >= 2:
        head = banner_label(page, True, 8.5, "secondary")
        head.Text = ("%d MESSAGES" % len(cards)) + (("  ·  NEWEST %d SHOWN" % len(shown)) if len(shown) < len(cards) else "")
        head.SetBounds(pad, y + 6, inner - 80, 16)
        clr = banner_label(page, False, 9.0, "accent", True)
        clr.Text = "Clear all"
        clr.TextAlign = ContentAlignment.MiddleRight
        clr.SetBounds(w - 2 - pad - 80, y + 4, 80, 18)
        clr.Click += lambda s, e: rt_clear_all()
        y += 26
    for i, cd in enumerate(shown):
        if i or len(cards) >= 2:
            sep = WF.Panel(); sep.BackColor = col("hairline"); sep.SetBounds(pad, y, inner, 1); page.Controls.Add(sep)
        key = cd["key"]
        hd = banner_label(page, True, 8.5, "accent")
        hd.Text = "CLAUDE DUET  ·  " + ("TEST  ·  " if cd.get("test") else "") + cd["at"]
        hd.SetBounds(pad, y + 9, inner - 30, 14)
        x = banner_label(page, False, 12.0, "secondary", True)
        x.Text = "×"
        x.Font = Font("Segoe UI", 13.0, FontStyle.Regular, GraphicsUnit.Point)
        x.TextAlign = ContentAlignment.MiddleCenter
        x.SetBounds(w - 2 - pad - 22, y + 5, 24, 22)
        x.Click += (lambda k: (lambda s, e: rt_close(k)))(key)
        body = banner_label(page, False, 10.5, "text", True)
        body.Text = cd["text"]
        bh = min(WF.TextRenderer.MeasureText(cd["text"], body.Font, Size(inner, 0), WF.TextFormatFlags.WordBreak).Height + 4, 64)
        body.AutoEllipsis = True
        body.SetBounds(pad, y + 27, inner, bh)
        body.Click += lambda s, e: (mark_read("reply banner click"), threading.Thread(target=show_tab, args=("claude",), daemon=True).start())
        by = y + 27 + bh + 6
        b = WF.Button()
        listening = cd["phase"] == "listening"
        b.Text = "Send now" if listening else "Reply"
        b.FlatStyle = WF.FlatStyle.Flat
        b.FlatAppearance.BorderSize = 0
        b.BackColor = col("accent") if listening else col("hairline")
        b.ForeColor = col("page") if listening else col("text")
        b.Font = Font("Bahnschrift", 9.5, FontStyle.Bold, GraphicsUnit.Point)
        b.Cursor = WF.Cursors.Hand
        b.TabStop = False
        b.Enabled = cd["phase"] != "sending"
        b.SetBounds(pad, by, 84, 26)
        b.Click += (lambda k: (lambda s, e: rt_reply_click(k)))(key)
        page.Controls.Add(b)
        if cd["status"]:
            st = WF.Label()
            st.AutoSize = False
            st.Font = Font("Segoe UI Symbol", 9.0, FontStyle.Regular, GraphicsUnit.Point)
            st.ForeColor = col("accent") if cd["phase"] == "sent" else col("secondary")
            st.BackColor = col("panel")
            st.Text = cd["status"]
            st.AutoEllipsis = True
            st.TextAlign = ContentAlignment.MiddleLeft
            st.SetBounds(pad + 94, by, inner - 94, 26)
            page.Controls.Add(st)
        y = by + 26 + 10
    ph = y + 2
    page.SetBounds(1, 0, w - 2, ph)
    page.ResumeLayout()
    rt["h_full"] = (ph + 1) if cards else 0


def reply_find_row(row):
    """Worker thread: is that message on the Claude Duet page? Scrolls the chat to the latest once if not."""
    if not row:
        return False
    for attempt in range(3):
        try:
            r = chat.evaluate_js("window.__dbChime && window.__dbChime.findRow ? window.__dbChime.findRow(%s) : 'nohook'" % json.dumps(row))
        except Exception as e:
            r = "error: %s" % e
        if r == "ok":
            return True
        if r != "scrolled":
            log.info("reply: message row %s", r)
            return False
        time.sleep(0.8)
    return False


def reply_start(key):
    """Worker thread (Reply clicked): start an F12-style recording aimed at that card's message."""
    cd = rt_card(key)
    if not cd:
        return
    if state["rec"] or state["busy"] or state.get("pre"):
        rt_set(key, "Mic is busy - try again in a moment", "idle")
        return
    if not reply_find_row(cd["row"]):
        rt_set(key, "Can't find that message on the Claude Duet page", "idle")
        return
    state["reply_to"], state["reply_row"], state["listen_ovr"] = key, cd["row"], rt_listen()
    log.info("reply: listening for a reply to message %s", cd["mid"][-8:])
    ptt_down()
    if not state["rec"]:
        state["reply_to"] = state["listen_ovr"] = None
        rt_set(key, "Mic didn't open", "idle")
        return
    rt_set(key, "Listening  -  stops when you pause, Esc cancels", "listening")


def reply_ended(status, phase="idle"):
    """A reply recording was cancelled (Esc, nothing heard, card closed)."""
    key, state["reply_to"], state["listen_ovr"] = state.get("reply_to"), None, None
    if key:
        rt_set(key, status, phase)


REPLY_JS = r"""
(function(rid){
  const S = window.__dbChime; if (!S || !S.rowFor) return 'nohook';
  const row = S.rowFor(rid); if (!row) return 'norow';
  const cancel = document.querySelector('[data-testid=messages-composer] button[aria-label="Cancel reply"]');
  if (cancel) cancel.click();
  const bub = row.querySelector('[data-row-bubble]') || row;
  const o = {bubbles: true, cancelable: true, pointerType: 'mouse', view: window};
  bub.dispatchEvent(new PointerEvent('pointerover', o));
  bub.dispatchEvent(new MouseEvent('mouseover', o));
  bub.dispatchEvent(new PointerEvent('pointermove', o));
  return 'hovered';
})(%s)
"""

REPLY_CLICK_JS = r"""
(function(rid){
  const S = window.__dbChime; const row = S && S.rowFor(rid); if (!row) return 'norow';
  const b = [...row.querySelectorAll('[data-hover-strip] button')].find(x => x.getAttribute('aria-label') === 'Reply');
  if (!b) return 'nobutton';
  b.click();
  return 'ok';
})(%s)
"""

# The chip on the composer must quote the start of THAT message before anything is sent.
REPLY_CHIP_JS = r"""
(function(rid){
  const S = window.__dbChime; const row = S && S.rowFor(rid);
  const chip = document.querySelector('[data-testid=messages-reply-chip]');
  if (!chip) return 'nochip';
  if (!row) return 'norow';
  const norm = s => (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
  const prose = row.querySelector('[data-cds=Prose]') || row.querySelector('[data-row-bubble]') || row;
  const want = norm(prose.innerText).slice(0, 24), have = norm(chip.innerText.replace(/^\s*replying to:?/i, ''));
  return (want && have.indexOf(want.slice(0, Math.min(16, want.length))) >= 0) ? 'ok' : 'mismatch';
})(%s)
"""

REPLY_PARK_JS = r"""
(function(t, sel){
  const H = window.__dbH;
  const c = document.querySelector('[data-testid=messages-composer] button[aria-label="Cancel reply"]');
  if (c) c.click();
  const box = document.querySelector('[data-testid=messages-composer] textarea') || document.querySelector(sel);
  if (!box) return 'nobox';
  H.setText(box, t); box.blur();
  return 'parked';
})(%s, %s)
"""


def reply_send(text, row):
    """Worker thread: attach the Duet reply to that message (its own Reply button), check the chip, then send with
    the same in-page send F12 uses. Never sends without the chip: then the words are left unsent in the box."""
    def ev(js):
        try:
            return chat.evaluate_js(js)
        except Exception as e:
            return "error: %s" % e
    chip = "nochip"
    for attempt in range(4):
        if attempt:
            reply_find_row(row)
        if ev(COMMON_JS + REPLY_JS % json.dumps(row)) != "hovered":
            continue
        clicked = "nobutton"
        for _ in range(8):
            time.sleep(0.12)
            clicked = ev(REPLY_CLICK_JS % json.dumps(row))
            if clicked == "ok":
                break
        if clicked != "ok":
            log.info("reply: Reply button %s (try %d)", clicked, attempt + 1)
            continue
        for _ in range(12):
            time.sleep(0.12)
            chip = ev(REPLY_CHIP_JS % json.dumps(row))
            if chip in ("ok", "mismatch"):
                break
        if chip == "ok":
            break
        log.info("reply: chip %s (try %d)", chip, attempt + 1)
    if chip != "ok":
        log.warning("reply: could not attach to the message (%s); words left unsent in the box", chip)
        ev(COMMON_JS + REPLY_PARK_JS % (json.dumps(text), json.dumps(CFG["BOX_SELECTOR"])))
        return "noreply"
    how = send_in_page(text, False)
    if how == "sent" and ev("document.querySelector('[data-testid=messages-reply-chip]') ? 'chip' : 'clear'") == "chip":
        log.warning("reply: sent state but the reply chip is still up")
    return how


def toast_test():
    """toast.go / bannertest.go: three test banners, built from the three newest Claude Duet messages on the page
    (so their Reply buttons answer those real messages), marked TEST. Falls back to sample text."""
    picks = []
    try:
        raw = chat.evaluate_js("window.__dbChime && window.__dbChime.lastMessages ? window.__dbChime.lastMessages(3) : '[]'")
        picks = json.loads(raw or "[]")
    except Exception as e:
        log.error("banner test: %s", e)
    if not picks:
        picks = [{"text": "Test banner %d from Claude Duet. It stays until you close it." % i, "mid": "", "row": ""} for i in (1, 2, 3)]
    log.info("banner test: %d banners", len(picks))
    for p in picks:
        reply_toast(p.get("text", ""), p.get("mid", ""), p.get("row", ""), test=True)
        time.sleep(0.4)


# ---- approval banner ----

def approval_card(raw):
    c = aprcfg()
    try:
        d = json.loads(raw)
        cid = str(d["id"])[:80]
    except Exception as e:
        log.error("approval card: bad data %s", e)
        return
    new = cid not in apr["pending"]
    if new:
        unread_mark("approval card")
    if not c["on"]:
        return
    name = re.sub(r"\s+", " ", clean_text(d.get("name"))).strip()[:60]
    apr["pending"][cid] = {"name": name or "a Claude Code session", "body": clean_lines(d.get("body"))[:3000], "clicked": 0.0}
    if new:
        log.info("approval card seen: %s, %d chars, buttons %s", str(d.get("sig") or "")[:120], len(apr["pending"][cid]["body"]), d.get("labels"))
    apr_poke()


def approval_gone(cid):
    if apr["pending"].pop(str(cid)[:80], None) is not None:
        log.info("approval card gone from the tab")
        apr["status"] = ""
    apr_poke()


def apr_poke():
    try:
        from System import Action
        board.native.Invoke(Action(apr_refresh))
    except Exception as e:
        log.error("approval banner: %s", e)


def apr_build(c):
    import System.Windows.Forms as WF
    from System.Drawing import ColorTranslator, Font, FontStyle, GraphicsUnit
    th = theme()
    col = lambda k: ColorTranslator.FromHtml(th[k])
    w = int(c["width"])
    f, page, h = banner_make(w)
    page.SetBounds(1, 0, w - 2, 120)
    banner_tab_mark(page, w - 2)
    ctl = {}
    ctl["head"] = banner_label(page, True, 8.5, "accent")
    ctl["head"].Text = "CLAUDE DUET  ·  NEEDS YOUR OK"
    ctl["title"] = banner_label(page, True, 10.5)
    ctl["bodyp"] = WF.Panel(); ctl["bodyp"].BackColor = col("panel"); page.Controls.Add(ctl["bodyp"])
    ctl["body"] = banner_label(ctl["bodyp"], False, 10.0, "text")
    ctl["more"] = banner_label(page, False, 9.0, "accent", True)
    ctl["status"] = banner_label(page, False, 9.5, "secondary")
    for k, text, fill, fore in (("allow", "Allow", "accent", "page"), ("deny", "Deny", "hairline", "text")):
        b = WF.Button()
        b.Text = text
        b.FlatStyle = WF.FlatStyle.Flat
        b.FlatAppearance.BorderSize = 0
        b.BackColor = col(fill)
        b.ForeColor = col(fore)
        b.Font = Font("Bahnschrift", 10.0, FontStyle.Bold, GraphicsUnit.Point)
        b.Cursor = WF.Cursors.Hand
        b.TabStop = False
        page.Controls.Add(b)
        ctl[k] = b
    ctl["allow"].Click += lambda s, e: apr_press("allow")
    ctl["deny"].Click += lambda s, e: apr_press("deny")

    def toggle(s, e):
        apr["expanded"] = not apr["expanded"]
        apr_refresh()
    ctl["more"].Click += toggle
    apr.update({"form": f, "page": page, "ctl": ctl, "h": h})
    t = WF.Timer()
    t.Interval = 250
    t.Tick += lambda s, e: apr_refresh()                 # re-lays out on status changes, tab switches, minimize
    t.Start()
    apr["timer"] = t
    banner_timer_start()


def apr_press(which):
    cid = next(iter(apr["pending"]), None)
    if not cid or apr["pending"][cid]["clicked"]:
        return
    apr["pending"][cid]["clicked"] = time.time()
    apr["status"] = "Sending %s…" % ("Allow" if which == "allow" else "Deny")
    apr_refresh()
    threading.Thread(target=apr_click, args=(cid, which), daemon=True).start()


def apr_click(cid, which):
    """Matt's click: press the matching button on the real card. Anything but a clean 'ok' is reported."""
    try:
        res = chat.evaluate_js("window.__dbChime && window.__dbChime.clickCard ? window.__dbChime.clickCard(%s, %s) : 'nohook'" % (json.dumps(cid), json.dumps(which)))
    except Exception as e:
        res = "error: %s" % e
    log.info("approval click (%s): %s", which, res)
    if res != "ok":
        apr_fail("Couldn't find the card to %s it." % which)
        return
    time.sleep(4.0)                                      # the card should be gone from the tab by now
    if cid in apr["pending"]:
        apr_fail("The card didn't respond.")


def apr_fail(msg):
    apr["status"] = msg + " Opening Claude Duet."
    apr["fail_until"] = time.time() + 6.0
    apr["pending"].clear()
    apr_poke()
    show_tab("claude")


def apr_refresh():
    try:
        _apr_refresh()
    except Exception as e:
        if time.time() - apr.get("err_t", 0) > 30:
            apr["err_t"] = time.time()
            log.error("approval banner: %s", e)


def _apr_refresh():
    """UI thread: build the banner on first use, then lay out its text and buttons for the card (the slide itself
    is banner_tick's job)."""
    import System.Windows.Forms as WF
    from System.Drawing import Size
    c = aprcfg()
    failing = time.time() < apr["fail_until"]
    if apr["form"] is None:
        if not c["on"] or not (apr["pending"] or failing):
            return
        apr_build(c)
    ctl = apr["ctl"]
    cid = next(iter(apr["pending"]), None)
    card = apr["pending"].get(cid) or {"name": "", "body": "", "clicked": 0.0}
    w = int(c["width"])
    pad = 16
    inner = w - 2 - pad - 14
    waiting = len(apr["pending"]) - 1
    ctl["head"].SetBounds(pad, 9, inner, 14)
    ctl["title"].Text = (("Allow message to %s?" % card["name"]) if cid else "Claude Duet") + (("   (+%d waiting)" % waiting) if waiting > 0 else "")
    ctl["title"].SetBounds(pad, 26, inner, 22)
    body = card["body"]
    long_ = len(body) > int(c["preview_chars"])
    shown = body if (apr["expanded"] or not long_) else body[:int(c["preview_chars"])].rsplit(" ", 1)[0] + "…"
    ctl["body"].Text = shown if cid else ""
    th_ = WF.TextRenderer.MeasureText(ctl["body"].Text, ctl["body"].Font, Size(inner - 18, 0), WF.TextFormatFlags.WordBreak).Height if cid else 0
    body_h = min(th_ + 6, 260 if apr["expanded"] else 120)
    ctl["bodyp"].SetBounds(pad, 52, inner, body_h)
    ctl["bodyp"].AutoScroll = apr["expanded"] and th_ + 6 > 260
    ctl["body"].SetBounds(0, 0, inner - 18, th_ + 6)
    y = 52 + body_h + 4
    ctl["more"].Visible = bool(cid) and long_
    if ctl["more"].Visible:
        ctl["more"].Text = "Show less" if apr["expanded"] else "Show full text"
        ctl["more"].SetBounds(pad, y, 140, 18)
        y += 22
    busy = bool(card["clicked"]) or failing
    ctl["allow"].Visible = ctl["deny"].Visible = not busy and bool(cid)
    ctl["status"].Visible = busy
    ctl["status"].Text = apr["status"]
    ctl["allow"].SetBounds(pad, y + 4, 96, 30)
    ctl["deny"].SetBounds(pad + 104, y + 4, 96, 30)
    ctl["status"].SetBounds(pad, y + 6, inner, 24)
    ph = y + 44
    apr["page"].SetBounds(1, 0, w - 2, ph)
    apr["h_full"] = ph + 1


# ---------- reply chime ----------
# One soft two-note chime when Claude's reply lands in the chat window. The page watches for new
# rows marked data-side="agent" (never Matt's own data-side="user" rows) and calls Api.chime.
# One chime per burst (CHIME_BURST seconds), none for rows already there at load or reload.

CHIME_WAV = os.path.join(ROOT, "chime.wav")
CHIME_BURST = 5.0
chime_state = {"last": 0.0, "played": 0, "skipped": 0}


def make_chime():
    """chime.wav: ~0.3 s, E5 then A5 sine, soft fade in and out, peak at CHIME_VOLUME (0-1).
    The file starts with CHIME_LEAD seconds of silence: the USB DAC (Magni) goes idle when nothing
    plays and mutes the first few hundred ms while it wakes, which swallowed the whole chime."""
    vol = max(0.0, min(1.0, float(CFG.get("CHIME_VOLUME", 0.25))))
    sr = 44100
    y = np.zeros(int(sr * 0.30))
    lead = np.zeros(int(sr * max(0.0, float(CFG.get("CHIME_LEAD", 0.5)))))

    def note(f, start, dur):
        n = int(sr * dur)
        t = np.arange(n) / sr
        env = np.minimum(1.0, t / 0.015) * np.cos(np.linspace(0, np.pi / 2, n)) ** 2   # 15 ms fade in, smooth fade out
        i = int(sr * start)
        y[i:i + n] += np.sin(2 * np.pi * f * t) * env

    note(659.25, 0.00, 0.16)
    note(880.00, 0.11, 0.19)
    y = y / max(1e-9, np.abs(y).max()) * vol
    out = (np.concatenate([lead, y]) * 32767).astype(np.int16)
    with wave.open(CHIME_WAV, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(out.tobytes())


def chime(source="reply", force=False):
    """Plays chime.wav async (never takes focus). Returns 'played', 'off' or 'burst'.
    force skips the one-per-burst rule (pre-alerts, tests)."""
    if not CFG.get("CHIME_ON", True):
        return "off"
    now = time.time()
    if not force and now - chime_state["last"] < CHIME_BURST:
        chime_state["skipped"] += 1
        log.info("chime skipped (burst) from %s", source)
        return "burst"
    chime_state["last"] = now
    chime_state["played"] += 1
    try:
        winsound.PlaySound(CHIME_WAV, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        log.error("chime failed: %s", e)
    log.info("chime played from %s (#%d)", source, chime_state["played"])
    return "played"


def chime_test():
    """chime.go: play the chime once now (ignores the burst window), for checking it's audible."""
    chime_state["last"] = 0.0
    chime("chime.go test")


class Api:
    """Exposed to the chat and board pages as window.pywebview.api."""
    def chime(self, n=1):
        return chime("reply x%s" % int(n or 1))

    def business_from_drive(self, text=""):
        """The board read the Drive mirror of business-status.json; keep the newer copy on the PC."""
        return business_from_drive(text)

    def nudge(self, phase="", title="", mins=0, at=0):
        threading.Thread(target=nudge, args=(phase, title, mins, at), daemon=True).start()
        return True

    def reply_toast(self, text="", mid="", row=""):
        threading.Thread(target=reply_toast, args=(str(text or ""), str(mid or ""), str(row or "")), daemon=True).start()
        return True

    def approval_card(self, raw=""):
        threading.Thread(target=approval_card, args=(str(raw or ""),), daemon=True).start()
        return True

    def approval_gone(self, cid=""):
        threading.Thread(target=approval_gone, args=(str(cid or ""),), daemon=True).start()
        return True

    def tabs(self, view="", focus=""):
        if view in ("today", "focus"):
            tabs["view"] = view
        tabs["focus"] = str(focus or "")[:40]
        threading.Thread(target=update_tabbars, daemon=True).start()
        return True

    def discord(self, show=True):
        threading.Thread(target=discord_show, args=(bool(show),), daemon=True).start()
        return True

    def prealert(self, label=""):
        """The board's timeline heads-up (once per warning stage, decided by the page)."""
        return chime("pre-alert: %s" % str(label)[:80], force=True)


CHIME_JS = r"""
(function(){
  if (window.__dbChime) return 'already';
  const S = window.__dbChime = {seen: new Set(), url: location.href, armed: Date.now() + 5000,
                                last: 0, fired: 0, timer: null};
  // Claude's messages, in page order. A row is one part of a message (data-row-id "cmsg_X:N").
  function agentIds(){
    const out = [];
    document.querySelectorAll('[data-row-id]').forEach(r => {
      const id = (r.getAttribute('data-row-id') || '').split(':')[0];
      if (!id) return;
      const agent = r.matches('[data-side="agent"]') || r.querySelector('[data-side="agent"]');
      const user = r.matches('[data-side="user"]') || r.querySelector('[data-side="user"]');
      if (agent && !user && out[out.length - 1] !== id) out.push(id);
    });
    return out;
  }
  function call(n){
    const api = window.pywebview && window.pywebview.api;
    if (api && api.chime) api.chime(n);
    else window.addEventListener('pywebviewready', () => window.pywebview.api.chime(n), {once: true});
  }
  // Reply banners (11/16 sticky): after a short wait (a reply can arrive in parts), one banner per new Claude message:
  // its text, its message id and its last row id (the row whose Reply button the banner's Reply uses).
  function msgOf(id){
    const parts = []; let last = '';
    document.querySelectorAll('[data-row-id]').forEach(r => {
      const rid = r.getAttribute('data-row-id') || '';
      if (rid.split(':')[0] !== id) return;
      if (r.matches('[data-side="user"]') || r.querySelector('[data-side="user"]')) return;
      const t = ((r.querySelector('[data-cds=Prose]') || r).innerText || '').replace(/\s+/g, ' ').trim();   // the message text only, not its time
      if (t) { parts.push(t); last = rid; }
    });
    return {mid: id, row: last, text: parts.join(' ').slice(0, 500)};
  }
  function toastLater(ids){
    setTimeout(() => {
      const api = window.pywebview && window.pywebview.api;
      ids.forEach(id => {
        try {
          const m = msgOf(id);
          if (m.text && api && api.reply_toast) api.reply_toast(m.text, m.mid, m.row);
        } catch (e) {}
      });
    }, 1200);
  }
  S.rowFor = rid => { try { return document.querySelector('[data-row-id="' + CSS.escape(rid) + '"]'); } catch (e) { return null; } };
  S.findRow = function(rid){
    if (S.rowFor(rid)) return 'ok';
    const j = document.querySelector('[data-testid=jump-to-latest], [data-testid=messages-scroll-to-bottom], button[aria-label="Scroll to bottom"]');
    if (j && j.getClientRects().length) { j.click(); return 'scrolled'; }
    return 'norow';
  };
  S.lastMessages = n => JSON.stringify(agentIds().slice(-n).reverse().map(msgOf).filter(m => m.text).reverse());
  // Approval cards (11/15): a card holding an Allow and a Deny button. Found by text; reported to the host, which shows
  // a toast. clickCard is called only when Matt clicks a toast button: nothing here ever clicks by itself.
  S.cards = new Map();
  function hash(str){ let h = 5381; for (let i = 0; i < str.length; i++) h = ((h * 33) ^ str.charCodeAt(i)) >>> 0; return 'c' + h.toString(36); }
  function btnText(b){ return ((b.innerText || b.textContent || '')).replace(/\s+/g, ' ').trim(); }
  function scanCards(){
    const api = window.pywebview && window.pywebview.api;
    if (!api || !api.approval_card) return;
    const found = new Map();
    document.querySelectorAll('button, [role="button"]').forEach(allow => {
      const t = btnText(allow);
      if (!/^allow\b/i.test(t) || t.length > 20 || !allow.getClientRects().length) return;
      let box = allow.parentElement, deny = null;
      for (let i = 0; box && i < 8; i++, box = box.parentElement) {
        deny = Array.from(box.querySelectorAll('button, [role="button"]')).find(x => /^(deny|decline|reject)\b/i.test(btnText(x)) && btnText(x).length <= 20);
        if (deny) break;
      }
      if (!deny || !box) return;
      const labels = new Set([btnText(allow), btnText(deny), 'Esc', 'Enter', 'Allow', 'Deny', 'Decline']);
      const linesOf = el => (el.innerText || '').split('\n').map(x => x.replace(/\s+/g, ' ').trim()).filter(x => x && !labels.has(x));
      // The nearest box holding both buttons is often just the button row: climb until the card's own text is in it,
      // but never into a box that holds a second Allow button or most of the page.
      for (let g = 0; g < 6 && box.parentElement && linesOf(box).join(' ').length < 60; g++) {
        const par = box.parentElement;
        if ((par.innerText || '').length > 2500) break;
        if (Array.from(par.querySelectorAll('button, [role="button"]')).filter(x => /^allow\b/i.test(btnText(x))).length > 1) break;
        box = par;
      }
      const lines = linesOf(box);
      if (!lines.length) return;
      let name = '', m = null;
      for (const ln of lines.slice(0, 10)) { m = ln.match(/(?:session)\s*[:\-]?\s*["“'`]?([A-Za-z0-9][A-Za-z0-9 _.\-]{1,38})/i); if (m) { name = m[1].trim(); break; } }
      const body = lines.join('\n').slice(0, 3000);
      const id = hash(body.slice(0, 400));
      found.set(id, {box: box, allow: allow, deny: deny, name: name, body: body, labels: [btnText(allow), btnText(deny)]});
    });
    found.forEach((c, id) => {
      const known = S.cards.get(id);
      S.cards.set(id, c);
      if (!known) api.approval_card(JSON.stringify({id: id, name: c.name, body: c.body, labels: c.labels,
        sig: c.box.tagName + '.' + String(c.box.className || '').split(' ').slice(0, 3).join('.')}));
    });
    Array.from(S.cards.keys()).forEach(id => {
      if (!found.has(id)) { S.cards.delete(id); api.approval_gone(id); }
    });
  }
  S.clickCard = function(id, which){
    try {
      let c = S.cards.get(id);
      if (!c || !c.allow.isConnected || !c.deny.isConnected) { scanCards(); c = S.cards.get(id); }
      if (!c) return 'nocard';
      const b = which === 'allow' ? c.allow : c.deny;
      if (!b || !b.isConnected || b.disabled || b.getAttribute('aria-disabled') === 'true') return 'nobutton';
      b.click();
      return 'ok';
    } catch (e) { return 'error: ' + e; }
  };
  function scan(){
    try { scanCards(); } catch (e) {}
    const ids = agentIds();
    let lastSeen = -1;
    ids.forEach((id, i) => { if (S.seen.has(id)) lastSeen = i; });
    const quiet = Date.now() < S.armed || location.href !== S.url || (lastSeen < 0 && S.seen.size > 0);
    if (location.href !== S.url) { S.url = location.href; S.armed = Date.now() + 3000; }
    // Only rows below the newest one already known count: scrolling up into history doesn't chime.
    const fresh = ids.filter((id, i) => i > lastSeen && !S.seen.has(id));
    ids.forEach(id => S.seen.add(id));
    if (quiet || !fresh.length || fresh.length > 3) return;   // load, room switch or a bulk render
    toastLater(fresh);                                          // the reply toast: every new reply, not once per burst
    if (Date.now() - S.last < 5000) return;                     // one chime per burst
    S.last = Date.now(); S.fired++;
    call(fresh.length);
  }
  scan();
  new MutationObserver(() => { clearTimeout(S.timer); S.timer = setTimeout(scan, 250); })
    .observe(document.body, {childList: true, subtree: true});
  return 'installed';
})()
"""


BOARD_IND_JS = r"""
(function(mode){
  let el = document.getElementById('__dbInd');
  if (!el) {
    const st = document.createElement('style');
    st.textContent = `
      #__dbInd{position:fixed;inset:0;pointer-events:none;z-index:2147483647;opacity:0;transition:opacity .15s}
      #__dbInd[data-mode=listen],#__dbInd[data-mode=send]{opacity:1}
      #__dbInd[data-mode=listen]{box-shadow:inset 0 0 0 4px __TEXT__}
      #__dbInd i{position:absolute;top:12px;right:14px;width:14px;height:14px;border-radius:50%;background:__TEXT__}
      #__dbInd[data-mode=listen] i{animation:__dbPulse 1.1s ease-in-out infinite}
      #__dbInd[data-mode=send] i{background:__SECONDARY__;opacity:.85}
      @keyframes __dbPulse{0%,100%{transform:scale(1);opacity:1;box-shadow:0 0 0 0 __TEXT__8C}
        50%{transform:scale(.8);opacity:.6;box-shadow:0 0 0 8px __TEXT__00}}`;
    document.documentElement.appendChild(st);
    el = document.createElement('div'); el.id = '__dbInd'; el.setAttribute('aria-hidden', 'true');
    el.appendChild(document.createElement('i'));
    document.documentElement.appendChild(el);
  }
  el.dataset.mode = mode;
  return mode;
})(__MODE__)
"""


GRAPHITE = {"page": "#131314", "panel": "#1A1A1C", "hairline": "#2A2A2D", "text": "#E8E2D6",
            "secondary": "#A39E94", "muted": "#6B6760", "accent": "#B08D57"}


def theme():
    """config.json THEME over the Graphite defaults; anything that isn't #RRGGBB is ignored."""
    t = dict(GRAPHITE)
    for k, v in (CFG.get("THEME") or {}).items():
        if k in t and isinstance(v, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            t[k] = v
    return t


# The board page runs in a sandboxed frame, so config.json reaches it by message: the day bar's
# sleep schedule and the THEME colours. Sent when the board loads, when the page says hello,
# after reload.go, and once a minute.
BOARD_CFG_JS = r"""
(function(cfg){
  window.__dbBoardCfg = cfg;
  const frame = () => [...document.querySelectorAll('iframe')].find(f => /\.frame\.claudeusercontent\.com\//.test(f.src || ''));
  const send = () => { const f = frame(); if (!f || !f.contentWindow) return 'noframe';
    f.contentWindow.postMessage(window.__dbBoardCfg, new URL(f.src).origin); return 'sent'; };
  if (!window.__dbBoardHello) {
    window.__dbBoardHello = true;
    window.addEventListener('message', e => {
      try {
        if (!/\.frame\.claudeusercontent\.com$/.test(new URL(e.origin).hostname) || !e.data) return;
        if (e.data.type === 'dayboard-hello') send();
        else if (e.data.type === 'dayboard-chime' && window.pywebview && window.pywebview.api)
          window.pywebview.api.prealert(String(e.data.label || '').slice(0, 80));
        else if (e.data.type === 'dayboard-business-drive' && window.pywebview && window.pywebview.api)
          window.pywebview.api.business_from_drive(JSON.stringify(e.data.data || null).slice(0, 20000));
        else if (e.data.type === 'dayboard-discord' && window.pywebview && window.pywebview.api)
          window.pywebview.api.discord(!!e.data.show);
        else if (e.data.type === 'dayboard-nudge' && window.pywebview && window.pywebview.api)
          window.pywebview.api.nudge(String(e.data.phase || ''), String(e.data.title || '').slice(0, 60), Number(e.data.mins) || 0, Number(e.data.at) || 0);
        else if (e.data.type === 'dayboard-tabs' && window.pywebview && window.pywebview.api)
          window.pywebview.api.tabs(String(e.data.view || ''), String(e.data.focus || '').slice(0, 40));
      } catch (x) {}
    });
  }
  return send();
})(__CFG__)
"""
board_cfg_state = {"last": None}


def bizcard_cfg():
    """11/16: config.json BIZ_CARD {"on": true, "seconds": 20}. Layout B shows ONE big business card that cross-fades
    through every business every `seconds` (5-300), holding while the mouse is over it. Off or missing = the tiles."""
    d = dict({"on": False, "seconds": 20}, **(CFG.get("BIZ_CARD") or {}))
    try:
        s = int(d.get("seconds") or 20)
    except Exception:
        s = 20
    return {"on": d.get("on") is True, "seconds": max(5, min(300, s))}


def board_cfg():
    pre = CFG.get("PREALERT") or {}
    return {"type": "dayboard-config", "sleep": CFG.get("SLEEP_SCHEDULE") or [], "theme": theme(),
            "routines": CFG.get("ROUTINES") or [],
            "motion": CFG.get("MOTION") or {},
            "business_drive_file": CFG.get("BUSINESS_DRIVE_FILE_ID", ""),
            "workout_from": CFG.get("WORKOUT_TRACK_FROM", ""),
            "discord": {"on": dcfg()["on"], "shown": state["discord"]}, "tabbar": tabbars_on(),
            "nudge": {"on": ncfg()["on"], "lead": ncfg()["lead_minutes"]},
            "prealert": {k: pre[k] for k in ("rules", "default", "home_words") if k in pre},
            "layout": "B" if dock_on() else "",      # 11/16: "B" only while the chat really is docked beside the page
            "bizcard": bizcard_cfg()}                # 11/16: layout B's one cycling business card (BIZ_CARD); off = the tiles


def push_board_cfg(why="tick"):
    try:
        r = board.evaluate_js(BOARD_CFG_JS.replace("__CFG__", json.dumps(board_cfg())))
        if r != board_cfg_state["last"] or why != "tick":
            log.info("board config %s (%s)", r, why)
        board_cfg_state["last"] = r
    except Exception as e:
        log.error("board config push failed: %s", e)


def board_post(msg):
    """Send one message to the board page (it runs in a sandboxed frame)."""
    js = ("(function(m){const f=[...document.querySelectorAll('iframe')].find(x=>/\\.frame\\.claudeusercontent\\.com\\//.test(x.src||''));"
          "if(!f||!f.contentWindow)return 'noframe';f.contentWindow.postMessage(m,new URL(f.src).origin);return 'sent';})(%s)" % json.dumps(msg))
    return board.evaluate_js(js)


def workout_done():
    """Ctrl+Alt+W (WORKOUT_KEY): mark today's workout Done on the board."""
    try:
        r = board_post({"type": "dayboard-workout-done"})
        sound("sent")
        log.info("workout done key: %s", r)
    except Exception as e:
        log.error("workout done failed: %s", e)


# ---------- business tracker: DayBoard/business-status.json ----------
BIZ_FILE = os.path.join(ROOT, "business-status.json")
biz_state = {"mtime": None}


def biz_time(d):
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(d.get("updated", ""))).timestamp()
    except Exception:
        return 0.0


def biz_valid(d):
    return isinstance(d, dict) and isinstance(d.get("businesses"), list) and all(
        isinstance(b, dict) and isinstance(b.get("name"), str) for b in d["businesses"])


def read_biz():
    try:
        with open(BIZ_FILE, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if biz_valid(d) else None
    except Exception:
        return None


def push_biz(why):
    d = read_biz()
    if d is None:
        log.warning("business-status.json missing or not valid (%s)", why)
        return
    try:
        r = board_post({"type": "dayboard-business", "data": d})
        log.info("business status sent (%s): %s", why, r)
    except Exception as e:
        log.error("business push failed: %s", e)


def biz_watch():
    """Watch business-status.json and send it to the board the moment it is saved."""
    while True:
        try:
            m = os.path.getmtime(BIZ_FILE)
        except OSError:
            m = None
        if m != biz_state["mtime"]:
            first = biz_state["mtime"] is None
            biz_state["mtime"] = m
            if m is not None and not first:
                time.sleep(0.2)   # let the writer finish
                push_biz("file saved")
        time.sleep(1)


def business_from_drive(text):
    try:
        d = json.loads(text)
    except Exception:
        return "bad json"
    if not biz_valid(d):
        return "not valid"
    local = read_biz()
    if local is not None and biz_time(d) <= biz_time(local):
        return "local is current"
    tmp = BIZ_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, BIZ_FILE)
    log.info("business-status.json updated from Drive (updated %s)", d.get("updated"))
    return "written"


def board_cfg_loop():
    while True:
        time.sleep(60)
        push_board_cfg()


def on_board_loaded():
    threading.Timer(2.0, push_board_cfg, args=("board loaded",)).start()
    threading.Timer(2.5, push_biz, args=("board loaded",)).start()


def board_ind(mode):
    """'listen' (pulsing dot + brick-red edge), 'send' (steady amber dot) or 'off'. Never blocks."""
    if not CFG.get("BOARD_GLOW", True):
        return

    def run():
        try:
            th = theme()
            board.evaluate_js(BOARD_IND_JS.replace("__MODE__", json.dumps(mode))
                              .replace("__TEXT__", th["text"]).replace("__SECONDARY__", th["secondary"]))
        except Exception as e:
            log.error("board indicator failed: %s", e)
    threading.Thread(target=run, daemon=True).start()


def show_result(how, with_shot=False):
    if how == "sent":
        sound("sent")
        PILL.show("Sent", "sent", 1.6)
    elif how == "nothing heard":
        sound("fail")
        PILL.show("Didn't catch that", "fail", 2.5)
    else:
        sound("fail")
        PILL.show("Didn't send - check Duet", "fail", 3.0)
    board_ind("off")


# ---------- push to talk ----------

def on_audio(indata, frames, t, status):
    state["frames"].append(indata.copy())
    # Speech detection for auto-send, measured against this room's noise:
    # - the first PTT_NOISE_CAL_SECONDS set the noise floor (20th percentile of the level, so the
    #   press click doesn't count);
    # - the floor only ever moves down afterwards (lowest 1-second 20th percentile: the gaps between
    #   words), so talking during the calibration half second can't lock in a high floor;
    # - speech = level above max(PTT_SILENCE_RMS, floor x PTT_NOISE_MULT) for PTT_SPEECH_MS in a row
    #   (with a short decay), so key clicks and steady game or fan noise never count.
    ms = 1000.0 * frames / RATE
    rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
    vs = state["vad"]
    vs["t"] += ms
    vs["recent"].append(rms)
    if CFG.get("DEBUG"):
        state.setdefault("rms_list", []).append(rms)
    skip = listen_floor_delay_ms()
    low = CFG.get("PTT_SILENCE_RMS", 120)
    if vs["t"] <= skip:                       # speakers still turning down: ignore for the floor
        vs["recent"].clear()
    elif vs["t"] <= skip + 1000.0 * CFG.get("PTT_NOISE_CAL_SECONDS", 0.5):
        vs["cal"].append(rms)                 # measuring the room
    else:
        if vs["floor"] is None:
            vs["floor"] = float(np.percentile(vs["cal"], 20)) if vs["cal"] else 0.0
            vs["thr"] = max(low, vs["floor"] * CFG.get("PTT_NOISE_MULT", 4.0))
            vs["recent"].clear()
            log.info("auto-send: room noise %.0f, speech above %.0f", vs["floor"], vs["thr"])
        if len(vs["recent"]) >= int(1000 / ms):   # every ~1 s: let the floor fall, never rise
            m = float(np.percentile(vs["recent"], 20))
            vs["recent"].clear()
            if m < vs["floor"]:
                vs["floor"] = m
                vs["thr"] = max(low, m * CFG.get("PTT_NOISE_MULT", 4.0))
    # Speech counts from the very first block: until the room is measured, use the plain minimum
    # (PTT_SILENCE_RMS), so talking right after the press is heard within the 1 s start grace.
    if rms > (vs["thr"] if vs["thr"] is not None else low):
        state["loud_ms"] = state.get("loud_ms", 0.0) + ms
        if state["loud_ms"] >= CFG.get("PTT_SPEECH_MS", 200):
            if time.time() - state.get("last_voice", 0) > 1.0 and state.get("countdown"):
                state["countdown"] = None   # talking again: the countdown goes away
            state["last_voice"] = time.time()
            state["spoke"] = True
    else:
        state["loud_ms"] = max(0.0, state.get("loud_ms", 0.0) - ms)


def listen_cfg():
    """config.json LISTEN: one timing for F12 (Claude) and ` (Discord): stop after quiet_seconds
    with no clear speech, or at max_seconds no matter what."""
    L = CFG.get("LISTEN") or {}
    o = state.get("listen_ovr")
    if o:                                  # a banner Reply: its own tight timing
        return float(o["quiet_seconds"]), float(L.get("max_seconds", CFG.get("PTT_MAX_SECONDS", 120)))
    return (float(L.get("quiet_seconds", CFG.get("PTT_SILENCE_SECONDS", 6))),
            float(L.get("max_seconds", CFG.get("PTT_MAX_SECONDS", 120))))


def listen_auto_stop():
    """LISTEN auto_stop (false since 11/15): when false, F12 and ` never stop on silence or time;
    they keep listening until the key is pressed again."""
    return bool(state.get("listen_ovr")) or bool((CFG.get("LISTEN") or {}).get("auto_stop", True))


def listen_grace():
    """LISTEN start_grace_seconds (F12 only): recording starts the instant F12 is pressed, but it
    never auto-stops this early; if none of Matt's own speech is heard by then it is cancelled and
    nothing is sent. Backtick (Discord) is unchanged."""
    o = state.get("listen_ovr")
    if o:
        return float(o["start_grace_seconds"])
    return float((CFG.get("LISTEN") or {}).get("start_grace_seconds", 3))


def listen_voice_wait():
    """LISTEN voice_wait_seconds (F12): how long to wait for Matt's first words before cancelling as
    'nothing heard' (nothing is sent). Never shorter than the start grace."""
    L = CFG.get("LISTEN") or {}
    o = state.get("listen_ovr")
    if o:
        return max(listen_grace(), float(o["voice_wait_seconds"]))
    return max(listen_grace(), float(L.get("voice_wait_seconds", 3)))


def listen_floor_delay_ms():
    """LISTEN floor_delay_ms (F12): skip this much audio before measuring the room's noise floor, so the
    speakers have already turned down (40 ms fade + output latency) and friends' voices from the
    speakers don't set the floor."""
    return float((CFG.get("LISTEN") or {}).get("floor_delay_ms", 150))


def auto_send_watch(gen, label):
    """Toggle mode: stop and send after PTT_SILENCE_SECONDS with no clear speech, or at
    PTT_MAX_SECONDS no matter what (both send, never discard). The pill counts down the last
    PTT_COUNTDOWN_SECONDS. F12 still sends at once; Esc still cancels."""
    if not listen_auto_stop():
        log.info("auto-send watch off: F12 keeps listening until pressed again")
        return
    started = time.time()
    quiet, cap = listen_cfg()
    grace = listen_grace()
    cd = CFG.get("PTT_COUNTDOWN_SECONDS", 5)
    log.info("auto-send watch on (quiet %s s after your speech, no auto-stop for %s s, waits %s s for your voice, cap %s s)",
             quiet, grace, listen_voice_wait(), cap)
    nxt, shown = started + 5, None
    while state["rec"] and state["rec_gen"] == gen:
        now = time.time()
        since = now - state.get("last_voice", started)
        if CFG.get("DEBUG") and now >= nxt:
            nxt = now + 5
            lst, state["rms_list"] = state.get("rms_list", []), []
            vs = state["vad"]
            log.info("auto-send watch: %.1f s since speech, level median %.0f max %.0f, floor %s thr %s",
                     since, float(np.median(lst)) if lst else -1, max(lst) if lst else -1,
                     None if vs["floor"] is None else round(vs["floor"]), None if vs["thr"] is None else round(vs["thr"]))
        el = now - started
        if el >= cap:
            events.put(("auto", (gen, "max")))
            return
        if el < grace:                            # start grace: never stop this early
            time.sleep(0.05)
            continue
        if not state.get("spoke"):                # wait up to voice_wait_seconds for his voice, then cancel
            if el >= listen_voice_wait():
                events.put(("auto", (gen, "nothing")))
                return
            time.sleep(0.05)
            continue
        left = min(quiet - since, cap - el)       # the quiet clock only runs after his speech
        if left <= 0:
            events.put(("auto", (gen, "silence")))
            return
        if cd and left <= cd:
            n = int(math.ceil(left))
            if n != shown:
                shown = n
                state["countdown"] = n
                PILL.show("Sending in %d  -  keep talking to wait, F12 sends now" % n, "listen")
        elif shown is not None:
            shown = None
            state["countdown"] = None
            PILL.show(label, "listen")
        time.sleep(0.1)


def ptt_prestart():
    """F12 pressed while the last recording is still being transcribed and sent: the mic starts
    capturing at once (nothing he says is lost) and ptt_down takes it over when the send is done."""
    pre = {"frames": [], "t": time.time()}
    try:
        s = sd.InputStream(samplerate=RATE, channels=1, dtype="int16",
                           callback=lambda i, f, t, st: pre["frames"].append(i.copy()))
        s.start()
    except Exception as e:
        log.error("mic open failed (early start): %s", e)
        return
    pre["stream"] = s
    state["pre"] = pre
    log.info("F12 press while still sending the last one: listening now, joins when the send is done")
    PILL.show("Listening  -  still sending the last one", "listen")


def pre_take():
    """Stop the early-start stream and return what it captured (or None)."""
    pre, state["pre"] = state.get("pre"), None
    if not pre:
        return None
    try:
        pre["stream"].stop()
        pre["stream"].close()
    except Exception:
        pass
    return pre["frames"]


def ptt_down():
    if state["rec"]:
        return  # key repeat while held
    if state["busy"]:
        if toggle_mode() and not state.get("pre"):
            ptt_prestart()                # still sending the last one: listen now, join after
        return
    with shot_lock:   # F12 within SHOT_WAIT of F11: the question goes with the screenshot
        st = state["shot_t"]
        state["with_shot"] = bool(st and not state["shot_claimed"] and time.time() - st <= CFG.get("SHOT_WAIT", 3.0)
                                  and not state.get("reply_to"))
        if state["with_shot"]:
            state["shot_claimed"] = True
    state["frames"] = []
    # speech-detection state must exist before the first audio block arrives
    state["last_voice"] = time.time()
    state["loud_ms"], state["rms_list"], state["spoke"], state["countdown"] = 0.0, [], False, None
    state["vad"] = {"t": 0.0, "cal": [], "recent": [], "floor": None, "thr": None}
    early = pre_take()
    if early:                           # F12 was pressed during the last send: keep those words
        for b in early:
            on_audio(b, len(b), None, None)
        log.info("F12: %.1f s heard during the last send joined this recording", sum(len(b) for b in early) / RATE)
    sound("press")
    try:
        s = sd.InputStream(samplerate=RATE, channels=1, dtype="int16", callback=on_audio)
        s.start()
    except Exception as e:
        log.error("mic open failed: %s", e)
        sound("fail")
        PILL.show("Mic didn't open", "fail", 2.5)
        return
    state["last_voice"] = time.time()   # the silence clock starts once the mic is open
    state["stream"], state["rec"] = s, True
    state["rec_gen"] += 1
    esc_grab()
    label = "Listening + screenshot" if state["with_shot"] else ("Listening for your reply" if state.get("reply_to") else "Listening")
    if toggle_mode():
        label += "  -  F12 sends, Esc cancels"
    PILL.show(label, "listen")
    board_ind("listen")
    if toggle_mode():   # auto-send after a quiet spell, with a hard cap
        threading.Thread(target=auto_send_watch, args=(state["rec_gen"], label), daemon=True).start()
    try:
        chat.evaluate_js("window.__dbMuted = true; window.speechSynthesis && speechSynthesis.cancel();")
    except Exception:
        pass


def toggle_mode():
    return CFG.get("PTT_MODE", "toggle") == "toggle"


def esc_grab():
    """Swallow Esc only while recording, so it works normally in games and apps otherwise."""
    if state["esc_remove"] is None:
        state["esc_remove"] = keyboard.hook_key("esc", esc_hook, suppress=True)


def esc_release():
    rm, state["esc_remove"] = state["esc_remove"], None
    if rm is not None:
        try:
            rm()
        except Exception as e:
            log.error("esc unhook failed: %s", e)


def esc_hook(e):
    events.put(("esc", e.event_type))   # returns None: Esc is swallowed while this hook exists


def ptt_cancel(label="Cancelled"):
    """Esc while recording (or the time limit): throw the recording away, send nothing,
    clear the indicator."""
    if not state["rec"]:
        return
    try:
        state["stream"].stop()
        state["stream"].close()
    except Exception:
        pass
    state["rec"], state["frames"], state["fake_wav"] = False, [], None
    state["rec_stopped"] = time.time()
    with_shot, state["with_shot"] = state["with_shot"], False
    sound("cancel")
    PILL.show(label, "fail", 1.0 if label == "Cancelled" else 4.0)
    board_ind("off")
    try:
        chat.evaluate_js("window.__dbMuted = false;")
    except Exception:
        pass
    if with_shot:   # the screenshot that was waiting for this question comes back out of the box
        threading.Thread(target=remove_shots, daemon=True).start()
    log.info("ptt cancelled%s", " (screenshot removed)" if with_shot else "")
    if state.get("reply_to"):
        reply_ended("Nothing heard - not sent" if label.startswith("Nothing") else "Cancelled - not sent")


def remove_shots():
    ev = state["shot_done"]
    if ev is not None:
        ev.wait(10)
    names, state["shot_names"] = state["shot_names"], []
    js = ("(function(names){let n=0; document.querySelectorAll('button[aria-label^=\"Remove attachment\"]').forEach(b=>{"
          "if(names.some(x=>b.getAttribute('aria-label')==='Remove attachment, '+x)){b.click();n++;}}); return n;})(%s)"
          % json.dumps(names))
    try:
        log.info("removed %s screenshot(s)", chat.evaluate_js(js))
    except Exception as e:
        log.error("remove screenshot failed: %s", e)


def ptt_up():
    if not state["rec"]:
        return
    if not state["esc_held"]:
        esc_release()
    sound("release")
    PILL.show("Sending", "send")
    board_ind("send")
    time.sleep(0.25)  # catch the tail of the last word
    state["stream"].stop()
    state["stream"].close()
    state["rec"], state["busy"] = False, True
    state["rec_stopped"] = time.time()
    key = state.get("reply_to")
    state["send_reply"] = (key, state.get("reply_row")) if key else None
    state["reply_to"] = state["listen_ovr"] = None
    if key:
        rt_set(key, "Sending…", "sending")
    try:
        chat.evaluate_js("window.__dbMuted = false;")
    except Exception:
        pass
    threading.Thread(target=finish, daemon=True).start()


def speech_only(audio):
    """Simple energy VAD. Returns (audio with silence trimmed, info) or (None, info) when the clip
    is too short or has too little speech to send. Long pauses are squeezed to about 0.6 s so
    whisper never sees long silence, which is what makes it invent or repeat text."""
    info = {"secs": round(len(audio) / RATE, 2)}
    if len(audio) < RATE * CFG.get("MIN_AUDIO_SECONDS", 0.5):
        info["drop"] = "too short"
        return None, info
    n = RATE // 50   # 20 ms frames
    fr = audio[: len(audio) // n * n].astype(np.float32).reshape(-1, n)
    rms = np.sqrt((fr ** 2).mean(axis=1))
    floor = float(np.percentile(rms, 10))
    thr = max(float(CFG.get("VAD_MIN_RMS", 120)), floor * 3.0)
    speech = rms > thr
    info.update(floor=round(floor), thr=round(thr), speech_secs=round(float(speech.sum()) * 0.02, 2))
    if speech.sum() * 0.02 < CFG.get("VAD_MIN_SPEECH_SECONDS", 0.3):
        info["drop"] = "no speech"
        return None, info
    pad = 15   # keep 300 ms either side of speech
    keep = np.convolve(speech.astype(np.int32), np.ones(2 * pad + 1, np.int32), mode="same") > 0
    out = fr[keep].astype(np.int16).reshape(-1)
    info["kept_secs"] = round(len(out) / RATE, 2)
    return out, info


def write_wav(path, audio):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(audio.tobytes())


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16)


def finish():
    with_shot = state["with_shot"]
    try:
        if with_shot:   # make sure the screenshot has landed in the box first
            ev = state["shot_done"]
            if ev is not None:
                ev.wait(10)
            with_shot = state["shot_ok"]
        fake, state["fake_wav"] = state["fake_wav"], None
        if fake:
            audio = read_wav(fake)
        elif state["frames"]:
            audio = np.concatenate(state["frames"]).reshape(-1)
        else:
            audio = np.zeros(0, np.int16)
        clip, vinfo = speech_only(audio)
        log.info("vad %s", vinfo)
        if clip is not None:
            write_wav(WAV, clip)
            result = process(WAV, with_shot)
        else:
            result = process(None, with_shot)
        show_result(result["how"], with_shot)
        reply_result(result["how"])
    except Exception as e:
        log.exception("finish failed: %s", e)
        show_result("error")
        reply_result("error")
    finally:
        state["send_reply"] = None
        state["with_shot"] = False
        state["shot_names"] = []
        state["busy"] = False
        pre = state.get("pre")
        if pre:                         # F12 was pressed during this send: carry on listening
            if time.time() - pre["t"] < 60:
                events.put(("early", None))
            else:
                pre_take()


def reply_result(how):
    sr = state.get("send_reply")
    if not sr:
        return
    msg = {"sent": ("✓  Sent", "sent"), "nothing heard": ("Didn't catch that - not sent", "idle"),
           "noreply": ("Couldn't attach to that message - your words are in the Claude Duet box, not sent", "idle")}
    rt_set(sr[0], *msg.get(how, ("Didn't send - check Claude Duet", "idle")))


def process(wav_path, with_shot=False):
    """Transcribe a WAV and send it (with the screenshot already in the box, if any).
    Returns a summary (no transcript text)."""
    t0 = time.time()
    text = transcribe(wav_path) if wav_path else ""
    r = {"chars": len(text), "stt_seconds": round(time.time() - t0, 2), "sent": False, "how": None,
         "shot": with_shot}
    if not text and not with_shot:
        r["how"] = "nothing heard"
    else:
        reply = state.get("send_reply")
        how = reply_send(text, reply[1]) if (reply and text) else send_in_page(text, with_shot)
        r["how"] = how
        r["reply"] = bool(reply and text)
        if how == "sent":
            r["sent"] = True
            if not text:
                r["how"] = "sent"   # screenshot went alone because nothing was heard
                r["note"] = "nothing heard, screenshot sent alone"
        elif text and not state.get("send_reply") and CFG.get("FLIP_FALLBACK") and how != "busy" and send_with_flip(text):
            r["sent"], r["how"] = True, "flip"
    log.info("ptt result %s", r)
    return r


# ---------- F11 quick-send ----------

def is_own_or_shell(hwnd):
    if not hwnd:
        return True
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == PID:
        return True
    cls = ctypes.create_unicode_buffer(64)
    user32.GetClassNameW(hwnd, cls, 64)
    return cls.value in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "DayBoardPill")


def track_foreground():
    """Remember the last window in front that isn't Day Board, so F11 still shoots the game
    if Matt has just clicked into the Duet chat."""
    while True:
        fg = user32.GetForegroundWindow()
        if not is_own_or_shell(fg):
            state["last_ext"] = fg
        time.sleep(0.25)


def shot_target():
    fg = user32.GetForegroundWindow()
    if not is_own_or_shell(fg):
        return fg
    h = state["last_ext"]
    if h and user32.IsWindow(h) and user32.IsWindowVisible(h) and not user32.IsIconic(h):
        return h
    return fg


ATTACH_JS = r"""
(function(b64, name, boxSel){
  const H = window.__dbH;
  const box = H.target(boxSel);
  if (!box) return 'nobox';
  box.focus();
  const bin = atob(b64), u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  const file = new File([u8], name, {type: 'image/png', lastModified: Date.now()});
  const dt = new DataTransfer(); dt.items.add(file);
  const ev = new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true});
  box.dispatchEvent(ev);
  if (ev.defaultPrevented) return 'paste';
  const inp = document.querySelector('[data-testid="messages-file-input"]') || document.querySelector('input[type=file]');
  if (inp) { inp.files = dt.files; inp.dispatchEvent(new Event('change', {bubbles: true})); return 'input'; }
  return 'none';
})(%s, %s, %s)
"""


def shot_down():
    if state["busy"]:
        sound("fail")
        PILL.show("Still sending - try again", "fail", 2.0)
        return
    with shot_lock:
        state["shot_gen"] += 1
        gen = state["shot_gen"]
        state["shot_t"] = time.time()
        state["shot_claimed"] = state["rec"]       # F12 already held: it goes with this question
        if state["rec"]:
            state["with_shot"] = True
        state["shot_ok"] = False
        state["shot_done"] = done = threading.Event()
    threading.Thread(target=shot_job, args=(gen, done), daemon=True).start()


def shot_job(gen, done):
    t0 = state["shot_t"]
    ok, info = False, {}
    try:
        hwnd = shot_target()
        info["window"] = window_title(hwnd)[:40]
        data, cinfo = capture.grab(hwnd, CFG.get("SHOT_MAX_W", 2560))
        info.update(cinfo, kb=len(data) // 1024, grab_s=round(time.time() - t0, 2))
        name = time.strftime("screenshot-%Y%m%d-%H%M%S.png")
        r = chat.evaluate_js(COMMON_JS + ATTACH_JS % (json.dumps(base64.b64encode(data).decode()),
                                                      json.dumps(name), json.dumps(CFG["BOX_SELECTOR"])))
        info["attach"] = r
        ok = r in ("paste", "input")
        if ok:
            state["shot_names"].append(name)
    except Exception as e:
        log.exception("screenshot failed: %s", e)
        info["error"] = str(e)
    info["total_s"] = round(time.time() - t0, 2)
    log.info("shot %s", info)
    state["shot_ok"] = ok
    done.set()
    if not ok:
        with shot_lock:
            if state["shot_gen"] == gen:
                state["shot_t"] = 0.0
        sound("fail")
        PILL.show("Screenshot didn't attach", "fail", 2.5)
        return
    if not state["shot_claimed"]:
        sound("shot")
        PILL.show("Screenshot ready - F12 to ask" if toggle_mode() else "Screenshot ready - hold F12 to ask", "shot")
    # wait out the rest of the F12 window, then send it alone unless F12 claimed it
    time.sleep(max(0.0, t0 + CFG.get("SHOT_WAIT", 3.0) - time.time()))
    with shot_lock:
        if state["shot_gen"] != gen or state["shot_claimed"]:
            return
        state["shot_t"] = 0.0
        if state["rec"] or state["busy"]:
            return
        state["busy"] = True
    try:
        PILL.show("Sending", "send")
        how = send_in_page("", True)
        log.info("shot sent alone: %s", how)
        show_result(how)
    finally:
        state["shot_names"] = []
        state["busy"] = False


# ---------- typing into the chat ----------

# Shared page helpers, installed once per page load. target() picks the text box Matt is in:
# the focused one (main box or a reply box), else the last one he focused, else the main box.
COMMON_JS = r"""
(function(){
  if (window.__dbH && window.__dbH.v === 3) return;
  const first = !window.__dbH;
  const H = window.__dbH = {v: 3};
  H.editable = e => !!e && e.isConnected && (e.tagName === 'TEXTAREA' || e.isContentEditable)
    && !e.disabled && !e.readOnly && e.getClientRects().length > 0
    && !/search|find/i.test([e.getAttribute('aria-label'), e.getAttribute('role'), e.getAttribute('placeholder')].join(' '));
  H.root = e => (e && e.isContentEditable && e.closest('[contenteditable]:not([contenteditable=false])')) || e;
  if (first) document.addEventListener('focusin', ev => {
    const h = window.__dbH, e = h.root(ev.target); if (h.editable(e)) h.last = e; }, true);
  H.target = function(boxSel){
    const ae = H.root(document.activeElement);
    if (H.editable(ae)) return ae;
    if (H.editable(H.last)) return H.last;
    const m = document.querySelector(boxSel);
    if (H.editable(m)) return m;
    const all = [...document.querySelectorAll('textarea,[contenteditable="true"]')].filter(H.editable);
    return all[all.length - 1] || null;
  };
  H.isSend = (b, sel) => (sel && b.matches(sel)) || b.type === 'submit'
    || /^send\b/i.test(b.getAttribute('aria-label') || b.getAttribute('title') || b.innerText || '');
  // The composer around a box: the nearest ancestor holding a Send button and no other text box.
  H.composer = function(box, sel){
    let n = box.parentElement;
    for (let i = 0; n && i < 14; i++, n = n.parentElement) {
      const others = [...n.querySelectorAll('textarea,[contenteditable="true"]')]
        .filter(x => x !== box && !box.contains(x) && !x.contains(box) && H.editable(x));
      if (others.length) break;
      const btn = [...n.querySelectorAll('button')].find(b => H.isSend(b, sel) && b.getClientRects().length);
      if (btn) return {root: n, btn: btn};
    }
    return {root: box.parentElement, btn: null};
  };
  H.val = box => box.tagName === 'TEXTAREA' ? box.value : box.innerText;
  H.setText = function(box, t){
    box.focus();
    if (box.tagName === 'TEXTAREA') {
      const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      set.call(box, t);
      box.dispatchEvent(new Event('input', {bubbles: true}));
    } else {
      document.execCommand('selectAll', false);
      document.execCommand('insertText', false, t);
    }
  };
  // Attachments waiting in the composer (chips with a "Remove attachment, <name>" button).
  H.media = box => {
    const scope = (box && (box.closest('section') || box.closest('[data-testid=messages-composer]'))) || document;
    const chips = scope.querySelectorAll('button[aria-label^="Remove attachment"]').length;
    return chips || scope.querySelectorAll('[data-testid=messages-composer-files] img').length;
  };
})();
"""

# Puts the text in the box Matt is in, waits for that box's Send button to be ready (a screenshot
# may still be uploading), clicks it (or presses Enter if the box has no button), then checks
# the box emptied. Progress goes to window.__dbSendState, which send_in_page polls.
SEND_JS = r"""
(function(t, boxSel, sendSel, shot){
  const H = window.__dbH;
  const box = H.target(boxSel);
  if (!box) return 'nobox';
  window.__dbSendState = 'waiting';
  window.__dbSendInfo = {reply: !document.querySelector(boxSel) || box !== document.querySelector(boxSel)};
  if (t) H.setText(box, t); else box.focus();
  const start = Date.now();
  let comp = H.composer(box, sendSel);
  function verify(t0, before){
    if (!box.isConnected) { window.__dbSendState = 'sent'; return; }
    const empty = H.val(box).trim() === '';
    const after = H.media(box);
    if (empty && (!shot || before === 0 || after < before)) { window.__dbSendState = 'sent'; return; }
    if (Date.now() - t0 > 5000) { window.__dbSendState = 'busy'; window.__dbSendInfo.media = [before, after]; return; }
    setTimeout(() => verify(t0, before), 150);
  }
  function tick(){
    comp = H.composer(box, sendSel);
    const b = comp.btn;
    const ready = b && !b.disabled && b.getAttribute('aria-disabled') !== 'true';
    const before = H.media(box);
    if (ready) { b.click(); window.__dbSendState = 'clicked'; setTimeout(() => verify(Date.now(), before), 200); return; }
    if (!b && Date.now() - start > 400) {
      const o = {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true};
      box.dispatchEvent(new KeyboardEvent('keydown', o));
      box.dispatchEvent(new KeyboardEvent('keyup', o));
      window.__dbSendState = 'entered'; setTimeout(() => verify(Date.now(), before), 200); return;
    }
    if (Date.now() - start > 20000) { window.__dbSendState = 'stuck'; return; }
    setTimeout(tick, 120);
  }
  setTimeout(tick, 150);
  return 'ok';
})(%s, %s, %s, %s)
"""


def box_text():
    js = ("(function(){const b=document.querySelector(%s); return b ? (b.value !== undefined ? b.value : b.innerText) : null;})()"
          % json.dumps(CFG["BOX_SELECTOR"]))
    return chat.evaluate_js(js)


def send_in_page(text, shot=False):
    """Returns 'sent', 'nobox', 'busy' (text left in the box, Send didn't go), 'stuck' or 'error'."""
    try:
        r = chat.evaluate_js(COMMON_JS + SEND_JS % (json.dumps(text), json.dumps(CFG["BOX_SELECTOR"]),
                                                    json.dumps(CFG["SEND_SELECTOR"]), "true" if shot else "false"))
        if r != "ok":
            return str(r)
        deadline = time.time() + 30
        while time.time() < deadline:
            time.sleep(0.2)
            s = chat.evaluate_js("window.__dbSendState || ''")
            if s in ("sent", "busy", "stuck"):
                info = chat.evaluate_js("JSON.stringify(window.__dbSendInfo || {})")
                log.info("send state %s %s", s, info)
                return s
        return "busy"
    except Exception as e:
        log.error("in-page send failed: %s", e)
        return "error"


def transcribe(wav_path):
    txt = OUT + ".txt"
    if os.path.exists(txt):
        os.remove(txt)
    exe, model = os.path.join(ROOT, CFG["WHISPER"]), os.path.join(ROOT, CFG["MODEL"])
    if os.path.exists(exe) and os.path.exists(model):
        cmd = [exe, "-m", model, "-f", wav_path, "-l", "en", "-t", str(CFG.get("THREADS", 4)),
               "-nt", "-np", "-otxt", "-of", OUT,
               "-mc", "0"] + CFG.get("WHISPER_ARGS", [])   # -mc 0: never prompt with earlier text
    else:
        log.warning("whisper missing, using Windows dictation fallback")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
               os.path.join(ROOT, "sapi-stt.ps1"), wav_path, txt]
    subprocess.run(cmd, cwd=ROOT, creationflags=0x08000000,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(txt):
        return ""
    with open(txt, encoding="utf-8", errors="ignore") as f:
        t = f.read()
    t = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", t)   # drop [BLANK_AUDIO], (music) and similar
    return collapse_repeats(re.sub(r"\s+", " ", t).strip())


def collapse_repeats(t):
    """'A. A. A. B.' -> 'A. B.': whisper sometimes loops one sentence back to back."""
    parts = [p for p in re.split(r"(?<=[.!?])\s+", t) if p]
    key = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
    out = []
    for p in parts:
        if out and key(p) and key(p) == key(out[-1]):
            continue
        out.append(p)
    return " ".join(out)


def send_with_flip(text):
    """Fallback, off unless FLIP_FALLBACK is true. Never taps keys into the game: it only
    types after Windows confirms the chat window is in front, and gives up otherwise."""
    hwnd = own_window(CLAUDE_TITLE)
    if not hwnd:
        return False
    prev = user32.GetForegroundWindow()
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.15)
    if user32.GetForegroundWindow() != hwnd:
        log.warning("flip refused by Windows; nothing typed")
        return False
    chat.evaluate_js("(function(){const b=document.querySelector(%s); if(b) b.focus();})()" % json.dumps(CFG["BOX_SELECTOR"]))
    if user32.GetForegroundWindow() != hwnd:
        return False
    keyboard.write(text, delay=0)
    if user32.GetForegroundWindow() == hwnd:
        keyboard.press_and_release("enter")
    time.sleep(0.15)
    if prev:
        user32.SetForegroundWindow(prev)
    return True


# ---------- voice replies ----------

def toggle_voice():
    state["voice"] = not state["voice"]
    try:
        chat.evaluate_js("window.__dbVoice = %s;" % ("true" if state["voice"] else "false"))
    except Exception:
        pass
    beep(1200 if state["voice"] else 400, 80)
    log.info("voice replies %s", "on" if state["voice"] else "off")


VOICE_JS = """
(function(sel, on){
  window.__dbVoice = on; window.__dbMuted = false;
  if (!sel || window.__dbObs) return;
  let seen = document.querySelectorAll(sel).length, timer = null;
  window.__dbObs = new MutationObserver(function(){
    clearTimeout(timer);
    timer = setTimeout(function(){
      const all = document.querySelectorAll(sel);
      if (all.length <= seen) return;
      seen = all.length;
      if (!window.__dbVoice || window.__dbMuted) return;
      const u = new SpeechSynthesisUtterance(all[all.length - 1].innerText);
      speechSynthesis.cancel(); speechSynthesis.speak(u);
    }, 2500);
  });
  window.__dbObs.observe(document.body, {childList: true, subtree: true, characterData: true});
})(%s, %s)
"""


def on_chat_loaded():
    try:
        chat.evaluate_js(COMMON_JS + VOICE_JS % (json.dumps(CFG["REPLY_SELECTOR"]), "true" if state["voice"] else "false"))
    except Exception as e:
        log.error("voice hook failed: %s", e)
    try:
        log.info("reply chime watcher %s", chat.evaluate_js(CHIME_JS))
    except Exception as e:
        log.error("chime hook failed: %s", e)
    threading.Timer(1.0, place).start()


# ---------- Claude's helpers (trigger files) ----------

PROBE_JS = r"""
(function(){
  const pick = e => ({tag: e.tagName, id: e.id || null,
    cls: (e.className && e.className.toString().slice(0, 160)) || null,
    aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
    ph: e.getAttribute('placeholder') || e.getAttribute('data-placeholder')});
  const r = {url: location.href, title: document.title};
  r.editable = [...document.querySelectorAll('[contenteditable="true"], textarea')].slice(0, 10).map(pick);
  r.buttons = [...document.querySelectorAll('button[aria-label]')].map(b => b.getAttribute('aria-label')).slice(0, 80);
  r.testids = [...new Set([...document.querySelectorAll('[data-testid]')].map(e => e.getAttribute('data-testid')))].slice(0, 150);
  const attrs = new Set();
  document.querySelectorAll('*').forEach(e => { for (const a of e.attributes) if (a.name.startsWith('data-')) attrs.add(a.name); });
  r.dataAttrs = [...attrs].slice(0, 200);
  r.counts = {streaming: document.querySelectorAll('[data-is-streaming]').length,
    fontClaude: document.querySelectorAll('.font-claude-message, .font-claude-response').length,
    reply: %s ? document.querySelectorAll(%s).length : null};
  r.voices = window.speechSynthesis ? speechSynthesis.getVoices().length : -1;
  const vals = {};
  ['data-side', 'data-row-bubble', 'data-part', 'data-surface', 'data-row-cells'].forEach(a => {
    vals[a] = [...new Set([...document.querySelectorAll('[' + a + ']')].map(e => e.getAttribute(a)))].slice(0, 20); });
  r.attrValues = vals;
  r.lastRows = [...document.querySelectorAll('[data-row-id]')].slice(-6).map(e => {
    const o = {}; for (const a of e.attributes) o[a.name] = a.value.slice(0, 60);
    const sides = [...e.querySelectorAll('[data-side]')].map(x => x.getAttribute('data-side'));
    return {attrs: o, sides: [...new Set(sides)], len: e.innerText.length, start: e.innerText.slice(0, 40)}; });
  return JSON.stringify(r);
})()
"""


def probe():
    sel = json.dumps(CFG["REPLY_SELECTOR"])
    out = {}
    for name, win in (("chat", chat), ("board", board)):
        try:
            out[name] = json.loads(win.evaluate_js(PROBE_JS % (sel, sel)) or "{}")
        except Exception as e:
            out[name] = {"error": str(e)}
    with open(os.path.join(ROOT, "probe.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log.info("probe written")


def selftest():
    """Runs the real transcribe + in-page send on selftest.wav and records whether the
    window in front (WoW during the test) ever changed."""
    wav = os.path.join(ROOT, "selftest.wav")
    before = user32.GetForegroundWindow()
    changes, stop = [], threading.Event()

    def watch():
        last = before
        while not stop.is_set():
            fg = user32.GetForegroundWindow()
            if fg != last:
                changes.append(window_title(fg))
                last = fg
            time.sleep(0.02)

    threading.Thread(target=watch, daemon=True).start()
    r = process(wav) if os.path.exists(wav) else {"error": "selftest.wav missing"}
    time.sleep(0.5)
    stop.set()
    r.update({"front_before": window_title(before), "focus_changes": changes})
    with open(os.path.join(ROOT, "selftest.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, indent=1)
    log.info("selftest %s", r)


def bench():
    """Times speech-engine settings on selftest.wav (nothing is sent). Writes bench.json."""
    wav = os.path.join(ROOT, "selftest.wav")
    exe = os.path.join(ROOT, CFG["WHISPER"])
    variants = [
        ("small_gpu_beam5", "ggml-small.en.bin", []),
        ("small_gpu_greedy", "ggml-small.en.bin", ["-bs", "1", "-bo", "1"]),
        ("turbo_gpu_greedy", "ggml-large-v3-turbo-q5_0.bin", ["-bs", "1", "-bo", "1"]),
        ("small_cpu_greedy_8t", "ggml-small.en.bin", ["-bs", "1", "-bo", "1", "-ng", "-t", "8"]),
        ("turbo_cpu_greedy_8t", "ggml-large-v3-turbo-q5_0.bin", ["-bs", "1", "-bo", "1", "-ng", "-t", "8"]),
    ]
    out = []
    for name, model, extra in variants:
        mp = os.path.join(ROOT, "whisper", model)
        if not os.path.exists(mp):
            continue
        for attempt in (1, 2):
            of = os.path.join(ROOT, "bench")
            if os.path.exists(of + ".txt"):
                os.remove(of + ".txt")
            t0 = time.time()
            subprocess.run([exe, "-m", mp, "-f", wav, "-l", "en", "-nt", "-np", "-otxt", "-of", of] + extra,
                           cwd=ROOT, creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            secs = round(time.time() - t0, 2)
            text = open(of + ".txt", encoding="utf-8", errors="ignore").read().strip() if os.path.exists(of + ".txt") else ""
            out.append({"name": name, "run": attempt, "seconds": secs, "text": text})
    with open(os.path.join(ROOT, "bench.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log.info("bench written")


def restart():
    """Start a fresh copy of the app, then quit this one."""
    if state.get("restarting"):
        return                                   # 11/16: never spawn twice
    state["restarting"] = True
    log.info("restarting")
    args = [sys.executable] + ([] if getattr(sys, "frozen", False) else [os.path.abspath(__file__)])
    subprocess.Popen(args, cwd=ROOT)
    # 11/16: a hard stop. os._exit could hang in DLL shutdown (keyboard hook), leaving an old copy holding the WebView2 profile
    try:
        k32 = ctypes.windll.kernel32
        k32.TerminateProcess(k32.GetCurrentProcess(), 0)
    finally:
        os._exit(0)


def reload_cfg():
    global CFG
    CFG = load_cfg()
    state["voice"] = CFG["VOICE_ON"]
    try:
        make_chime()
    except Exception as e:
        log.error("could not make chime: %s", e)
    on_chat_loaded()
    push_board_cfg("config reloaded")
    if dock_on():
        ui_post(dock_layout)                     # a new CHAT_DOCK width takes effect now (on/off needs a restart)
    if dcfg()["on"]:
        discord_gate({"mode": dcfg()["mode"]})
        discord_extra("config reloaded")
    log.info("config reloaded")


def dev_eval():
    """eval.go (only when DEV_EVAL is true): runs eval.js in a window, result to eval.json.
    First line of eval.js is the window: chat or board."""
    if not CFG.get("DEV_EVAL"):
        log.warning("eval.go ignored (DEV_EVAL is off)")
        return
    try:
        with open(os.path.join(ROOT, "eval.js"), encoding="utf-8") as f:
            target, js = f.read().split("\n", 1)
        t = target.strip()
        win = board if t == "board" else (discord_win() if t == "discord" else chat)
        out = {"result": win.evaluate_js(COMMON_JS + js)}
    except Exception as e:
        out = {"error": str(e)}
    with open(os.path.join(ROOT, "eval.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)


def fake_mic():
    """fakemic.go: the next recording uses selftest.wav (or the WAV named in fakemic.txt) instead
    of the microphone, for testing the real key path without speaking. It never starts a
    recording by itself: F12 still has to be pressed."""
    p = os.path.join(ROOT, "fakemic.txt")
    wav = os.path.join(ROOT, "selftest.wav")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            wav = f.read().strip() or wav
        os.remove(p)
    state["fake_wav"] = wav
    log.info("next F12 uses %s", os.path.basename(wav))


TEST_CARD_JS = r"""
(function(){
  document.querySelectorAll('#__dbTestCard').forEach(e => e.remove());
  const d = document.createElement('div'); d.id = '__dbTestCard';
  d.style.cssText = 'position:fixed;left:12px;bottom:12px;z-index:2147483000;background:#222;color:#eee;padding:10px;font:13px sans-serif;border:1px solid #888';
  d.innerHTML = '<div>\uE000</div><div>Message to Claude</div><div>\uE001</div><div>Your computer</div><div>Day Board TEST card (local only, nothing is sent)</div><div>Claude Code session "test-session" wants to send a message</div>'
    + '<div>This is a harmless test of the Allow toast on the Day Board. Clicking Allow or Deny only removes this box.</div>'
    + '<button id="__dbTA">Allow</button> <button id="__dbTD">Deny</button>';
  document.body.appendChild(d);
  document.getElementById('__dbTA').onclick = function(){ window.__dbTestClicked = 'allow'; d.remove(); };
  document.getElementById('__dbTD').onclick = function(){ window.__dbTestClicked = 'deny'; d.remove(); };
  return 'injected';
})()
"""


def card_test():
    """card.go: put a harmless fake Allow/Deny card into the Claude Duet page (local DOM only), so the approval
    toast can be tried end to end. Its buttons only remove the fake card; nothing is sent to any session."""
    try:
        log.info("card test: %s", chat.evaluate_js(TEST_CARD_JS))
    except Exception as e:
        log.error("card test: %s", e)


def watcher():
    jobs = {"probe.go": probe, "selftest.go": selftest, "reload.go": reload_cfg, "place.go": lambda: place(startup=True),
            "bench.go": bench, "restart.go": restart, "eval.go": dev_eval, "fakemic.go": fake_mic,
            "chime.go": chime_test, "toast.go": toast_test, "bannertest.go": toast_test, "card.go": card_test, "discord.go": discord_show, "discordtest.go": discord_selftest, "hudtest.go": hud_test}
    while True:
        time.sleep(1)
        for name, fn in jobs.items():
            p = os.path.join(ROOT, name)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    continue                     # 11/16: can't clear the trigger: don't fire it again and again
                threading.Thread(target=fn, daemon=True).start()


# ---------- keys ----------

events = queue.Queue()


def ptt_hook(e):
    # Runs inside the Windows keyboard hook, so it must return at once; returning None
    # also blocks F12 from reaching the game. The worker thread does the real work.
    events.put(("ptt", e.event_type))


def shot_hook(e):
    # Same for F11: swallowed globally, so Steam / the Claude app never see it.
    events.put(("shot", e.event_type))


def worker():
    while True:
        key, kind = events.get()
        try:
            if key == "ptt":
                now = time.time()
                if kind == "down":
                    last, state["f12_last_down"] = state.get("f12_last_down", 0.0), now
                    # Key repeat while F12 is held. A repeat comes every ~30 ms, so a "held" F12
                    # with no event for 1.5 s means its key-up was lost: treat this as a new press.
                    if state["f12_held"] and now - last < 1.5:
                        continue
                    state["f12_held"] = True
                    if toggle_mode() and state["rec"]:
                        log.info("F12 press: stop and send")
                        state["f12_stopped"] = now
                        ptt_up()                   # second press: stop and send
                    elif toggle_mode() and now - state.get("f12_stopped", 0.0) < CFG.get("PTT_DEBOUNCE", 0.8):
                        log.info("F12 press ignored: double press right after F12 sent")
                    elif toggle_mode() and state.get("pre"):
                        log.info("F12 press: already waiting to listen")
                    else:
                        log.info("F12 press: start recording")
                        ptt_down()                 # first press (or hold mode): start
                else:
                    state["f12_held"] = False
                    if not toggle_mode():
                        ptt_up()                   # hold mode: release sends
            elif key == "esc":
                if kind == "down":
                    state["esc_held"] = True
                    ptt_cancel()
                else:
                    state["esc_held"] = False
                    if not state["rec"]:
                        esc_release()
            elif key == "reply":
                reply_start(kind)
            elif key == "reply_stop":
                if state["rec"] and state.get("reply_to") == kind:
                    log.info("reply: Send now clicked")
                    ptt_up()
            elif key == "early":
                if state.get("pre") and not state["rec"] and not state["busy"]:
                    log.info("F12: last send done, the early start carries on")
                    ptt_down()
            elif key == "auto":
                gen, why = kind
                if state["rec"] and gen == state["rec_gen"]:
                    if why == "nothing":
                        log.info("auto-cancel: none of your speech in the first %s s, nothing sent", listen_voice_wait())
                        ptt_cancel("Nothing heard - not sent")
                        if not state["esc_held"]:
                            esc_release()          # Esc goes back to games and apps
                        continue
                    if why == "silence":
                        log.info("auto-send: %s s quiet after your speech", listen_cfg()[0])
                    else:
                        log.info("auto-send: hit LISTEN max_seconds (%s s), sending", listen_cfg()[1])
                    ptt_up()
            elif kind == "down":
                if not state["f11_held"]:     # ignore key repeat while F11 is held
                    state["f11_held"] = True
                    shot_down()
            else:
                state["f11_held"] = False
        except Exception as e:
            log.exception("key error: %s", e)


def start():
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=watcher, daemon=True).start()
    threading.Thread(target=track_foreground, daemon=True).start()
    threading.Thread(target=board_cfg_loop, daemon=True).start()
    threading.Thread(target=biz_watch, daemon=True).start()
    threading.Thread(target=guard_loop, daemon=True).start()
    threading.Thread(target=audio_mirror, daemon=True).start()
    threading.Thread(target=discord_worker, daemon=True).start()
    keyboard.hook_key(CFG["PTT_KEY"], ptt_hook, suppress=True)
    if CFG.get("SHOT_KEY"):
        keyboard.hook_key(CFG["SHOT_KEY"], shot_hook, suppress=True)
    keyboard.add_hotkey(CFG["VOICE_KEY"], lambda: threading.Thread(target=toggle_voice, daemon=True).start())
    keyboard.add_hotkey(CFG.get("PIN_KEY", "ctrl+alt+t"), lambda: threading.Thread(target=toggle_on_top, daemon=True).start())
    keyboard.add_hotkey(CFG.get("HIDE_KEY", "ctrl+alt+h"), lambda: threading.Thread(target=toggle_hidden, daemon=True).start())
    if CFG.get("WORKOUT_KEY"):
        keyboard.add_hotkey(CFG["WORKOUT_KEY"], lambda: threading.Thread(target=workout_done, daemon=True).start())
    try:
        discord_keys()
    except Exception as e:
        log.error("discord keys: %s", e)
    time.sleep(2)
    place(startup=True)
    build_tabbars()
    state["last_fg"] = user32.GetForegroundWindow()   # the newest window grabs focus at start: ignore that
    state["tabwin"], state["discord"] = "today", False   # always open on the Day Board tab
    if embed_on():
        try:
            embed_tabs()
            show_tab("today")
        except Exception as e:
            log.exception("one window failed, keeping separate tab windows: %s", e)
            tabs.pop("views", None)
    apply_z(raise_=True)
    update_tabbars()
    try:
        board_fit_install()
    except Exception as e:
        log.exception("board fit failed: %s", e)
    start_hud()
    log.info("started; ptt=%s shot=%s sounds=%s", CFG["PTT_KEY"], CFG.get("SHOT_KEY"), CFG.get("PTT_SOUNDS", True))


try:
    make_sounds()
except Exception as e:
    log.error("could not make sounds: %s", e)
try:
    make_chime()
except Exception as e:
    log.error("could not make chime: %s", e)
pill_theme(theme())
pill_mod.PULSE = bool(CFG.get("PILL_PULSE", False))   # steady, no pulsing (11/15)
PILL = Pill(CFG.get("PILL", True))
B, C = layout()
install_webview_hooks()
BG = theme()["page"]
board = webview.create_window("Day Board", CFG["BOARD_URL"], x=B["x"], y=B["y"], width=B["w"], height=B["h"],
                              on_top=state["on_top"], js_api=Api(), background_color=BG,
                              maximized=bool(CFG.get("BOARD_START_MAXIMIZED", True)))
chat = webview.create_window(CLAUDE_TITLE, ccfg()["url"], x=B["x"], y=B["y"], width=B["w"], height=B["h"],
                             on_top=state["on_top"], js_api=Api(), background_color=BG)   # the Claude Duet tab (F12 sends here)
if dcfg()["on"]:
    discord = webview.create_window(DISCORD_TITLE, dcfg()["url"], x=B["x"], y=B["y"], width=B["w"], height=B["h"],
                                    js_api=DiscordApi(), background_color="#313338")
    discord.events.loaded += on_discord_loaded
chat.events.loaded += on_chat_loaded
board.events.loaded += on_board_loaded
menu = [Menu("Day Board", [
    MenuAction("Always on top: on/off   (Ctrl+Alt+T)", lambda: threading.Thread(target=toggle_on_top, daemon=True).start()),
    MenuAction("Claude Duet chat (on the Day Board tab)" if dock_cfg()["on"] else "Claude Duet tab",
               lambda: threading.Thread(target=show_tab, args=("claude",), daemon=True).start()),
    MenuAction("Discord: show / back to the board   (Ctrl+Alt+D)", lambda: threading.Thread(target=discord_show, daemon=True).start()),
    MenuAction("Hide both windows   (Ctrl+Alt+H brings them back)", lambda: threading.Thread(target=toggle_hidden, daemon=True).start()),
    MenuAction("Voice replies: on/off   (Ctrl+Alt+V)", lambda: threading.Thread(target=toggle_voice, daemon=True).start()),
])]
webview.start(start, menu=menu, private_mode=False, storage_path=os.path.join(ROOT, "webdata"), debug=CFG.get("DEBUG", False),
              icon=os.path.join(ROOT, "dayboard.ico"))   # window + taskbar icon (Matt's sun icon, 11/15)
