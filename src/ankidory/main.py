"""Main entry point for AnkiDory"""

import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from .aqt import AnkiApp
from .gui.deck_browser import DeckBrowser
from anki.collection import Collection
from . import init_db
from .config import Config

def initialize_app():
    """Initialize the application and its dependencies."""
    app = QApplication(sys.argv)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    return app

def initialize_collection():
    """Initialize or load the collection."""
    base_path = os.path.join(os.path.expanduser("~"), ".ankidory")
    os.makedirs(base_path, exist_ok=True)
    
    collection_path = os.path.join(base_path, "collection.anki2")
    if not os.path.exists(collection_path):
        Collection.create(collection_path)
    
    return Collection(collection_path)

def main():
    """Start AnkiDory as a standalone application."""
    try:
        # Initialize database
        init_db()
        
        # Initialize Qt application
        app = initialize_app()
        
        # Initialize collection
        col = initialize_collection()
        
        # Create and show main window
        main_window = QMainWindow()
        deck_browser = DeckBrowser(main_window, col)
        main_window.setCentralWidget(deck_browser)
        main_window.setWindowTitle("AnkiDory")
        main_window.resize(1024, 768)  # Set a reasonable default size
        main_window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error starting AnkiDory: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
