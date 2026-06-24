"""Home / onboarding window shown on first run and when the tray icon is
double-clicked. Friendlier than raw Settings: live status, how-to, a quick
model picker, a 'Test my system' button, and a scratch box to try dictation."""

import threading
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import formatting
from .audio import Recorder
from .settings_window import SettingsWindow

MODEL_PRESETS = [
    ("Fast — tiny", "tiny.en"),
    ("Balanced — small (recommended)", "small.en"),
    ("Accurate — medium", "medium.en"),
    ("Most accurate — large-v3 turbo", "large-v3-turbo"),
]

TEST_SECONDS = 4


def _pretty_hotkey(combo: str) -> str:
    return "+".join(part.capitalize() for part in combo.split("+"))


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color:#dddddd;")
    return line


class MainWindow(QWidget):
    settingsSaved = Signal()
    _sigTestStatus = Signal(str)
    _sigTestResult = Signal(str, bool)
    _sigTestDone = Signal()

    def __init__(self, config, controller):
        super().__init__()
        self.config = config
        self.controller = controller
        self.settings_window: SettingsWindow | None = None

        self.setWindowTitle("WisperLocal")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 18, 20, 18)

        title = QLabel("WisperLocal")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        root.addWidget(title)

        self.welcome = QLabel(
            "👋 Welcome! Pick a model, run a quick test, then press your hotkey "
            "in any app to dictate."
        )
        self.welcome.setWordWrap(True)
        self.welcome.setStyleSheet("color:#2563EB;")
        root.addWidget(self.welcome)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 13px;")
        root.addWidget(self.status_label)

        self.howto = QLabel()
        self.howto.setWordWrap(True)
        self.howto.setStyleSheet("color:#555;")
        root.addWidget(self.howto)

        root.addWidget(_hline())

        # Model quick-picker
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self._build_model_combo()
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_row.addWidget(self.model_combo, 1)
        root.addLayout(model_row)

        # System test
        test_row = QHBoxLayout()
        self.test_btn = QPushButton("🎤  Test my system")
        self.test_btn.clicked.connect(self._start_test)
        test_row.addWidget(self.test_btn)
        self.test_status = QLabel("")
        self.test_status.setWordWrap(True)
        test_row.addWidget(self.test_status, 1)
        root.addLayout(test_row)

        # Scratch / try-it box
        root.addWidget(QLabel("Try it here — click in the box, press your hotkey, and talk:"))
        self.scratch = QPlainTextEdit()
        self.scratch.setPlaceholderText("Your dictated text will appear here…")
        self.scratch.setFixedHeight(90)
        root.addWidget(self.scratch)

        # Buttons
        btn_row = QHBoxLayout()
        settings_btn = QPushButton("Open Settings…")
        settings_btn.clicked.connect(self.open_settings)
        btn_row.addWidget(settings_btn)
        btn_row.addStretch(1)
        close_btn = QPushButton("Close to tray")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        # signals
        self._model_state = "loading"
        self._dl_text = ""
        self._sigTestStatus.connect(self.test_status.setText)
        self._sigTestResult.connect(self._on_test_result)
        self._sigTestDone.connect(self._on_test_done)
        controller.statusChanged.connect(lambda *_: self._refresh_status())
        controller.modelStatusChanged.connect(self._on_model_state)
        controller.modelProgress.connect(self._on_model_progress)

        self.welcome.setVisible(not config.get("first_run_done"))
        self._refresh_status()
        self._refresh_howto()

    # --------------------------------------------------------------- helpers
    def _build_model_combo(self):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        current = self.config.get("model")
        values = [v for _, v in MODEL_PRESETS]
        for label, value in MODEL_PRESETS:
            self.model_combo.addItem(label, value)
        if current not in values:
            self.model_combo.addItem(f"Current — {current}", current)
        idx = self.model_combo.findData(current)
        self.model_combo.setCurrentIndex(max(0, idx))
        self.model_combo.blockSignals(False)

    def _on_model_state(self, state):
        self._model_state = state
        self._refresh_status()

    def _on_model_progress(self, text):
        self._dl_text = text
        if self._model_state == "downloading":
            self._refresh_status()

    def _refresh_status(self):
        state = self.controller.state
        dev = (self.controller.transcriber.active_device or self.config.get("device")).upper()
        model = self.config.get("model")
        if state in ("recording", "transcribing", "enhancing"):
            dot = {"recording": "🔴", "transcribing": "🟡", "enhancing": "🟣"}[state]
            label = {"recording": "Recording…", "transcribing": "Transcribing…",
                     "enhancing": "Enhancing…"}[state]
            self.status_label.setText(f"{dot}  {label}   ·   {model} ({dev})")
            return
        ms = self._model_state
        if ms == "downloading":
            self.status_label.setText(f"⬇️  {self._dl_text or 'Downloading model…'}")
        elif ms == "loading":
            self.status_label.setText(f"⏳  Loading model…   ·   {model} ({dev})")
        elif ms == "error":
            self.status_label.setText(f"⚫  Model problem — check the tray   ·   {model}")
        else:
            self.status_label.setText(f"🟢  Ready   ·   model: {model} ({dev})")

    def _refresh_howto(self):
        combo = _pretty_hotkey(self.config.get("hotkey"))
        mode = self.config.get("record_mode")
        action = ("Hold " + combo + " and speak; release to insert."
                  if mode == "push_to_talk"
                  else f"Press {combo}, speak, then press {combo} again.")
        self.howto.setText(f"How to use:  {action}  The text is pasted wherever your cursor is.")

    # --------------------------------------------------------------- actions
    def show_and_raise(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.raise_()
        self.activateWindow()

    def _on_model_changed(self):
        value = self.model_combo.currentData()
        if not value or value == self.config.get("model"):
            return
        self.config.set("model", value)
        self.config.save()
        self.controller.apply_settings()
        self._refresh_status()

    def open_settings(self):
        if self.settings_window is not None and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = SettingsWindow(self.config)
        self.settings_window.saved.connect(self._on_settings_saved)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_settings_saved(self):
        self.controller.apply_settings()
        self._build_model_combo()
        self._refresh_status()
        self._refresh_howto()
        self.settingsSaved.emit()

    # ------------------------------------------------------------ system test
    def _start_test(self):
        if not self.controller.model_ready:
            self.test_status.setStyleSheet("color:#DC2626;")
            self.test_status.setText("Model is still preparing — wait until the status shows 'Ready'.")
            return
        self.test_btn.setEnabled(False)
        self.test_status.setStyleSheet("color:#555;")
        threading.Thread(target=self._test_worker, daemon=True).start()

    def _test_worker(self):
        try:
            rec = Recorder(device=self.config.get("input_device"))
            rec.start()
            for s in range(TEST_SECONDS, 0, -1):
                self._sigTestStatus.emit(f"🎙️ Listening… speak now ({s})")
                time.sleep(1)
            audio = rec.stop()
            self._sigTestStatus.emit("Transcribing…")
            text = self.controller.transcriber.transcribe(
                audio,
                language=self.controller.current_language(),
                vad_filter=self.config.get("vad_filter"),
            )
            text = formatting.format_with_config(text, self.config)
            if text:
                self._sigTestResult.emit(f'✓ It works! Heard: "{text}"', True)
            else:
                self._sigTestResult.emit("No speech detected — check your mic in Settings.", False)
        except Exception as exc:
            self._sigTestResult.emit(f"✗ Error: {exc}", False)
        finally:
            self._sigTestDone.emit()

    def _on_test_result(self, message: str, ok: bool):
        self.test_status.setStyleSheet("color:#16A34A;" if ok else "color:#DC2626;")
        self.test_status.setText(message)

    def _on_test_done(self):
        self.test_btn.setEnabled(True)

    # ------------------------------------------------------------------ close
    def closeEvent(self, event):
        if not self.config.get("first_run_done"):
            self.config.set("first_run_done", True)
            self.config.save()
            self.welcome.setVisible(False)
        event.ignore()
        self.hide()
