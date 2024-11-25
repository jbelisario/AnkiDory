from __future__ import annotations

from typing import Optional, List
from aqt import AnkiQt
from aqt.qt import *
from aqt.utils import tooltip
from anki.cards import Card
from anki.utils import int_time
from anki.llm import llm_manager

class GuideMe:
    """Manages the Guide Me feature functionality."""
    
    def __init__(self, mw: AnkiQt):
        self.mw = mw
        
    def show_hint(self, card: Card) -> None:
        """Show a hint for the current card."""
        if not card:
            return
            
        # Get card content
        question = card.question()
        answer = card.answer()
        card_content = f"Question: {question}\nAnswer: {answer}"
        
        # Get previous hints
        previous_hints = card.get_hints()
        
        # Generate new hint
        hint = llm_manager.generate_hint(card_content=card_content, previous_hints=previous_hints)
        
        if hint.startswith("Error"):
            tooltip(hint)
            return
            
        # Store the hint
        card.add_hint(hint)
        
        # Show the hint in a dialog
        self._show_hint_dialog(hint, len(previous_hints) + 1)
        
    def _show_hint_dialog(self, hint: str, hint_number: int) -> None:
        """Display the hint in a dialog box."""
        dialog = QDialog(self.mw)
        dialog.setWindowTitle("Guide Me - Hint")
        
        layout = QVBoxLayout()
        
        # Hint number label
        hint_label = QLabel(f"Hint #{hint_number}:")
        hint_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addWidget(hint_label)
        
        # Hint text
        hint_text = QLabel(hint)
        hint_text.setWordWrap(True)
        hint_text.setStyleSheet("margin: 10px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(hint_text)
        
        # Close button
        close_btn = QPushButton("Got it!")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.resize(400, 200)
        dialog.exec_()
