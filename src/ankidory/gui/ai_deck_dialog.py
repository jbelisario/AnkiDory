"""Dialog for AI deck generation settings."""

import logging
from typing import Callable, Optional

from aqt import gui_hooks
from aqt.qt import *
from aqt.utils import disable_help_button, restoreGeom, saveGeom, showInfo, tr

logger = logging.getLogger(__name__)

class AIDeckDialog(QDialog):
    """Dialog for configuring AI deck generation."""
    
    def __init__(self, parent: QWidget, deck_name: str, on_confirm: Callable[[dict], None]) -> None:
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            deck_name: Name of the deck being created
            on_confirm: Callback when settings are confirmed
        """
        super().__init__(parent)
        self.deck_name = deck_name
        self.on_confirm = on_confirm
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle(f"AI Deck Settings - {self.deck_name}")
        self.setMinimumWidth(400)
        disable_help_button(self)
        restoreGeom(self, "aiDeckDialog")
        
        layout = QVBoxLayout()
        
        # Topic input
        topic_group = QGroupBox("Topic")
        topic_layout = QVBoxLayout()
        self.topic_input = QPlainTextEdit()  
        self.topic_input.setPlaceholderText("Enter the topic for your deck (e.g. 'Basic Python Programming')\n\nFeel free to provide more context or specific areas you'd like to focus on.")
        self.topic_input.setMinimumHeight(100)  
        topic_layout.addWidget(self.topic_input)
        topic_group.setLayout(topic_layout)
        layout.addWidget(topic_group)
        
        # Difficulty level
        difficulty_group = QGroupBox("Difficulty Level")
        difficulty_layout = QVBoxLayout()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Intermediate", "Advanced"])
        difficulty_layout.addWidget(self.difficulty_combo)
        difficulty_group.setLayout(difficulty_layout)
        layout.addWidget(difficulty_group)
        
        # Number of cards
        cards_group = QGroupBox("Number of Cards")
        cards_layout = QVBoxLayout()
        self.cards_spin = QSpinBox()
        self.cards_spin.setRange(2, 50)
        self.cards_spin.setValue(10)
        cards_layout.addWidget(self.cards_spin)
        cards_group.setLayout(cards_layout)
        layout.addWidget(cards_group)
        
        # Model selection
        model_group = QGroupBox("LLM Model")
        model_layout = QVBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama-3.1-8b-instant", "mixtral-8x7b-32768"])
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _on_accept(self) -> None:
        """Handle dialog acceptance."""
        topic_text = self.topic_input.toPlainText().strip()  
        if not topic_text:
            showInfo("Please enter a topic for your deck.")
            return
            
        settings = {
            "topic": topic_text,
            "difficulty": self.difficulty_combo.currentText(),
            "num_cards": self.cards_spin.value(),
            "model": self.model_combo.currentText(),
        }
        
        self.accept()
        saveGeom(self, "aiDeckDialog")
        self.on_confirm(settings)
