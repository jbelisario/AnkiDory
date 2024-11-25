"""Deck Browser UI Integration for AnkiDory."""

import logging
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import tooltip, showInfo, getOnlyText, tr
from aqt.webview import AnkiWebView
from aqt.operations.deck import add_deck
from .ai_deck_dialog import AIDeckDialog
from ..generator.deck_generator import DeckGenerator
from ..models import DeckGenerationRequest

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_deck_browser():
    """Initialize deck browser modifications."""
    logger.debug("Initializing deck browser modifications...")
    try:
        from aqt.deckbrowser import DeckBrowser
        
        # Store original drawLinks
        original_draw_links = DeckBrowser.drawLinks
        
        @property
        def new_draw_links(self):
            """Add our button to the list of bottom buttons."""
            # Get base links from parent class
            if isinstance(original_draw_links, property):
                links = list(original_draw_links.fget(self))
            else:
                links = list(original_draw_links)
            # Add our button - no shortcut, command name, button text
            links.append(["", "ankidory_generate", "Generate Deck with AI"])
            return links
            
        # Replace the drawLinks property
        DeckBrowser.drawLinks = new_draw_links
        
        # Store original link handler
        original_link_handler = DeckBrowser._linkHandler
        
        def patched_link_handler(self, url):
            """Handle our custom button click."""
            if url == "ankidory_generate":
                logger.debug("AI Generate button clicked!")
                try:
                    # First, get the deck name like Anki's create deck
                    deck_name = getOnlyText(tr.decks_new_deck_name()).strip()
                    if not deck_name:
                        return
                        
                    # Show the AI deck dialog
                    def on_confirm(settings):
                        try:
                            # Create the deck
                            did = mw.col.decks.id(deck_name)
                            deck = mw.col.decks.get(did)
                            mw.col.decks.select(did)
                            
                            # Generate cards
                            request = DeckGenerationRequest(
                                deck_id=did,
                                deck_name=deck_name,
                                topic=settings["topic"],
                                num_cards=settings["num_cards"],
                                difficulty=settings["difficulty"].lower(),
                                model=settings["model"]
                            )
                            generator = DeckGenerator(collection=mw.col)
                            generator.generate_deck(request)
                            
                            # Refresh the deck browser
                            self.show()
                        except Exception as e:
                            logger.error(f"Error in deck generation: {e}")
                            tooltip(f"Error generating deck: {str(e)}")
                    
                    dialog = AIDeckDialog(mw, deck_name, on_confirm)
                    dialog.exec()
                except Exception as e:
                    logger.error(f"Error generating deck: {e}")
                    tooltip(f"Error generating deck: {str(e)}")
                return
            
            # Call original handler for other URLs
            return original_link_handler(self, url)
            
        # Replace the link handler
        DeckBrowser._linkHandler = patched_link_handler
        
        logger.debug("Deck browser modifications completed successfully")
        
        # Force refresh if browser exists
        if mw and mw.deckBrowser:
            mw.deckBrowser.show()
            
    except Exception as e:
        logger.error(f"Failed to initialize deck browser: {e}")
