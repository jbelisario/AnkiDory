"""Data models for AnkiDory."""

from dataclasses import dataclass
from typing import Optional
from anki.decks import DeckId

@dataclass
class Card:
    """Represents a flashcard."""
    question: str
    answer: str
    hint: Optional[str] = None

@dataclass
class DeckGenerationRequest:
    """Parameters for deck generation."""
    deck_id: DeckId
    deck_name: str
    topic: str
    difficulty: str
    num_cards: int
    model: str
