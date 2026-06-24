"""System tray icon, status display, and menu."""

from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .icons import make_icon

_STATUS_TEXT = {
    "idle": "Ready",
    "recording": "Recording...",
    "transcribing": "Transcribing...",
    "enhancing": "Enhancing...",
    "error": "Error - check settings",
}


class TrayApp:
    def __init__(self, app, config, controller, main_window):
        self.app = app
        self.config = config
        self.controller = controller
        self.main_window = main_window

        self._status = "idle"
        self._model_status = "loading"
        self._last_info = ""
        self._dl_text = ""

        self.tray = QSystemTrayIcon(make_icon("idle"))
        self.tray.setToolTip("WisperLocal")
        self._build_menu()
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        controller.statusChanged.connect(self._on_status)
        controller.modelStatusChanged.connect(self._on_model_status)
        controller.modelProgress.connect(self._on_model_progress)
        controller.info.connect(self._on_info)
        self._refresh()

    # ------------------------------------------------------------------- menu
    def _build_menu(self) -> None:
        menu = QMenu()
        self.header = menu.addAction(self._hotkey_label())
        self.header.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Open WisperLocal", self.main_window.show_and_raise)
        menu.addAction("Start / stop dictation", self.controller.toggle)
        menu.addAction("Settings...", self.main_window.open_settings)
        menu.addSeparator()
        menu.addAction("Quit", self.quit)
        self.tray.setContextMenu(menu)

    def _hotkey_label(self) -> str:
        combo = self.config.get("hotkey")
        pretty = "+".join(p.capitalize() for p in combo.split("+"))
        mode = "hold" if self.config.get("record_mode") == "push_to_talk" else "press"
        return f"Hotkey: {pretty} ({mode})"

    def refresh_header(self) -> None:
        self.header.setText(self._hotkey_label())
        self._refresh()

    # ---------------------------------------------------------------- signals
    def _on_status(self, status: str) -> None:
        self._status = status
        self._refresh()

    def _on_model_status(self, status: str) -> None:
        self._model_status = status
        if status == "ready":
            self.tray.showMessage("WisperLocal", "Model ready. Press your hotkey to dictate.",
                                  make_icon("idle"), 3000)
        elif status == "error":
            self.tray.showMessage("WisperLocal", self._last_info or "Model failed to load.",
                                  make_icon("error"), 6000)
        elif status == "downloading":
            self.tray.showMessage("WisperLocal", "Downloading the selected model...",
                                  make_icon("loading"), 3000)
        self._refresh()

    def _on_info(self, message: str) -> None:
        self._last_info = message
        lowered = message.lower()
        if "error" in lowered or "failed" in lowered:
            self.tray.showMessage("WisperLocal", message, make_icon("error"), 5000)
        self._refresh()

    # ---------------------------------------------------------------- display
    def _on_model_progress(self, text: str) -> None:
        self._dl_text = text
        if self._model_status == "downloading":
            self._refresh()

    def _refresh(self) -> None:
        icon_state = self._status
        if self._status == "idle" and self._model_status in ("loading", "downloading"):
            icon_state = "loading"
        self.tray.setIcon(make_icon(icon_state))

        status = _STATUS_TEXT.get(self._status, "Ready")
        if self._status == "idle":
            if self._model_status == "downloading":
                status = self._dl_text or "Downloading model..."
            elif self._model_status == "loading":
                status = "Loading model..."

        tip = f"WisperLocal - {status}"
        if self._last_info and self._model_status != "downloading":
            tip += f"\n{self._last_info}"
        self.tray.setToolTip(tip)

    # ----------------------------------------------------------------- actions
    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show_and_raise()

    def quit(self) -> None:
        try:
            self.controller.shutdown()
        finally:
            self.tray.hide()
            self.app.quit()
