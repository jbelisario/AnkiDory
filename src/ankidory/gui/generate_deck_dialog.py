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
    QStackedWidget,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QLineEdit,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSlot, QMimeData, QThread, pyqtSignal
from aqt import mw
from ..config import Config
from anki.deck_generator import DeckGenerator, DeckGenerationError, GenerationProgress
import os

class PDFDropZone(QFrame):
    """Custom widget for PDF drag and drop."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumHeight(100)
        
        # Setup UI
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel("Drop PDF here or click Browse")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.file_path = None
        self.setStyleSheet("""
            PDFDropZone {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 4px;
            }
            PDFDropZone:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
                self.setStyleSheet("""
                    PDFDropZone {
                        background-color: #e9ecef;
                        border: 2px dashed #0d6efd;
                        border-radius: 4px;
                    }
                """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            PDFDropZone {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 4px;
            }
            PDFDropZone:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        url = event.mimeData().urls()[0]
        self.file_path = url.toLocalFile()
        self.label.setText(os.path.basename(self.file_path))
        self.setStyleSheet("""
            PDFDropZone {
                background-color: #f8f9fa;
                border: 2px solid #0d6efd;
                border-radius: 4px;
            }
        """)

class GenerationWorker(QThread):
    """Worker thread for deck generation."""
    progress = pyqtSignal(str, int, str)  # stage, progress, message
    finished = pyqtSignal(str)  # deck name
    error = pyqtSignal(str)  # error message
    
    def __init__(self, deck_generator, deck_name: str, text: str, num_cards: int):
        super().__init__()
        self.deck_generator = deck_generator
        self.deck_name = deck_name
        self.text = text
        self.num_cards = num_cards
        
    def run(self):
        try:
            # Set up progress callback
            def progress_callback(progress: GenerationProgress):
                self.progress.emit(progress.stage, progress.progress, progress.message)
                
            self.deck_generator.set_progress_callback(progress_callback)
            
            # Generate cards
            cards = self.deck_generator.generate_cards_from_text(self.text, self.num_cards)
            
            # Create deck
            self.deck_generator.create_deck(self.deck_name, cards)
            
            self.finished.emit(self.deck_name)
            
        except DeckGenerationError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {str(e)}")

class GenerateDeckDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = Config()
        self.deck_generator = DeckGenerator(mw.col)  # Pass the Anki collection
        self.worker = None
        self.setup_ui()
        self.apply_styles()
        
    def apply_styles(self):
        """Apply consistent styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 13px;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #86b7fe;
                outline: 0;
                box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton#generate {
                background-color: #0d6efd;
                color: white;
            }
            QPushButton#generate:hover {
                background-color: #0b5ed7;
            }
            QPushButton#cancel {
                background-color: #6c757d;
                color: white;
            }
            QPushButton#cancel:hover {
                background-color: #5c636a;
            }
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0d6efd;
            }
        """)
        
    def setup_ui(self):
        """Initialize the dialog UI components"""
        self.setWindowTitle("Generate Deck with AI")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Input Method Selection
        input_section = QWidget()
        input_layout = QHBoxLayout()
        input_section.setLayout(input_layout)
        
        input_label = QLabel("Input Method:")
        self.input_combo = QComboBox()
        self.input_combo.addItems(["Paste Text", "Upload PDF"])
        self.input_combo.currentIndexChanged.connect(self.on_input_method_changed)
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_combo)
        input_layout.addStretch()
        layout.addWidget(input_section)
        
        # Deck Name Section
        deck_section = QWidget()
        deck_layout = QHBoxLayout()
        deck_section.setLayout(deck_layout)
        
        deck_label = QLabel("Deck Name:")
        self.deck_name = QLineEdit()
        self.deck_name.setPlaceholderText("Enter deck name...")
        
        deck_layout.addWidget(deck_label)
        deck_layout.addWidget(self.deck_name)
        layout.addWidget(deck_section)
        
        # Stacked Widget for Input Methods
        self.input_stack = QStackedWidget()
        
        # Text Input Widget
        text_widget = QWidget()
        text_layout = QVBoxLayout()
        text_widget.setLayout(text_layout)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste your text here...")
        text_layout.addWidget(self.text_edit)
        
        # Character Counter for Text
        text_counter_layout = QHBoxLayout()
        self.text_counter = QLabel("0 characters")
        text_counter_layout.addStretch()
        text_counter_layout.addWidget(self.text_counter)
        text_layout.addLayout(text_counter_layout)
        
        self.input_stack.addWidget(text_widget)
        
        # PDF Upload Widget
        pdf_widget = QWidget()
        pdf_layout = QVBoxLayout()
        pdf_widget.setLayout(pdf_layout)
        
        self.pdf_drop_zone = PDFDropZone()
        pdf_layout.addWidget(self.pdf_drop_zone)
        
        upload_layout = QHBoxLayout()
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_pdf)
        upload_layout.addStretch()
        upload_layout.addWidget(self.browse_button)
        pdf_layout.addLayout(upload_layout)
        
        pdf_info = QLabel("Supported format: PDF (max 10MB)")
        pdf_info.setStyleSheet("color: #6c757d;")
        pdf_layout.addWidget(pdf_info)
        
        self.input_stack.addWidget(pdf_widget)
        layout.addWidget(self.input_stack)
        
        # Number of Cards Selection
        cards_section = QWidget()
        cards_layout = QHBoxLayout()
        cards_section.setLayout(cards_layout)
        
        cards_label = QLabel("Number of Cards:")
        self.cards_combo = QComboBox()
        self.cards_combo.addItems(["5", "10", "15", "20"])
        self.cards_combo.setCurrentText("10")
        
        cards_layout.addWidget(cards_label)
        cards_layout.addWidget(self.cards_combo)
        cards_layout.addStretch()
        layout.addWidget(cards_section)
        
        # Status Label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #6c757d;")
        self.status_label.hide()
        layout.addWidget(self.status_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_button = QPushButton("Generate")
        self.generate_button.setDefault(True)
        self.generate_button.clicked.connect(self.generate_deck)
        self.generate_button.setToolTip("Generate flashcards from the input text")
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.handle_cancel)
        self.cancel_button.setToolTip("Cancel generation or close dialog")
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.generate_button)
        
        layout.addLayout(button_layout)
        
        # Style the buttons
        self.generate_button.setObjectName("generate")
        self.cancel_button.setObjectName("cancel")
        
        # Add tooltips
        self.input_combo.setToolTip("Choose between pasting text or uploading a PDF file")
        self.deck_name.setToolTip("Enter a name for your new deck")
        self.text_edit.setToolTip("Type or paste your text here")
        self.cards_combo.setToolTip("Select how many flashcards to generate")
        
        # Connect signals
        self.text_edit.textChanged.connect(self.update_text_counter)
        
    def on_input_method_changed(self, index):
        """Handle input method selection change"""
        self.input_stack.setCurrentIndex(index)
        
    def update_text_counter(self):
        """Update the text character counter"""
        count = len(self.text_edit.toPlainText())
        self.text_counter.setText(f"{count} characters")
        
    def browse_pdf(self):
        """Open file dialog for PDF selection"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        if file_name:
            self.pdf_drop_zone.file_path = file_name
            self.pdf_drop_zone.label.setText(os.path.basename(file_name))
            self.pdf_drop_zone.setStyleSheet("""
                PDFDropZone {
                    background-color: #f8f9fa;
                    border: 2px solid #0d6efd;
                    border-radius: 4px;
                }
            """)
            
    def handle_progress(self, stage: str, progress: int, message: str):
        """Handle progress updates from the worker."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        
    def handle_finished(self, deck_name: str):
        """Handle successful deck generation."""
        self.progress_bar.setValue(100)
        self.status_label.setText("Deck created successfully!")
        
        QMessageBox.information(
            self,
            "Success",
            f"Successfully created deck '{deck_name}'!"
        )
        self.cleanup_worker()
        self.accept()
        
    def handle_error(self, error_message: str):
        """Handle generation error."""
        self.cleanup_worker()
        QMessageBox.critical(
            self,
            "Error",
            f"An error occurred: {error_message}"
        )
        
    def cleanup_worker(self):
        """Clean up the worker thread."""
        if self.worker:
            if self.worker.isRunning():
                self.deck_generator.cancel_generation()
                self.worker.wait()
            self.worker = None
            
        self.progress_bar.hide()
        self.status_label.hide()
        self.generate_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        
    def handle_cancel(self):
        """Handle cancel button click."""
        if self.worker and self.worker.isRunning():
            self.deck_generator.cancel_generation()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("Cancelling...")
        else:
            self.reject()
            
    @pyqtSlot()
    def generate_deck(self):
        """Generate Anki deck from the input"""
        try:
            # Check deck name
            deck_name = self.deck_name.text().strip()
            if not deck_name:
                QMessageBox.warning(self, "Error", "Please enter a deck name.")
                return
                
            # Get number of cards
            num_cards = int(self.cards_combo.currentText())
            
            # Get input text
            if self.input_combo.currentIndex() == 0:  # Text input
                text = self.text_edit.toPlainText()
                if not text:
                    QMessageBox.warning(self, "Error", "Please enter some text.")
                    return
            else:  # PDF input
                file_path = self.pdf_drop_zone.file_path
                if file_path is None:
                    QMessageBox.warning(self, "Error", "Please select a PDF file.")
                    return
                    
                # Check file size
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10MB
                    QMessageBox.warning(self, "Error", "PDF file is too large (max 10MB).")
                    return
                    
                # Extract text
                text = self.deck_generator.extract_text_from_pdf(file_path)
            
            # Show progress UI
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.status_label.show()
            self.generate_button.setEnabled(False)
            self.cancel_button.setText("Cancel Generation")
            
            # Start worker thread
            self.worker = GenerationWorker(
                self.deck_generator,
                deck_name,
                text,
                num_cards
            )
            self.worker.progress.connect(self.handle_progress)
            self.worker.finished.connect(self.handle_finished)
            self.worker.error.connect(self.handle_error)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred: {str(e)}"
            )
            self.cleanup_worker()
