"""AnkiDory addon initialization."""

import logging
import os
import sqlite3
from aqt import mw, gui_hooks
from .gui import deck_browser

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the addon database."""
    logger.debug("Initializing database...")
    try:
        db_path = os.path.join(os.path.dirname(__file__), "ankidory.db")
        
        # Create database connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create necessary tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY,
                deck_id INTEGER,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deck_id) REFERENCES decks(id)
            );
        """)
        
        conn.commit()
        conn.close()
        logger.debug("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def delayed_init():
    """Initialize the addon after profile loads."""
    logger.debug("Running delayed initialization...")
    try:
        # Initialize database
        if not init_db():
            logger.error("Failed to initialize database")
            return

        # Initialize deck browser modifications
        deck_browser.init_deck_browser()
        
        # Force refresh the deck browser to show our modifications
        if mw and mw.deckBrowser:
            mw.deckBrowser.show()
            
        logger.debug("Delayed initialization completed successfully")
    except Exception as e:
        logger.error(f"Delayed initialization failed: {e}")

# Register initialization hook
gui_hooks.profile_did_open.append(delayed_init)

# Force initialization on reload
if mw and mw.col:
    delayed_init()
