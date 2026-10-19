"""Modern floating popup card displaying recognized Japanese text and definitions."""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QApplication,
)

from src.nlp.parser import Token


class WordCard(QWidget):
    """Card widget for a single parsed Japanese token."""

    def __init__(self, token: Token, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Header row: Surface word + Reading + Base Form
        header = QHBoxLayout()
        header.setSpacing(8)

        surface_label = QLabel(token.surface)
        surface_font = QFont("Noto Sans CJK JP", 14, QFont.Weight.Bold)
        surface_label.setFont(surface_font)
        surface_label.setStyleSheet("color: #89b4fa;")
        header.addWidget(surface_label)

        if token.reading and token.reading != token.surface:
            reading_label = QLabel(f"[{token.reading}]")
            reading_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
            header.addWidget(reading_label)

        if token.dictionary_form != token.surface:
            base_label = QLabel(f"Base: {token.dictionary_form}")
            base_label.setStyleSheet(
                "color: #f9e2af; font-size: 11px; background-color: #313244; padding: 2px 6px; border-radius: 4px;"
            )
            header.addWidget(base_label)

        pos_label = QLabel(token.pos_category)
        pos_label.setStyleSheet(
            "color: #cdd6f4; font-size: 10px; background-color: #45475a; padding: 2px 6px; border-radius: 4px;"
        )
        header.addWidget(pos_label)
        header.addStretch()

        layout.addLayout(header)

        # Meaning list
        for idx, entry in enumerate(token.definitions[:2], start=1):
            for meaning in entry.get("meanings", [])[:2]:
                meaning_label = QLabel(f"• {meaning}")
                meaning_label.setWordWrap(True)
                meaning_label.setStyleSheet("color: #bac2de; font-size: 12px;")
                layout.addWidget(meaning_label)

        self.setStyleSheet(
            """
            WordCard {
                background-color: #181825;
                border-radius: 6px;
                border: 1px solid #313244;
            }
        """
        )


class ResultPopup(QDialog):
    """Floating borderless dictionary card for OCR results."""

    def __init__(
        self,
        text: str,
        tokens: list[Token],
        latency_ms: float,
        pos: QPoint | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("eigopop")
        self.setWindowTitle("Eigopop")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setMinimumWidth(380)
        self.setMaximumWidth(460)
        self.setMaximumHeight(500)

        # Main container with styled rounded border
        container = QWidget(self)
        container.setObjectName("Container")
        container.setStyleSheet(
            """
            QWidget#Container {
                background-color: #1e1e2e;
                border: 1.5px solid #89b4fa;
                border-radius: 10px;
            }
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        inner_layout = QVBoxLayout(container)
        inner_layout.setContentsMargins(14, 12, 14, 12)
        inner_layout.setSpacing(10)

        # Top Bar: Title & Latency badge & Close button
        top_bar = QHBoxLayout()
        title_label = QLabel("EIGOPOP")
        title_label.setStyleSheet(
            "color: #cdd6f4; font-size: 11px; font-weight: bold; letter-spacing: 1px;"
        )
        top_bar.addWidget(title_label)

        latency_badge = QLabel(f"⚡ {latency_ms:.0f} ms")
        latency_badge.setStyleSheet(
            "color: #a6e3a1; font-size: 10px; background-color: #313244; padding: 2px 6px; border-radius: 4px;"
        )
        top_bar.addWidget(latency_badge)
        top_bar.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(
            "background-color: #313244; color: #cdd6f4; border: none; padding: 3px 8px; border-radius: 4px; font-size: 11px;"
        )
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text))
        top_bar.addWidget(copy_btn)

        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "background-color: transparent; color: #a6adc8; border: none; font-size: 13px;"
        )
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)

        inner_layout.addLayout(top_bar)

        # Full Recognized Text Box
        recognized_label = QLabel(text)
        recognized_label.setFont(QFont("Noto Sans CJK JP", 14, QFont.Weight.Medium))
        recognized_label.setWordWrap(True)
        recognized_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        recognized_label.setStyleSheet(
            "background-color: #11111b; color: #f5e0dc; padding: 8px 10px; border-radius: 6px; border: 1px solid #313244;"
        )
        inner_layout.addWidget(recognized_label)

        # Scrollable List of Content Word Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        words_container = QWidget()
        words_layout = QVBoxLayout(words_container)
        words_layout.setContentsMargins(0, 0, 0, 0)
        words_layout.setSpacing(8)

        content_tokens = [t for t in tokens if t.is_content_word]
        if not content_tokens:
            content_tokens = tokens  # fallback if no content words detected

        for token in content_tokens:
            if token.definitions:
                words_layout.addWidget(WordCard(token))

        words_layout.addStretch()
        scroll.setWidget(words_container)
        inner_layout.addWidget(scroll)

        # Positioning: near the given cursor/snip point, or center of screen
        if pos:
            screen = QApplication.primaryScreen().availableGeometry()
            target_x = min(pos.x() + 20, screen.width() - 480)
            target_y = min(pos.y() + 20, screen.height() - 520)
            self.move(max(target_x, 10), max(target_y, 10))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
