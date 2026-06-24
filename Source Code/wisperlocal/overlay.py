"""Floating "listening" overlay — a small frameless pill near the bottom of the
screen that shows a live waveform while recording, with cancel (X) and insert
(check) buttons, then a "Transcribing..." state.

It never takes keyboard focus (WS_EX_NOACTIVATE on Windows), so the caret stays
in whatever app the user was typing in and the paste lands correctly.
"""

import math
import sys
from collections import deque

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget

W, H = 290, 60
BAR_W, BAR_GAP = 3, 3
ACCENT = QColor("#3B82F6")
ACCENT_OK = QColor("#22C55E")
DANGER = QColor("#EF4444")
PILL_BG = QColor(24, 24, 27, 235)
TEXT = QColor("#E5E7EB")


class ListeningOverlay(QWidget):
    cancelClicked = Signal()
    confirmClicked = Signal()

    def __init__(self, level_provider=None):
        super().__init__(None)
        self.level_provider = level_provider
        self.enabled = True
        self._state = "hidden"   # recording | transcribing | done | error | hidden
        self._levels: deque[float] = deque(maxlen=64)
        self._phase = 0.0
        self._cancel_rect = None
        self._confirm_rect = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(W, H)

        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)

    # ---------------------------------------------------------------- showing
    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            try:
                import ctypes

                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                WS_EX_TOOLWINDOW = 0x00000080
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
            except Exception:
                pass

    def _reposition(self):
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + geo.height() - self.height() - 90
        self.move(x, y)

    # ------------------------------------------------------------- public API
    def on_status(self, status: str):
        if not self.enabled:
            return
        if status == "recording":
            self._start_recording()
        elif status in ("transcribing", "enhancing"):
            if self._state != "hidden":
                self._state = status
                self.update()
        elif status in ("idle", "error"):
            if self._state in ("recording", "transcribing", "enhancing"):
                self._finish(ok=(status != "error"))

    def _start_recording(self):
        self._state = "recording"
        self._levels.clear()
        self._reposition()
        if not self.isVisible():
            self.show()
        if not self._timer.isActive():
            self._timer.start()
        self.update()

    def _finish(self, ok=True):
        self._state = "done" if ok else "error"
        self.update()
        QTimer.singleShot(700, self._do_hide)

    def _do_hide(self):
        if self._state in ("done", "error"):  # don't hide if a new recording began
            self._timer.stop()
            self._state = "hidden"
            self.hide()

    # ---------------------------------------------------------------- ticking
    def _tick(self):
        self._phase += 0.18
        if self._state == "recording" and self.level_provider is not None:
            try:
                raw = float(self.level_provider())
            except Exception:
                raw = 0.0
            disp = min(1.0, (max(0.0, raw) ** 0.5) * 1.7)
            self._levels.append(disp)
        self.update()

    # ----------------------------------------------------------------- mouse
    def mousePressEvent(self, event):
        if self._state != "recording":
            return
        pos = event.position()
        if self._confirm_rect is not None and self._confirm_rect.contains(pos):
            self.confirmClicked.emit()
        elif self._cancel_rect is not None and self._cancel_rect.contains(pos):
            self.cancelClicked.emit()
            # Hide immediately so the idle status doesn't flash "Inserted".
            self._timer.stop()
            self._state = "hidden"
            self.hide()

    # --------------------------------------------------------------- painting
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        p.fillPath(path, PILL_BG)

        if self._state == "recording":
            self._paint_recording(p, w, h)
        elif self._state == "transcribing":
            self._paint_busy(p, w, h, "Transcribing…")
        elif self._state == "enhancing":
            self._paint_busy(p, w, h, "Enhancing…")
        elif self._state == "done":
            self._paint_message(p, w, h, ACCENT_OK, "✓", "Inserted")
        elif self._state == "error":
            self._paint_message(p, w, h, DANGER, "!", "Try again")
        p.end()

    def _paint_recording(self, p, w, h):
        cy = h / 2
        r = 14
        confirm_c = QPointF(w - 16 - r, cy)
        cancel_c = QPointF(w - 16 - r - 2 * r - 10, cy)
        self._confirm_rect = QRectF(confirm_c.x() - r, confirm_c.y() - r, 2 * r, 2 * r)
        self._cancel_rect = QRectF(cancel_c.x() - r, cancel_c.y() - r, 2 * r, 2 * r)

        # red recording dot
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(DANGER))
        p.drawEllipse(QPointF(20, cy), 5, 5)

        # waveform bars
        x0 = 36
        x1 = cancel_c.x() - r - 12
        p.setBrush(QBrush(ACCENT))
        count = max(1, int((x1 - x0) // (BAR_W + BAR_GAP)))
        levels = list(self._levels)[-count:]
        if len(levels) < count:
            levels = [0.0] * (count - len(levels)) + levels
        max_h = h * 0.55
        x = x0
        for i, lv in enumerate(levels):
            shimmer = 0.10 + 0.05 * (1 + math.sin(self._phase + i * 0.5))
            bh = max(3.0, (lv if lv > 0.02 else shimmer) * max_h)
            p.drawRoundedRect(QRectF(x, cy - bh / 2, BAR_W, bh), 1.5, 1.5)
            x += BAR_W + BAR_GAP

        self._draw_circle_button(p, cancel_c, r, QColor(255, 255, 255, 28), DANGER, "x")
        self._draw_circle_button(p, confirm_c, r, ACCENT, QColor("white"), "check")

    def _paint_busy(self, p, w, h, label):
        self._cancel_rect = self._confirm_rect = None
        cy = h / 2
        pen = QPen(ACCENT)
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        start = int(-self._phase * 70 * 16) % (360 * 16)
        p.drawArc(QRectF(18, cy - 11, 22, 22), start, 100 * 16)
        p.setPen(TEXT)
        p.setFont(QFont("Segoe UI", 11))
        p.drawText(QRectF(52, 0, w - 60, h), Qt.AlignVCenter | Qt.AlignLeft, label)

    def _paint_message(self, p, w, h, color, glyph, text):
        cy = h / 2
        self._draw_circle_button(p, QPointF(28, cy), 13, color, QColor("white"),
                                 "check" if glyph == "✓" else "bang")
        p.setPen(TEXT)
        p.setFont(QFont("Segoe UI", 11))
        p.drawText(QRectF(52, 0, w - 60, h), Qt.AlignVCenter | Qt.AlignLeft, text)

    def _draw_circle_button(self, p, center, r, fill, fg, glyph):
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(fill))
        p.drawEllipse(center, r, r)
        pen = QPen(fg)
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        cx, cy = center.x(), center.y()
        if glyph == "x":
            d = r * 0.42
            p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
            p.drawLine(QPointF(cx - d, cy + d), QPointF(cx + d, cy - d))
        elif glyph == "check":
            p.drawLine(QPointF(cx - r * 0.42, cy + r * 0.02), QPointF(cx - r * 0.08, cy + r * 0.36))
            p.drawLine(QPointF(cx - r * 0.08, cy + r * 0.36), QPointF(cx + r * 0.45, cy - r * 0.34))
        elif glyph == "bang":
            p.drawLine(QPointF(cx, cy - r * 0.45), QPointF(cx, cy + r * 0.12))
            p.drawPoint(QPointF(cx, cy + r * 0.4))
