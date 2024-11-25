import unittest
from unittest.mock import Mock, patch
import json
from pathlib import Path
from anki.deck_generator import DeckGenerator, Card, DeckGenerationError, GenerationProgress

class TestDeckGenerator(unittest.TestCase):
    def setUp(self):
        self.deck_generator = DeckGenerator()
        self.progress_updates = []
        
        def progress_callback(progress: GenerationProgress):
            self.progress_updates.append(progress)
            
        self.deck_generator.set_progress_callback(progress_callback)
        
    def test_card_validation(self):
        """Test card validation logic"""
        # Valid card
        card = Card(
            front="What is Python?",
            back="Python is a high-level programming language.",
            tags=["test"]
        )
        self.assertEqual(card.front, "What is Python?")
        self.assertEqual(card.back, "Python is a high-level programming language.")
        self.assertEqual(card.tags, ["test"])
        
    @patch('anki.deck_generator.llm_manager')
    def test_generate_cards_from_text(self, mock_llm):
        """Test card generation from text"""
        # Mock LLM response
        mock_cards = [
            {
                "front": "What is Python?",
                "back": "Python is a programming language."
            },
            {
                "front": "Who created Python?",
                "back": "Guido van Rossum created Python."
            }
        ]
        mock_llm.generate_completion.return_value = json.dumps(mock_cards)
        
        # Test generation
        cards = self.deck_generator.generate_cards_from_text(
            "Python is a programming language created by Guido van Rossum.",
            num_cards=2
        )
        
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].front, "What is Python?")
        self.assertEqual(cards[1].back, "Guido van Rossum created Python.")
        
    def test_pdf_extraction(self):
        """Test PDF text extraction"""
        # Create test PDF path
        test_pdf = Path(__file__).parent / "test_files" / "test.pdf"
        
        # Test non-existent file
        with self.assertRaises(DeckGenerationError):
            self.deck_generator.extract_text_from_pdf(str(test_pdf))
            
    def test_progress_tracking(self):
        """Test progress updates"""
        with patch('anki.deck_generator.llm_manager') as mock_llm:
            mock_llm.generate_completion.return_value = json.dumps([
                {"front": "Test?", "back": "Answer"}
            ])
            
            self.deck_generator.generate_cards_from_text("Test text")
            
            # Verify progress updates
            stages = [p.stage for p in self.progress_updates]
            self.assertIn("text_processing", stages)
            self.assertIn("card_generation", stages)
            self.assertIn("card_processing", stages)
            
    def test_cancellation(self):
        """Test generation cancellation"""
        # Simulate cancellation during generation
        def mock_completion(*args, **kwargs):
            self.deck_generator.cancel_generation()
            return json.dumps([])
            
        with patch('anki.deck_generator.llm_manager') as mock_llm:
            mock_llm.generate_completion.side_effect = mock_completion
            
            with self.assertRaises(DeckGenerationError) as context:
                self.deck_generator.generate_cards_from_text("Test text")
                
            self.assertIn("cancelled", str(context.exception).lower())
            
if __name__ == '__main__':
    unittest.main()
