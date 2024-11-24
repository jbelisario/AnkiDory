from aqt.qt import *
from aqt.utils import tr
from aqt import mw

class AISettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setup_ui()
        self.load_settings()
        self.silentlyClose = True

    def setup_ui(self):
        self.setWindowTitle("AI Settings")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Model selection
        model_group = QGroupBox("LLM Model")
        model_layout = QVBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ])
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Hint generation prompt
        prompt_group = QGroupBox("Hint Generation Prompt")
        prompt_layout = QVBoxLayout()
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Enter hint generation prompt...")
        self.prompt_edit.setMaximumHeight(200)
        prompt_layout.addWidget(self.prompt_edit)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)

        # Character count
        self.char_count = QLabel("0/2000 characters")
        self.prompt_edit.textChanged.connect(self.update_char_count)
        layout.addWidget(self.char_count)

        # Buttons
        button_box = QDialogButtonBox()
        self.reset_button = button_box.addButton("Reset to Default", 
                                               QDialogButtonBox.ButtonRole.ResetRole)
        button_box.addButton(QDialogButtonBox.StandardButton.Save)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)

        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        self.reset_button.clicked.connect(self.reset_to_default)
        
        layout.addWidget(button_box)

    def update_char_count(self):
        count = len(self.prompt_edit.toPlainText())
        self.char_count.setText(f"{count}/2000 characters")
        if count > 2000:
            self.char_count.setStyleSheet("color: red")
        else:
            self.char_count.setStyleSheet("")

    def load_settings(self):
        config = mw.addonManager.getConfig(__name__)
        if not config:
            config = {
                "current_model": "llama-3.1-8b-instant",
                "current_prompt": "Generate a helpful hint for this flashcard that guides the student towards the answer without directly giving it away."
            }
            mw.addonManager.writeConfig(__name__, config)
        
        self.model_combo.setCurrentText(config["current_model"])
        self.prompt_edit.setPlainText(config["current_prompt"])

    def save_settings(self):
        if len(self.prompt_edit.toPlainText()) > 2000:
            QMessageBox.warning(self, "Error", 
                              "Prompt exceeds 2000 character limit.")
            return

        config = {
            "current_model": self.model_combo.currentText(),
            "current_prompt": self.prompt_edit.toPlainText()
        }
        mw.addonManager.writeConfig(__name__, config)
        self.accept()

    def reset_to_default(self):
        default_config = {
            "current_model": "llama-3.1-8b-instant",
            "current_prompt": "Generate a helpful hint for this flashcard that guides the student towards the answer without directly giving it away."
        }
        self.model_combo.setCurrentText(default_config["current_model"])
        self.prompt_edit.setPlainText(default_config["current_prompt"])

class AISettings:
    def __init__(self, mw):
        self.mw = mw

    def show_settings(self):
        dialog = AISettingsDialog(self.mw)
        dialog.exec()
