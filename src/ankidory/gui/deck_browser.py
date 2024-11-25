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
                        return True
                        
                    # Create the deck first
                    op = add_deck(parent=self.mw, name=deck_name)
                    
                    def on_deck_added(changes):
                        """Show AI settings dialog after deck is created."""
                        logger.debug(f"Deck created with id: {changes.id}")
                        
                        def on_settings_confirmed(settings):
                            """Handle confirmed AI settings."""
                            logger.debug(f"AI settings confirmed: {settings}")
                            
                            # Create generation request
                            request = DeckGenerationRequest(
                                deck_id=changes.id,
                                deck_name=deck_name,
                                topic=settings["topic"],
                                difficulty=settings["difficulty"],
                                num_cards=settings["num_cards"],
                                model=settings["model"]
                            )
                            
                            # Initialize generator
                            generator = DeckGenerator(self.mw.col)
                            
                            # Generate the deck
                            if generator.generate_deck(request):
                                showInfo("AI deck generation complete!")
                                self.refresh()
                            else:
                                showInfo("Failed to generate AI deck. Check the logs for details.")
                            
                        dialog = AIDeckDialog(
                            parent=self.mw,
                            deck_name=deck_name,
                            on_confirm=on_settings_confirmed
                        )
                        dialog.show()
                    
                    op.success(on_deck_added).run_in_background()
                    return True
                except Exception as e:
                    logger.error(f"Error handling button click: {e}")
                    showInfo(f"Error creating AI deck: {e}")
                    return True
            return original_link_handler(self, url)
            
        # Replace the link handler
        DeckBrowser._linkHandler = patched_link_handler
        
        logger.debug("Successfully patched deck browser")
        
        # Force a refresh of the deck browser
        if mw and mw.deckBrowser:
            mw.deckBrowser.refresh()
            logger.debug("Refreshed deck browser")
        
    except Exception as e:
        logger.error(f"Failed to patch deck browser: {e}")
        showInfo(f"Error initializing AnkiDory: {e}")
