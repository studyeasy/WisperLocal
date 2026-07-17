"""Global hotkey listener built on pynput.

Tracks the set of currently-pressed keys so it can support both a single
activation (toggle mode) and a held-combo with release detection
(push-to-talk mode). Uses virtual-key codes for letters/digits so combos
resolve correctly even while modifiers are held (pynput's `char` is
unreliable under Ctrl/Alt on Windows).

Robustness: Windows silently drops low-level hook events when a hook callback
is slow (LowLevelHooksTimeout), which used to leave a phantom "still pressed"
combo that made the hotkey unresponsive until restart. Two defenses:
  * Callbacks are dispatched on a dedicated worker thread so the hook
    callback itself returns immediately.
  * On every key press the tracked state is re-checked against the real
    keyboard state (GetAsyncKeyState), so a missed release self-heals.
"""

import ctypes
import queue
import sys
import threading

from pynput import keyboard

_MODS = {
    keyboard.Key.ctrl: "ctrl", keyboard.Key.ctrl_l: "ctrl", keyboard.Key.ctrl_r: "ctrl",
    keyboard.Key.alt: "alt", keyboard.Key.alt_l: "alt", keyboard.Key.alt_r: "alt",
    keyboard.Key.alt_gr: "alt",
    keyboard.Key.shift: "shift", keyboard.Key.shift_l: "shift", keyboard.Key.shift_r: "shift",
    keyboard.Key.cmd: "win", keyboard.Key.cmd_l: "win", keyboard.Key.cmd_r: "win",
}

_ALIASES = {
    "control": "ctrl", "ctl": "ctrl",
    "windows": "win", "super": "win", "cmd": "win", "meta": "win",
    "option": "alt", "opt": "alt",
    "esc": "escape", "return": "enter",
}

# Virtual-key codes for tokens whose real state we can query on Windows.
_TOKEN_VKS = {
    "ctrl": (0x11,), "alt": (0x12,), "shift": (0x10,), "win": (0x5B, 0x5C),
    "space": (0x20,), "escape": (0x1B,), "enter": (0x0D,), "tab": (0x09,),
}


def normalize_token(token: str) -> str:
    token = token.strip().lower()
    return _ALIASES.get(token, token)


def parse_combo(combo: str) -> set[str]:
    tokens = set()
    for part in combo.lower().replace(" ", "").split("+"):
        if part:
            tokens.add(normalize_token(part))
    return tokens


def _token(key) -> str | None:
    if key in _MODS:
        return _MODS[key]
    if isinstance(key, keyboard.Key):
        return key.name.lower()  # space, f1..f12, escape, etc.
    if isinstance(key, keyboard.KeyCode):
        vk = key.vk
        if vk is not None:
            if 0x30 <= vk <= 0x5A:        # 0-9, A-Z
                return chr(vk).lower()
            if 0x60 <= vk <= 0x69:        # numpad 0-9
                return str(vk - 0x60)
        if key.char:
            return key.char.lower()
    return None


def _vks_for(token: str):
    if token in _TOKEN_VKS:
        return _TOKEN_VKS[token]
    if len(token) == 1:
        ch = token.upper()
        if "0" <= ch <= "9" or "A" <= ch <= "Z":
            return (ord(ch),)
    if token.startswith("f") and token[1:].isdigit():
        n = int(token[1:])
        if 1 <= n <= 24:
            return (0x70 + n - 1,)
    return None


def _physically_down(token: str) -> bool | None:
    """Real key state from the OS: True/False, or None if unqueryable."""
    if sys.platform != "win32":
        return None
    vks = _vks_for(token)
    if not vks:
        return None
    try:
        user32 = ctypes.windll.user32
        return any(user32.GetAsyncKeyState(vk) & 0x8000 for vk in vks)
    except Exception:
        return None


class HotkeyManager:
    """Fires on_activate when the full combo becomes pressed, and on_deactivate
    when it is subsequently released. Callbacks are run on a dedicated
    dispatcher thread (never on the OS hook thread), so slow callbacks cannot
    make Windows drop hook events."""

    def __init__(self, combo: str, on_activate, on_deactivate=None):
        self.required = parse_combo(combo)
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate
        self._pressed: set[str] = set()
        self._active = False
        self._listener = None
        self._lock = threading.Lock()
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._dispatcher: threading.Thread | None = None

    def start(self) -> None:
        self._dispatcher = threading.Thread(
            target=self._dispatch_loop, daemon=True, name="hotkey-dispatch"
        )
        self._dispatcher.start()
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._dispatcher is not None:
            self._queue.put(None)  # sentinel: end dispatch loop
            self._dispatcher = None
        self._pressed.clear()
        self._active = False

    # ------------------------------------------------------------- dispatch
    def _dispatch_loop(self) -> None:
        while True:
            fn = self._queue.get()
            if fn is None:
                return
            try:
                fn()
            except Exception as exc:
                print(f"[hotkey] callback error: {exc}")

    def _resync_locked(self, ignore: str | None = None) -> bool:
        """Drop tracked keys the OS says are no longer held (missed releases).

        Returns True if this uncovered a missed release of the active combo,
        in which case _active has been cleared so the combo can fire again.
        """
        missed_release = False
        for tok in list(self._pressed):
            if tok == ignore:
                continue
            if _physically_down(tok) is False:
                self._pressed.discard(tok)
                if self._active and tok in self.required:
                    self._active = False
                    missed_release = True
        return missed_release

    # --------------------------------------------------------------- events
    def _on_press(self, key) -> None:
        tok = _token(key)
        if tok is None:
            return
        with self._lock:
            missed_release = self._resync_locked(ignore=tok)
            self._pressed.add(tok)
            should_fire = not self._active and self.required and self.required.issubset(self._pressed)
            if should_fire:
                self._active = True
        if missed_release and self.on_deactivate is not None:
            self._queue.put(self.on_deactivate)
        if should_fire:
            self._queue.put(self.on_activate)

    def _on_release(self, key) -> None:
        tok = _token(key)
        if tok is None:
            return
        with self._lock:
            fire_release = self._active and tok in self.required
            if fire_release:
                self._active = False
            self._pressed.discard(tok)
        if fire_release and self.on_deactivate is not None:
            self._queue.put(self.on_deactivate)
