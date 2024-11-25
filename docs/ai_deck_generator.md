# AI Deck Generator for Anki

The AI Deck Generator is a powerful feature that automatically creates high-quality Anki flashcards from your text or PDF documents using advanced AI technology.

## Setup

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure API Keys:
   - Copy `config.ini` to your Anki addon directory
   - Edit `config.ini` and add your API keys:
     - For Groq (recommended): Add your Groq API key
     - For OpenAI: Add your OpenAI API key

## Usage

1. Open Anki and click the "Generate Deck with AI" button in the toolbar (or press Alt+G)
2. In the dialog:
   - Enter a name for your new deck
   - Choose your input method:
     - **Text**: Paste text directly
     - **PDF**: Upload a PDF file (max 10MB)
   - Select number of cards to generate (5-20)
   - Click "Generate"

3. The generator will:
   - Process your input
   - Generate high-quality flashcards using AI
   - Create a new Anki deck
   - Add the generated cards to your collection

## Features

- **Smart Card Generation**: AI creates clear, concise, and effective flashcards
- **PDF Support**: Extract text from PDF documents
- **Progress Tracking**: See real-time progress of card generation
- **Cancellation**: Cancel generation at any time
- **Error Recovery**: Graceful handling of errors
- **Quality Control**: Validates generated cards for quality

## Configuration

Edit `config.ini` to customize:
- LLM provider (Groq or OpenAI)
- Model settings
- Card generation parameters
- PDF processing options

## Troubleshooting

1. **Missing API Key**:
   - Ensure you've added your API key to `config.ini`
   - Check the provider setting matches your API key

2. **PDF Issues**:
   - Ensure PDF is under 10MB
   - Check PDF is text-based (not scanned)
   - Try copying text manually if extraction fails

3. **Generation Errors**:
   - Check internet connection
   - Verify API key is valid
   - Try with smaller text input
   - Check error message for specific issues

## Support

For issues or questions:
1. Check the error message
2. Review troubleshooting steps
3. Check Anki logs for details
4. Report issues with:
   - Error message
   - Steps to reproduce
   - Log output
