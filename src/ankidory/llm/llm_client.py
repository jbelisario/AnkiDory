"""LLM client for generating flashcards."""

import json
import logging
import os
from typing import List, Optional
try:
    from anki.llm import LLMManager
    HAS_ANKI_LLM = True
except ImportError:
    HAS_ANKI_LLM = False
import groq
from ..models import Card
from ..config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert educator and flashcard creator. Your task is to create high-quality Anki flashcards for the given topic.
Follow these guidelines:
1. Each card should focus on a single, clear concept
2. Questions should be specific and unambiguous
3. Answers should be concise but complete
4. Include helpful hints that guide the student's thinking without giving away the answer
5. Adjust complexity based on the specified difficulty level
6. Use examples and analogies where appropriate
7. For technical topics, include practical applications
8. Ensure factual accuracy and current information"""

class LLMClient:
    """Client for interacting with LLM APIs."""
    
    def __init__(self) -> None:
        """Initialize the LLM client."""
        self.config = Config()
        self.api_key = self.config.get("groq", "api_key")
        if not self.api_key:
            # Create a new config file with default settings
            self.config._create_default_config()
            self.api_key = self.config.get("groq", "api_key")
            if not self.api_key:
                raise ValueError("Groq API key not found in configuration")
        
        # Initialize Groq client
        self.client = groq.Client(api_key=self.api_key)
        logger.info("Using Groq client")
        
    def generate_cards(
        self,
        topic: str,
        difficulty: str,
        num_cards: int,
        model: str = "mixtral-8x7b"
    ) -> List[Card]:
        """Generate flashcards using LLM."""
        try:
            # Get card generation prompt from config
            prompt = f"""Generate {num_cards} Anki flashcards about {topic}.
Difficulty level: {difficulty}

IMPORTANT: Respond with ONLY a JSON array of card objects.
Each card object must have these exact fields:
- "question": The question text
- "answer": The answer text
- "hint": A helpful hint (optional)

Example format:
[
  {{
    "question": "What is X?",
    "answer": "X is Y",
    "hint": "Think about Z"
  }}
]

Do not include any other text, explanations, or formatting in your response.
Just the raw JSON array."""
            
            # Generate cards using Groq
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                top_p=1,
                stream=False
            )
            
            # Parse response into Card objects
            response_text = completion.choices[0].message.content.strip()
            logger.debug(f"LLM response: {response_text}")
            
            try:
                # Remove any leading/trailing whitespace or non-JSON characters
                response_text = response_text.strip()
                if not response_text.startswith('['):
                    # Try to find the start of the JSON array
                    start_idx = response_text.find('[')
                    if start_idx == -1:
                        raise ValueError("No JSON array found in response")
                    response_text = response_text[start_idx:]
                
                if not response_text.endswith(']'):
                    # Try to find the end of the JSON array
                    end_idx = response_text.rfind(']')
                    if end_idx == -1:
                        raise ValueError("No complete JSON array found in response")
                    response_text = response_text[:end_idx+1]
                
                cards_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response_text}")
                raise ValueError("LLM response was not valid JSON")
            
            if not isinstance(cards_data, list):
                raise ValueError("LLM response was not a JSON array")
            
            # Convert to Card objects
            cards = []
            for card_data in cards_data:
                if not isinstance(card_data, dict):
                    logger.error(f"Invalid card data: {card_data}")
                    continue
                    
                try:
                    cards.append(Card(
                        question=card_data["question"],
                        answer=card_data["answer"],
                        hint=card_data.get("hint", "")  # hint is optional
                    ))
                except KeyError as e:
                    logger.error(f"Missing required field in card data: {e}")
                    continue
                
            if not cards:
                raise ValueError("No valid cards were generated")
                
            return cards
            
        except Exception as e:
            logger.error(f"Error generating cards: {e}")
            raise
