"""AI-powered deck generation module."""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from anki.collection import Collection
from anki.decks import DeckId
from ..llm.llm_client import LLMClient
from ..models import Card, DeckGenerationRequest

logger = logging.getLogger(__name__)

class DeckGenerator:
    """Handles AI-powered deck generation."""
    
    def __init__(self, collection: Collection) -> None:
        """Initialize the generator.
        
        Args:
            collection: Anki collection to add cards to
        """
        self.col = collection
        self.llm_client = LLMClient()
        
    def generate_deck(self, request: DeckGenerationRequest) -> bool:
        """Generate a new deck using AI.
        
        Args:
            request: Parameters for deck generation
            
        Returns:
            bool: True if generation was successful
        """
        try:
            logger.debug(f"Generating deck: {request}")
            
            # Generate cards using LLM
            cards = self.llm_client.generate_cards(
                topic=request.topic,
                difficulty=request.difficulty,
                num_cards=request.num_cards,
                model=request.model
            )
            
            # Add cards to the deck
            self._add_cards_to_deck(request.deck_id, cards)
            
            logger.debug(f"Successfully generated deck with {len(cards)} cards")
            return True
            
        except Exception as e:
            logger.error(f"Error generating deck: {e}")
            return False
            
    def _add_cards_to_deck(self, deck_id: DeckId, cards: List[Card]) -> None:
        """Add cards to the specified deck.
        
        Args:
            deck_id: ID of the deck to add cards to
            cards: List of cards to add
        """
        # Get the Basic note type
        basic_model = self.col.models.by_name("Basic")
        if not basic_model:
            raise ValueError("Basic note type not found")
            
        # Add each card
        for card in cards:
            note = self.col.new_note(basic_model)
            note.fields[0] = card.question
            note.fields[1] = card.answer
            note.deck_id = deck_id
            self.col.add_note(note, deck_id)
