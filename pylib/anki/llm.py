import os
import configparser
from pathlib import Path
from typing import Optional, List, Dict
import openai
from openai import OpenAI
from .utils import is_win, is_mac

class LLMManager:
    """Manages LLM interactions for the Guide Me feature."""
    
    def __init__(self):
        self._client = None
        self._config = self._load_config()
        self._setup_client()
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from config.ini file."""
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent / "config.ini"
        if not config_path.exists():
            raise FileNotFoundError(
                "config.ini not found. Please copy config_example.ini to config.ini "
                "and fill in your API key."
            )
        config.read(config_path)
        return config
        
    def _setup_client(self):
        """Initialize the OpenAI client with API key from config."""
        api_key = self._config.get("llm", "openai_api_key")
        self._client = OpenAI(api_key=api_key)
        
    def generate_hint(self, card_content: str, previous_hints: List[str] = None) -> str:
        """Generate a contextual hint for the given card content."""
        if not previous_hints:
            previous_hints = []
            
        prompt = self._create_hint_prompt(card_content, previous_hints)
        
        try:
            response = self._client.chat.completions.create(
                model=self._config.get("llm", "model"),
                messages=[
                    {"role": "system", "content": "You are a helpful tutor providing hints for flashcard review. "
                     "Your hints should guide the student towards the answer without revealing it directly. "
                     "Focus on connecting concepts and triggering recall through associated ideas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=int(self._config.get("llm", "max_tokens")),
                temperature=float(self._config.get("llm", "temperature"))
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating hint: {str(e)}"
            
    def _create_hint_prompt(self, card_content: str, previous_hints: List[str]) -> str:
        """Create a prompt for hint generation based on card content and previous hints."""
        prompt = f"Generate a helpful hint for this flashcard content:\n{card_content}\n\n"
        
        if previous_hints:
            prompt += "\nPrevious hints given:\n"
            for i, hint in enumerate(previous_hints, 1):
                prompt += f"{i}. {hint}\n"
            prompt += "\nProvide a new hint that builds upon these previous hints "
            prompt += "while giving additional context or connections."
        else:
            prompt += "\nProvide a subtle hint that helps connect related concepts "
            prompt += "without directly revealing the answer."
            
        return prompt

# Global instance
llm_manager = LLMManager()
