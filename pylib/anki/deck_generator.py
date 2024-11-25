from typing import List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import json
import fitz  # PyMuPDF
from aqt import mw
from .utils import logger
from .llm import llm_manager
from anki.decks import DeckId
from anki.notes import Note

logger = logging.getLogger(__name__)

@dataclass
class GenerationProgress:
    """Progress information for deck generation."""
    stage: str
    progress: int
    message: str

class DeckGenerationError(Exception):
    """Custom exception for deck generation errors."""
    pass

class Card:
    def __init__(self, front: str, back: str, tags: List[str] = None):
        self.front = front
        self.back = back
        self.tags = tags or []

class DeckGenerator:
    def __init__(self):
        """Initialize the deck generator with configuration."""
        self.config = {
            'max_text_length': 5000,
            'default_tags': ['AnkiDory', 'AI-Generated'],
            'llm_settings': {
                'temperature': 0.7,
                'max_tokens': 2000,
                'model': 'mixtral-8x7b-32768'
            },
            'card_settings': {
                'min_length': 10,
                'max_length': 200,
                'quality_guidelines': [
                    "Clear and concise",
                    "One main concept per card",
                    "Avoid ambiguity",
                    "Include context when needed"
                ]
            }
        }
        self.llm = llm_manager
        self._cancel_event = threading.Event()
        self._progress_callback = None
        
    def set_progress_callback(self, callback: Callable[[GenerationProgress], None]):
        """Set callback for progress updates."""
        self._progress_callback = callback
        
    def cancel_generation(self):
        """Cancel ongoing generation."""
        self._cancel_event.set()
        
    def _update_progress(self, stage: str, progress: int, message: str):
        """Update generation progress."""
        if self._progress_callback:
            self._progress_callback(GenerationProgress(stage, progress, message))
            
    def _check_cancelled(self):
        """Check if generation was cancelled."""
        if self._cancel_event.is_set():
            raise DeckGenerationError("Generation cancelled by user")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        try:
            self._update_progress("pdf_extraction", 0, "Opening PDF file...")
            doc = fitz.open(pdf_path)
            
            text_parts = []
            total_pages = len(doc)
            
            for i, page in enumerate(doc):
                self._check_cancelled()
                self._update_progress(
                    "pdf_extraction",
                    int((i + 1) / total_pages * 100),
                    f"Extracting text from page {i + 1}/{total_pages}..."
                )
                text_parts.append(page.get_text())
                
            doc.close()
            return "\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise DeckGenerationError(f"Failed to extract text from PDF: {str(e)}")

    def generate_cards_from_text(self, text: str, num_cards: int = 10) -> List[Card]:
        """Generate Anki cards from text content using LLM."""
        try:
            # Prepare text chunk
            self._update_progress("text_processing", 0, "Processing text...")
            text_chunk = text[:self.config['max_text_length']]
            
            # Create enhanced prompt
            prompt = f"""You are an expert educator creating Anki flashcards. Your task is to create {num_cards} high-quality flashcards from the provided text.

Guidelines for card creation:
1. Each card should focus on one clear concept
2. Front should be a clear question or prompt
3. Back should provide a complete, concise answer
4. Include relevant context when needed
5. Avoid cards that are too obvious or too complex

Example card format:
{{
    "front": "What is the key principle of [concept]?",
    "back": "The key principle is [clear explanation]. This is important because [brief context]."
}}

Create {num_cards} cards from this text:
{text_chunk}

Format your response as a JSON array of objects with 'front' and 'back' fields. Ensure each card follows the quality guidelines."""

            self._update_progress("card_generation", 20, "Generating cards with AI...")
            self._check_cancelled()
            
            # Generate cards with configured settings
            try:
                response = self.llm.generate_completion(
                    prompt,
                    max_tokens=self.config['llm_settings']['max_tokens'],
                    temperature=self.config['llm_settings']['temperature']
                )
            except Exception as e:
                raise DeckGenerationError(f"AI card generation failed: {str(e)}")
            
            self._update_progress("card_processing", 60, "Processing generated cards...")
            self._check_cancelled()
            
            # Parse and validate cards
            try:
                cards_data = json.loads(response)
            except json.JSONDecodeError:
                raise DeckGenerationError("Failed to parse AI response")
                
            validated_cards = []
            
            for card in cards_data:
                self._check_cancelled()
                # Basic validation
                if (len(card['front']) >= self.config['card_settings']['min_length'] and
                    len(card['front']) <= self.config['card_settings']['max_length'] and
                    len(card['back']) >= self.config['card_settings']['min_length'] and
                    len(card['back']) <= self.config['card_settings']['max_length']):
                    
                    validated_cards.append(Card(
                        front=card['front'],
                        back=card['back'],
                        tags=self.config['default_tags']
                    ))
            
            if not validated_cards:
                raise DeckGenerationError("No valid cards were generated")
                
            self._update_progress("card_processing", 80, f"Successfully generated {len(validated_cards)} cards")
            return validated_cards
            
        except DeckGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error generating cards: {str(e)}")
            raise DeckGenerationError(f"Failed to generate cards: {str(e)}")

    def create_deck(self, deck_name: str, cards: List[Card]) -> DeckId:
        """Create an Anki deck and add the generated cards to it."""
        try:
            self._update_progress("deck_creation", 85, "Creating Anki deck...")
            self._check_cancelled()
            
            # Create or get deck
            deck_id = mw.col.decks.add_normal_deck_with_name(deck_name).id
            
            # Get the Basic note type
            basic_notetype = mw.col.models.by_name("Basic")
            if not basic_notetype:
                raise DeckGenerationError("Basic note type not found")
            
            # Set the deck as current
            mw.col.decks.select(deck_id)
            
            # Add cards to deck
            total_cards = len(cards)
            for i, card in enumerate(cards):
                self._check_cancelled()
                self._update_progress(
                    "deck_creation",
                    85 + int((i + 1) / total_cards * 15),
                    f"Adding card {i + 1}/{total_cards}..."
                )
                
                note = mw.col.new_note(basic_notetype)
                note.fields[0] = card.front  # Front field
                note.fields[1] = card.back   # Back field
                
                # Add tags
                for tag in card.tags:
                    note.add_tag(tag)
                
                # Add note to deck
                mw.col.add_note(note, deck_id)
            
            # Save changes
            self._update_progress("deck_creation", 100, "Saving changes...")
            mw.col.save()
            mw.reset()
            
            return deck_id
            
        except DeckGenerationError:
            raise
        except Exception as e:
            logger.error(f"Error creating deck: {str(e)}")
            raise DeckGenerationError(f"Failed to create deck: {str(e)}")
