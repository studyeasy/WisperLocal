"""Application entry point: build the Qt app, controller, windows, and tray."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from . import APP_NAME, __version__
from .config import Config
from .controller import Controller
from .icons import make_icon
from .main_window import MainWindow
from .overlay import ListeningOverlay
from .tray import TrayApp


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)  # closing a window must not exit
    app.setWindowIcon(make_icon("idle"))

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, APP_NAME, "No system tray is available on this system.")
        return 1

    config = Config()
    controller = Controller(config)

    # Floating listening overlay (waveform + cancel/insert).
    overlay = ListeningOverlay(level_provider=lambda: controller.recorder.get_level())
    overlay.enabled = bool(config.get("show_overlay"))
    controller.statusChanged.connect(overlay.on_status)
    overlay.cancelClicked.connect(controller.cancel)
    overlay.confirmClicked.connect(controller.confirm)

    main_window = MainWindow(config, controller)
    tray = TrayApp(app, config, controller, main_window)

    def _on_settings_saved():
        overlay.enabled = bool(config.get("show_overlay"))
        tray.refresh_header()

    main_window.settingsSaved.connect(_on_settings_saved)

    controller.preload_model()

    combo = "+".join(p.capitalize() for p in config.get("hotkey").split("+"))
    if not config.get("first_run_done"):
        main_window.show_and_raise()
    else:
        tray.tray.showMessage(
            APP_NAME,
            f"v{__version__} running in the tray. Press {combo} to dictate.",
            make_icon("idle"),
            4000,
        )

    return app.exec()
