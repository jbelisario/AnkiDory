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
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Model Selection Section
        model_section = QWidget()
        model_layout = QHBoxLayout()
        model_section.setLayout(model_layout)

        model_label = QLabel("LLM Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ])
        current_model = self.config.get("llm", "model", fallback="llama-3.1-8b-instant")
        self.model_combo.setCurrentText(current_model)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        layout.addWidget(model_section)

        # Hint Generation Section
        hint_label = QLabel("Hint Generation Prompt:")
        layout.addWidget(hint_label)

        self.prompt_edit = QTextEdit()
        current_prompt = self.config.get_prompt()
        self.prompt_edit.setText(current_prompt)
        layout.addWidget(self.prompt_edit)

        # Character Counter
        counter_layout = QHBoxLayout()
        self.char_counter = QLabel("0/2000 characters")
        counter_layout.addStretch()
        counter_layout.addWidget(self.char_counter)
        layout.addLayout(counter_layout)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Default")
        self.reset_button.clicked.connect(self.reset_prompt)
        
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
        self.prompt_edit.textChanged.connect(self.update_char_counter)
        self.update_char_counter()

    def update_char_counter(self):
        """Update the character counter label"""
        count = len(self.prompt_edit.toPlainText())
        self.char_counter.setText(f"{count}/2000 characters")
        if count > 2000:
            self.char_counter.setStyleSheet("color: red")
        else:
            self.char_counter.setStyleSheet("")

    def reset_prompt(self):
        """Reset the prompt to default"""
        default_prompt = self.config.get_default_prompt()
        self.prompt_edit.setText(default_prompt)

    def save_settings(self):
        """Save the settings and close the dialog"""
        # Validate prompt length
        if len(self.prompt_edit.toPlainText()) > 2000:
            from aqt.utils import showWarning
            showWarning("Prompt is too long (max 2000 characters)")
            return

        # Save settings
        self.config.set("llm", "model", self.model_combo.currentText())
        self.config.set_prompt(self.prompt_edit.toPlainText())
        self.config.save()
        
        self.accept()
