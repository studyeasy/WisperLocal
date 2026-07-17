"""Transcription history viewer (opened with the history hotkey or tray menu).

Shows the most recent dictations newest-first; selecting one previews the full
text, and Copy puts it back on the clipboard so a failed or lost paste can be
recovered.
"""

import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

PREVIEW_CHARS = 80


def _item_label(entry: dict) -> str:
    ts = entry.get("ts")
    try:
        when = datetime.datetime.fromtimestamp(float(ts)).strftime("%d %b %H:%M")
    except (TypeError, ValueError, OSError, OverflowError):
        when = "--:--"
    text = " ".join(entry.get("text", "").split())
    if len(text) > PREVIEW_CHARS:
        text = text[: PREVIEW_CHARS - 1] + "…"
    return f"[{when}]  {text}"


class HistoryWindow(QWidget):
    def __init__(self, history):
        super().__init__()
        self.history = history

        self.setWindowTitle("WisperLocal — Transcription history")
        self.resize(560, 420)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 14, 16, 14)

        hint = QLabel(
            "Recent dictations, newest first. Select one and press Copy "
            "(or double-click it) to put it back on the clipboard."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#555;")
        root.addWidget(hint)

        self.listing = QListWidget()
        self.listing.currentRowChanged.connect(self._on_select)
        self.listing.itemDoubleClicked.connect(lambda _item: self._copy_selected())
        root.addWidget(self.listing, 2)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Select an entry above to see the full text…")
        root.addWidget(self.preview, 1)

        btn_row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy to clipboard")
        self.copy_btn.clicked.connect(self._copy_selected)
        btn_row.addWidget(self.copy_btn)
        self.status = QLabel("")
        self.status.setStyleSheet("color:#16A34A;")
        btn_row.addWidget(self.status, 1)
        clear_btn = QPushButton("Clear history")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        self._entries: list[dict] = []

    # --------------------------------------------------------------- actions
    def refresh(self) -> None:
        self._entries = self.history.entries()
        self.listing.clear()
        for entry in self._entries:
            self.listing.addItem(QListWidgetItem(_item_label(entry)))
        self.preview.clear()
        self.status.setText("")
        if self._entries:
            self.listing.setCurrentRow(0)
        else:
            self.preview.setPlaceholderText("No transcriptions yet — dictate something first.")

    def show_and_raise(self) -> None:
        self.refresh()
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.raise_()
        self.activateWindow()

    def _on_select(self, row: int) -> None:
        if 0 <= row < len(self._entries):
            self.preview.setPlainText(self._entries[row]["text"])
            self.status.setText("")

    def _copy_selected(self) -> None:
        row = self.listing.currentRow()
        if not (0 <= row < len(self._entries)):
            return
        QGuiApplication.clipboard().setText(self._entries[row]["text"])
        self.status.setText("✓ Copied — press Ctrl+V where you need it.")

    def _clear(self) -> None:
        self.history.clear()
        self.refresh()
