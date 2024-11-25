from typing import Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QPushButton,
    QWidget,
    QTabWidget,
    QSpinBox
)
from PyQt6.QtCore import Qt
from aqt import mw
from ..config import Config

class AISettingsDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = Config()
        self.setup_ui()

    def setup_ui(self):
        """Initialize the dialog UI components"""
        self.setWindowTitle("AI Settings")
        self.setMinimumWidth(800)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Model Selection Section
        model_section = QWidget()
        model_layout = QHBoxLayout()
        model_section.setLayout(model_layout)

        model_label = QLabel("LLM Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mixtral-8x7b",
            "llama-3.1-8b-instant"
        ])
        current_model = self.config.get("llm", "model", fallback="mixtral-8x7b")
        self.model_combo.setCurrentText(current_model)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        layout.addWidget(model_section)

        # Tabs for different prompts
        tabs = QTabWidget()
        
        # Card Generation Tab
        card_tab = QWidget()
        card_layout = QVBoxLayout()
        card_tab.setLayout(card_layout)
        
        card_label = QLabel("Card Generation Prompt:")
        card_layout.addWidget(card_label)
        
        self.card_prompt_edit = QTextEdit()
        current_card_prompt = self.config.get_card_prompt()
        self.card_prompt_edit.setText(current_card_prompt)
        card_layout.addWidget(self.card_prompt_edit)
        
        # Card prompt character counter
        card_counter_layout = QHBoxLayout()
        self.card_char_counter = QLabel("0/4000 characters")
        card_counter_layout.addStretch()
        card_counter_layout.addWidget(self.card_char_counter)
        card_layout.addLayout(card_counter_layout)
        
        tabs.addTab(card_tab, "Card Generation")
        
        # Hint Generation Tab
        hint_tab = QWidget()
        hint_layout = QVBoxLayout()
        hint_tab.setLayout(hint_layout)
        
        hint_label = QLabel("Hint Generation Prompt:")
        hint_layout.addWidget(hint_label)
        
        self.hint_prompt_edit = QTextEdit()
        current_hint_prompt = self.config.get_hint_prompt()
        self.hint_prompt_edit.setText(current_hint_prompt)
        hint_layout.addWidget(self.hint_prompt_edit)
        
        # Hint prompt character counter
        hint_counter_layout = QHBoxLayout()
        self.hint_char_counter = QLabel("0/2000 characters")
        hint_counter_layout.addStretch()
        hint_counter_layout.addWidget(self.hint_char_counter)
        hint_layout.addLayout(hint_counter_layout)
        
        tabs.addTab(hint_tab, "Hint Generation")
        
        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Default")
        self.reset_button.clicked.connect(self.reset_prompts)
        
        self.save_button = QPushButton("Save")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)

        # Connect signals
        self.card_prompt_edit.textChanged.connect(lambda: self.update_char_counter(self.card_prompt_edit, self.card_char_counter, 4000))
        self.hint_prompt_edit.textChanged.connect(lambda: self.update_char_counter(self.hint_prompt_edit, self.hint_char_counter, 2000))
        self.update_char_counter(self.card_prompt_edit, self.card_char_counter, 4000)
        self.update_char_counter(self.hint_prompt_edit, self.hint_char_counter, 2000)

    def update_char_counter(self, text_edit: QTextEdit, counter: QLabel, max_chars: int):
        """Update character counter for a text edit"""
        count = len(text_edit.toPlainText())
        counter.setText(f"{count}/{max_chars} characters")
        if count > max_chars:
            counter.setStyleSheet("color: red;")
        else:
            counter.setStyleSheet("")

    def reset_prompts(self):
        """Reset prompts to default values"""
        self.card_prompt_edit.setText(self.config.get_default_card_prompt())
        self.hint_prompt_edit.setText(self.config.get_default_hint_prompt())

    def save_settings(self):
        """Save the current settings"""
        # Save model selection
        self.config.set("llm", "model", self.model_combo.currentText())
        
        # Save prompts
        self.config.set_card_prompt(self.card_prompt_edit.toPlainText())
        self.config.set_hint_prompt(self.hint_prompt_edit.toPlainText())
        
        self.config.save()
        self.accept()
