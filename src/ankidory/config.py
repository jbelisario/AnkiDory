"""Configuration management for AnkiDory."""

import os
import configparser
from typing import Optional

class Config:
    DEFAULT_HINT_PROMPT = """As a world-class instructor, create a helpful hint for a student studying with flashcards.
The student is looking at this question: "{question}"

Answer: "{answer}"

IMPORTANT RULES FOR HINT GENERATION:
1. NEVER use ANY words from the correct answer in your hint
2. NEVER reveal or suggest the exact terminology
3. Instead, guide the student to discover the terms by:
   - Using analogies
   - Describing the concept without using technical terms
   - Relating to everyday experiences
   - Using the Socratic method

Additional guidelines:
- Help build understanding of the underlying concepts
- Make the answer more intuitive through context
- Keep the hint concise (2-3 sentences)
- Focus on helping students discover the answer through understanding
- Do NOT include any introductory text like "Here's a hint" - just output the hint directly"""

    DEFAULT_CARD_PROMPT = """You are an expert educator and flashcard creator. Your task is to create high-quality Anki flashcards for the given topic.

Create {num_cards} Anki flashcards about {topic}.
Difficulty level: {difficulty}

Guidelines:
1. Each card should focus on a single, clear concept
2. Questions should be specific and unambiguous
3. Answers should be concise but complete
4. Include helpful hints that guide thinking without giving away the answer
5. Adjust complexity based on the specified difficulty level
6. Use examples and analogies where appropriate
7. For technical topics, include practical applications
8. Ensure factual accuracy and current information

IMPORTANT: You must respond with a valid JSON array containing card objects. Each card object must have "question", "answer", and "hint" fields.
Do not include any other text or formatting in your response.
Ensure the response is a complete and valid JSON array.

Example response format:
[
  {
    "question": "What is X?",
    "answer": "X is Y",
    "hint": "Think about Z"
  }
]"""

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        self.load()

    def load(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        else:
            self._create_default_config()

    def _create_default_config(self):
        """Create default configuration"""
        self.config["llm"] = {
            "provider": "groq"
        }
        
        self.config["groq"] = {
            "api_key": "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",
            "model": "mixtral-8x7b"
        }
        
        self.config["openai"] = {
            "api_key": "",  # Add your OpenAI API key here
            "model": "gpt-3.5-turbo"
        }
        
        self.config["common"] = {
            "max_tokens": "4000",
            "temperature": "0.7"
        }
        
        self.config["prompt"] = {
            "hint": self.DEFAULT_HINT_PROMPT,
            "card": self.DEFAULT_CARD_PROMPT
        }
        self.save()

    def get(self, section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
        """Get a configuration value"""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str):
        """Set a configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config[section][key] = value

    def get_hint_prompt(self) -> str:
        """Get the current hint generation prompt"""
        return self.config.get("prompt", "hint", fallback=self.DEFAULT_HINT_PROMPT)

    def set_hint_prompt(self, prompt: str):
        """Set the hint generation prompt"""
        if not self.config.has_section("prompt"):
            self.config.add_section("prompt")
        self.config["prompt"]["hint"] = prompt

    def get_card_prompt(self) -> str:
        """Get the current card generation prompt"""
        return self.config.get("prompt", "card", fallback=self.DEFAULT_CARD_PROMPT)

    def set_card_prompt(self, prompt: str):
        """Set the card generation prompt"""
        if not self.config.has_section("prompt"):
            self.config.add_section("prompt")
        self.config["prompt"]["card"] = prompt

    def get_default_hint_prompt(self) -> str:
        """Get the default hint generation prompt"""
        return self.DEFAULT_HINT_PROMPT

    def get_default_card_prompt(self) -> str:
        """Get the default card generation prompt"""
        return self.DEFAULT_CARD_PROMPT

    def get_prompt(self) -> str:
        """Get the current prompt (alias for get_hint_prompt for compatibility)"""
        return self.get_hint_prompt()

    def save(self):
        """Save configuration to file"""
        with open(self.config_path, "w") as f:
            self.config.write(f)
