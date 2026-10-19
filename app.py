"""Main application entrypoint for Eigopop with native Wayland & X11 support."""

import sys
import time
import argparse
from pathlib import Path
from PIL import Image

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from src.vision.ocr import OCREngine
from src.nlp.parser import JapaneseParser
from src.dict.lookup import DictionaryEngine
from src.capture.screen import ScreenCapture
from src.ui.snipper import SnippingOverlay
from src.ui.popup import ResultPopup


class EigopopController:
    """Core controller coordinating OCR, NLP, and UI components."""

    def __init__(self, force_cpu: bool = False):
        print("\n" + "=" * 50)
        print("   Initializing EIGOPOP Engines...")
        print("=" * 50)
        self.ocr = OCREngine(force_cpu=force_cpu)
        self.parser = JapaneseParser(mode="C")
        self.dictionary = DictionaryEngine()
        self.capture = ScreenCapture()
        self.active_popup: ResultPopup | None = None
        self.active_snipper: SnippingOverlay | None = None
        print(f"[Ready] All engines active (Wayland: {self.capture.is_wayland}).\n")

    def process_image(
        self, image: Image.Image, display_pos: QPoint | tuple[int, int] | None = None
    ) -> ResultPopup | None:
        """Run OCR, NLP, and dictionary lookup on an image, then show ResultPopup."""
        t_start = time.perf_counter()

        # 1. Vision OCR
        text, ocr_time = self.ocr.recognize(image)
        if not text:
            print("[Eigopop] No Japanese text recognized in crop.")
            return None

        # 2. NLP Tokenization & De-inflection
        tokens = self.parser.parse(text)

        # 3. Dictionary Lookup
        for token in tokens:
            if token.is_content_word:
                entries = self.dictionary.lookup_word(
                    token.dictionary_form, max_entries=2
                )
                token.definitions = [
                    {
                        "meanings": e.meanings,
                        "pos": e.pos,
                        "kana": e.kana,
                    }
                    for e in entries
                ]

        total_latency = (time.perf_counter() - t_start) * 1000
        print(f"[Eigopop] Recognized: '{text}' in {total_latency:.1f}ms")

        # 4. Display Result Popup
        if self.active_popup:
            self.active_popup.close()

        point_pos = None
        if isinstance(display_pos, tuple):
            point_pos = QPoint(display_pos[0], display_pos[1])
        elif isinstance(display_pos, QPoint):
            point_pos = display_pos

        self.active_popup = ResultPopup(
            text=text,
            tokens=tokens,
            latency_ms=total_latency,
            pos=point_pos,
        )
        self.active_popup.show()
        return self.active_popup

    def trigger_snip(self):
        """Trigger screen region selection."""
        if self.active_popup:
            self.active_popup.close()

        # If on Wayland and slurp is available, use native layer-shell slurp (NEVER gets tiled!)
        if self.capture.is_wayland and self.capture.has_slurp:
            img, pos = self.capture.select_and_capture_wayland()
            if img:
                self.process_image(img, display_pos=pos)
            return

        # Fallback to Qt full-screen overlay (X11)
        self.active_snipper = SnippingOverlay(capture_engine=self.capture)
        self.active_snipper.snip_completed.connect(self.process_image)
        self.active_snipper.show()


class ControlWindow(QMainWindow):
    """Small floating control toolbar with Snip button."""

    def __init__(self, controller: EigopopController):
        super().__init__()
        self.controller = controller
        self.setObjectName("eigopop")
        self.setWindowTitle("Eigopop")
        self.setFixedSize(280, 110)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog
        )

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("EIGOPOP")
        title.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #89b4fa; letter-spacing: 1px;"
        )
        status = QLabel("● Ready")
        status.setStyleSheet("color: #a6e3a1; font-size: 10px;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(status)

        exit_btn = QPushButton("✕")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setToolTip("Quit Eigopop (Esc / q)")
        exit_btn.setStyleSheet(
            "background-color: transparent; color: #a6adc8; border: none; font-size: 13px; font-weight: bold; padding: 0 4px;"
        )
        exit_btn.clicked.connect(QApplication.quit)
        header.addWidget(exit_btn)

        layout.addLayout(header)

        snip_btn = QPushButton("✂  Snip Japanese Text (Alt+S)")
        snip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        snip_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                font-weight: bold;
                padding: 8px 12px;
                border-radius: 6px;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:pressed {
                background-color: #74c7ec;
            }
        """
        )
        snip_btn.clicked.connect(self.controller.trigger_snip)
        layout.addWidget(snip_btn)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e2e;
            }
        """
        )

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            QApplication.quit()
        elif event.key() == Qt.Key.Key_S and (
            event.modifiers() & Qt.KeyboardModifier.AltModifier
        ):
            self.controller.trigger_snip()
        else:
            super().keyPressEvent(event)


def main():
    parser = argparse.ArgumentParser(
        description="Eigopop: Japanese On-Screen OCR Popup Assistant"
    )
    parser.add_argument(
        "--image", type=str, help="Path to image file for CLI test"
    )
    parser.add_argument(
        "--cpu", action="store_true", help="Force CPU inference"
    )
    args = parser.parse_args()

    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Error: Image not found at {image_path}")
            sys.exit(1)

        controller = EigopopController(force_cpu=args.cpu)
        img = Image.open(image_path).convert("RGB")
        text, latency = controller.ocr.recognize(img)
        print(f"\nRecognized: {text} ({latency:.1f}ms)")
        tokens = controller.parser.parse(text)
        for t in tokens:
            if t.is_content_word:
                entries = controller.dictionary.lookup_word(t.dictionary_form)
                m = entries[0].meanings[0] if entries else "N/A"
                print(f"  - {t.surface} (Base: {t.dictionary_form}) -> {m}")
        return

    # Set application ID for Wayland window matching
    import signal
    from PyQt6.QtCore import QTimer

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("eigopop")
    app.setDesktopFileName("eigopop")

    # Periodic timer to let Python process POSIX signals (Ctrl+C)
    sig_timer = QTimer()
    sig_timer.timeout.connect(lambda: None)
    sig_timer.start(250)

    controller = EigopopController(force_cpu=args.cpu)
    window = ControlWindow(controller)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
