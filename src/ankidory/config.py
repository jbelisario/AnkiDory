import os
import configparser
from typing import Optional

class Config:
    DEFAULT_PROMPT = """As a world-class instructor, create a helpful hint for a student studying with flashcards.
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
            "provider": "groq",
            "model": "llama-3.1-8b-instant"
        }
        self.config["prompt"] = {
            "current": self.DEFAULT_PROMPT
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

    def get_prompt(self) -> str:
        """Get the current prompt"""
        return self.config.get("prompt", "current", fallback=self.DEFAULT_PROMPT)

    def set_prompt(self, prompt: str):
        """Set the current prompt"""
        if not self.config.has_section("prompt"):
            self.config.add_section("prompt")
        self.config["prompt"]["current"] = prompt

    def get_default_prompt(self) -> str:
        """Get the default prompt"""
        return self.DEFAULT_PROMPT

    def save(self):
        """Save configuration to file"""
        with open(self.config_path, "w") as f:
            self.config.write(f)
