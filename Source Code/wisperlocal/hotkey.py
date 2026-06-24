"""Global hotkey listener built on pynput.

Tracks the set of currently-pressed keys so it can support both a single
activation (toggle mode) and a held-combo with release detection
(push-to-talk mode). Uses virtual-key codes for letters/digits so combos
resolve correctly even while modifiers are held (pynput's `char` is
unreliable under Ctrl/Alt on Windows).
"""

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


class HotkeyManager:
    """Fires on_activate when the full combo becomes pressed, and on_deactivate
    when it is subsequently released. Callbacks run on the listener thread, so
    they must return quickly (dispatch heavy work elsewhere)."""

    def __init__(self, combo: str, on_activate, on_deactivate=None):
        self.required = parse_combo(combo)
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate
        self._pressed: set[str] = set()
        self._active = False
        self._listener = None
        self._lock = threading.Lock()

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._pressed.clear()
        self._active = False

    def _on_press(self, key) -> None:
        tok = _token(key)
        if tok is None:
            return
        with self._lock:
            self._pressed.add(tok)
            should_fire = not self._active and self.required and self.required.issubset(self._pressed)
            if should_fire:
                self._active = True
        if should_fire:
            try:
                self.on_activate()
            except Exception as exc:
                print(f"[hotkey] on_activate error: {exc}")

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
            try:
                self.on_deactivate()
            except Exception as exc:
                print(f"[hotkey] on_deactivate error: {exc}")
