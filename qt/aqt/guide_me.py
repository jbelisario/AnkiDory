from __future__ import annotations

from typing import Optional, List
from aqt import mw
from aqt.qt import *
from PyQt6.QtCore import Qt
from aqt.utils import showInfo, tooltip
from anki.cards import Card
from anki.utils import int_time
from anki.llm import llm_manager
from .db import save_hint, get_hints
from .ai_hint import AIHintGenerator

class GuideMe:
    """Manages the Guide Me feature for providing hints during card review."""
    
    def __init__(self, main_window):
        self.mw = main_window
        self.hint_generator = AIHintGenerator()
        
    def _get_card_content(self, card):
        """Get the content of the card for hint generation."""
        if not card:
            return ""
        
        # Get question content
        question = card.question() if hasattr(card, 'question') else card.q()
        # Strip HTML tags for better processing
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(question, 'html.parser')
        return soup.get_text()

    def _generate_hint(self, card):
        """Generate a hint for the given card."""
        try:
            print(f"Generating hint for card ID: {card.id}")
            
            # Get existing hints
            existing_hints = get_hints(card.id)
            if existing_hints:
                print(f"Found existing hint: {existing_hints[0]}")
                return existing_hints[0]  # Return most recent hint
            
            print("No existing hint found, generating new hint...")
            
            # Get card content for debugging
            question = card.question()
            answer = card.answer()
            print(f"Card Question: {question}")
            print(f"Card Answer: {answer}")
            
            # Generate new hint using AI
            hint = self.hint_generator.generate_hint(card)
            print(f"Generated hint: {hint}")
            
            if not hint:
                print("Error: Generated hint is empty")
                return "Error: Unable to generate hint. Please try again."
                
            if hint.startswith("Error"):
                print(f"Error in hint generation: {hint}")
                return hint
            
            # Save the hint
            print("Saving hint to database...")
            save_hint(card.id, hint)
            print("Hint saved successfully")
            
            return hint
            
        except Exception as e:
            import traceback
            error_msg = f"Error generating hint: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return f"Error generating hint: {str(e)}"

    def show_hint(self, card):
        """Show a hint for the current card."""
        if not card:
            tooltip("No card selected")
            return

        try:
            print("\n=== Starting hint generation process ===")
            
            # Create and show a loading dialog
            loading_dialog = QDialog(self.mw)
            loading_dialog.setWindowTitle("Guide Me")
            loading_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            
            # Create layout
            layout = QVBoxLayout()
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Add loading message
            loading_label = QLabel("Generating your hint...\nThis may take a few seconds.")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loading_label.setStyleSheet("""
                QLabel {
                    color: #2196F3;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                }
            """)
            layout.addWidget(loading_label)
            
            # Set dialog properties
            loading_dialog.setLayout(layout)
            loading_dialog.setFixedSize(300, 100)
            loading_dialog.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    border-radius: 5px;
                }
            """)
            
            # Show loading dialog
            loading_dialog.show()
            QApplication.processEvents()
            
            # Generate hint
            hint = self._generate_hint(card)
            
            # Close loading dialog
            loading_dialog.close()
            
            if not hint:
                print("Error: No hint was generated")
                hint = "Error: No hint could be generated. Please try again."
            
            print(f"Showing hint dialog with hint: {hint}")
            self._show_hint_dialog(hint, 1)
            
        except Exception as e:
            import traceback
            error_msg = f"Error showing hint: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            showInfo(error_msg, title="Error")
        
    def _show_hint_dialog(self, hint: str, hint_number: int) -> None:
        """Display the hint in a dialog box."""
        dialog = QDialog(self.mw)
        dialog.setWindowTitle("Guide Me - Hint")
        dialog.setMinimumWidth(500)  # Made wider
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Hint number label
        hint_label = QLabel(f"Hint #{hint_number}")
        hint_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
        
        # Hint text (using QTextEdit for copyable text)
        hint_text = QTextEdit()
        hint_text.setPlainText(hint)
        hint_text.setReadOnly(True)
        hint_text.setStyleSheet("""
            QTextEdit {
                color: #333333;
                margin: 10px;
                padding: 15px;
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        
        # Set minimum height and make it expand with content
        hint_text.setMinimumHeight(100)
        hint_text.document().setDocumentMargin(10)
        hint_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(hint_text)
        
        # Buttons container
        button_container = QHBoxLayout()
        
        # Close button
        close_btn = QPushButton("Got it!")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 13px;
                min-width: 100px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        button_container.addStretch()
        button_container.addWidget(close_btn)
        layout.addLayout(button_container)
        
        # Set dialog layout
        dialog.setLayout(layout)
        
        # Print debug info
        print(f"Dialog size: {dialog.size()}")
        print(f"Hint text widget size: {hint_text.size()}")
        print(f"Hint content length: {len(hint)}")
        print(f"Hint content: [{hint}]")
        
        # Show dialog
        dialog.exec()
