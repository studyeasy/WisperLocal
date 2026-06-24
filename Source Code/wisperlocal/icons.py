"""Programmatically drawn tray icons (no image assets needed)."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap

STATE_COLORS = {
    "idle": "#3B82F6",          # blue
    "loading": "#9CA3AF",       # gray
    "recording": "#EF4444",     # red
    "transcribing": "#F59E0B",  # amber
    "enhancing": "#8B5CF6",     # violet
    "error": "#6B7280",         # dark gray
}


def make_icon(state: str = "idle") -> QIcon:
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    color = QColor(STATE_COLORS.get(state, STATE_COLORS["idle"]))
    p.setBrush(QBrush(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, size - 4, size - 4)

    # microphone capsule
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(
        QRectF(size * 0.385, size * 0.22, size * 0.23, size * 0.34),
        size * 0.115, size * 0.115,
    )

    # stand arc + base
    pen = QPen(QColor("white"))
    pen.setWidth(4)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(size * 0.30, size * 0.24, size * 0.40, size * 0.42), 200 * 16, 140 * 16)
    p.drawLine(int(size * 0.5), int(size * 0.655), int(size * 0.5), int(size * 0.76))
    p.drawLine(int(size * 0.40), int(size * 0.78), int(size * 0.60), int(size * 0.78))

    p.end()
    return QIcon(pm)
