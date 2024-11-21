# Dory - AI-Enhanced Anki

Dory is an extension of Anki that adds AI-powered features to enhance your learning experience. The main feature is "Guide Me," which provides contextual hints and guidance while reviewing cards.

## Features

### Guide Me 💡
- Get contextual hints for challenging cards
- Progressive hint system that builds understanding
- AI-powered assistance that helps form connections
- Tracks hint usage to help optimize your learning

## Installation

1. Clone this repository:
```bash
git clone https://github.com/jbelisario/AnkiDory.git
cd AnkiDory
```

2. Install additional dependencies:
```bash
pip install -r requirements-dory.txt
```

3. Copy the configuration file and add your OpenAI API key:
```bash
cp pylib/anki/config_example.ini pylib/anki/config.ini
# Edit config.ini and add your OpenAI API key
```

## Usage

1. During card review, you'll see a new "Guide Me 💡" button alongside the answer buttons
2. Click it to get a contextual hint about the current card
3. Multiple hints are available per card, each building upon previous hints
4. Hints are stored with the card for future reference

## Configuration

You can customize the Guide Me feature in `config.ini`:
- `model`: Choose between GPT-3.5-turbo or GPT-4
- `max_tokens`: Adjust the length of generated hints
- `temperature`: Control the creativity of the hints

## Development

The Guide Me feature is implemented across several components:
- `qt/aqt/guide_me.py`: Main feature implementation
- `pylib/anki/llm.py`: LLM integration
- `pylib/anki/cards.py`: Card model extensions
- Database tables: `dory_hints` and `dory_hint_stats`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the same terms as Anki - GNU AGPL v3 or later.
