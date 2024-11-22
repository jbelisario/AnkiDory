import os
import configparser
from pathlib import Path
from typing import Optional, List, Dict
import openai
from openai import OpenAI
import httpx
import groq
import time
from .utils import is_win, is_mac
import logging
import sys

# Configure logging to output to stdout
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

class LLMProvider:
    """Base class for LLM providers."""
    def __init__(self, config: configparser.ConfigParser):
        self._config = config
        
    def generate_completion(self, messages: List[Dict], max_tokens: int, temperature: float) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, config: configparser.ConfigParser):
        """Initialize OpenAI provider with API key from config."""
        logger.debug("Initializing OpenAI provider")
        if 'openai' not in config:
            raise ValueError("Config missing required 'openai' section")
            
        api_key = config.get('openai', 'api_key', fallback=None)
        if not api_key:
            raise ValueError("OpenAI API key not found in config")
            
        logger.debug("Setting up OpenAI client")
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('openai', 'model', fallback='gpt-3.5-turbo')
        logger.debug("OpenAI client initialized successfully")
        
    def generate_completion(self, prompt: str, max_tokens: int = 150) -> str:
        """Generate completion using OpenAI API."""
        try:
            logger.debug("Calling OpenAI API...")
            start_time = time.time()
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful AI tutor."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"OpenAI API call completed in {elapsed:.2f} seconds")
            logger.debug(f"OpenAI Response type: {type(chat_completion)}")
            
            completion_text = chat_completion.choices[0].message.content
            logger.debug(f"Received completion from OpenAI: {completion_text[:100]}...")
            return completion_text.strip()
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise

class GroqProvider(LLMProvider):
    """Groq LLM provider."""
    
    def __init__(self, config: configparser.ConfigParser):
        """Initialize Groq provider with API key from config."""
        logger.debug("Initializing Groq provider")
        if 'groq' not in config:
            raise ValueError("Config missing required 'groq' section")
        
        api_key = config.get('groq', 'api_key', fallback=None)
        if not api_key:
            raise ValueError("Groq API key not found in config")
            
        logger.debug("Setting up Groq client")
        self.client = groq.Client(api_key=api_key)
        self.model = config.get('groq', 'model', fallback='mixtral-8x7b-32768')
        logger.debug("Groq client initialized successfully")
        
    def generate_completion(self, prompt: str, max_tokens: int = 150) -> str:
        """Generate completion using Groq API."""
        try:
            logger.debug("Calling Groq API...")
            start_time = time.time()
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful AI tutor."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"Groq API call completed in {elapsed:.2f} seconds")
            logger.debug(f"Groq Response type: {type(chat_completion)}")
            
            if not chat_completion.choices:
                raise ValueError("No completion choices returned from Groq")
                
            completion_text = chat_completion.choices[0].message.content
            logger.debug(f"Received completion from Groq: {completion_text[:100]}...")
            return completion_text.strip()
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise

class LLMManager:
    """Manages LLM interactions for the Guide Me feature."""
    
    def __init__(self):
        logger.debug("Initializing LLM Manager")
        self._config = self._load_config()
        self._provider = None
        try:
            self._provider = self._setup_provider()
            logger.debug(f"Successfully initialized provider: {type(self._provider).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize provider: {str(e)}")
            raise
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from config.ini file."""
        config = configparser.ConfigParser()
        config_path = Path("/Users/cornucopian/CascadeProjects/AnkiDory/pylib/anki/config.ini")
        logger.debug(f"Loading config from: {config_path}")
        if not config_path.exists():
            raise FileNotFoundError(
                f"config.ini not found at {config_path}. Please copy config_example.ini to config.ini "
                "and fill in your API keys."
            )
        logger.debug(f"Config file exists at {config_path}")
        
        # Read the raw file contents for debugging
        with open(config_path, 'r') as f:
            raw_config = f.read()
        logger.debug(f"Raw config file contents:\n{raw_config}")
        
        config.read(config_path)
        logger.debug(f"Config sections after read: {config.sections()}")
        
        if 'llm' not in config.sections():
            raise ValueError("Config file missing required 'llm' section")
            
        logger.debug(f"Config llm section contents: {dict(config['llm'])}")
        
        # Log the provider setting
        provider = config.get('llm', 'provider', fallback='openai')
        logger.debug(f"Selected provider from config: {provider}")
        
        return config
        
    def _setup_provider(self) -> LLMProvider:
        """Initialize the selected LLM provider."""
        if 'llm' not in self._config:
            raise ValueError("Config missing required 'llm' section")
            
        provider_name = self._config.get("llm", "provider", fallback="openai").lower()
        logger.debug(f"Setting up provider from config: {provider_name}")
        logger.debug(f"Available sections in config: {self._config.sections()}")
        
        # Load common settings
        if 'common' in self._config:
            self.max_tokens = self._config.getint('common', 'max_tokens', fallback=150)
            self.temperature = self._config.getfloat('common', 'temperature', fallback=0.7)
            logger.debug(f"Loaded common settings - max_tokens: {self.max_tokens}, temperature: {self.temperature}")
        else:
            logger.warning("No common section found in config, using defaults")
            self.max_tokens = 150
            self.temperature = 0.7
        
        if provider_name == "openai":
            logger.debug("Using OpenAI provider")
            return OpenAIProvider(self._config)
        elif provider_name == "groq":
            logger.debug("Using Groq provider")
            return GroqProvider(self._config)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")
            
    def generate_hint(self, prompt: str) -> str:
        """Generate a hint using the configured LLM provider."""
        try:
            logger.debug(f"Generating hint using provider: {type(self._provider).__name__}")
            return self._provider.generate_completion(
                prompt=prompt,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            logger.error(f"Error generating hint: {str(e)}")
            raise

# Global instance
llm_manager = LLMManager()
