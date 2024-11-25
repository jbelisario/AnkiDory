# Generate Deck with AI - Product Requirements Document

## Overview
The "Generate Deck with AI" feature enhances Anki's deck creation capabilities by leveraging AI to automatically generate flashcards from text content or PDF documents. This feature streamlines the deck creation process and helps users create high-quality study materials efficiently.

## Problem Statement
Creating Anki decks manually is time-consuming and requires significant effort to:
1. Extract key concepts from learning materials
2. Format information into effective question-answer pairs
3. Ensure consistent card quality and coverage of material

## Solution
Introduce an AI-powered deck generation feature that:
- Accepts text input directly or via PDF upload
- Processes content using LLM technology
- Automatically generates well-structured Anki cards
- Allows customization of card generation through configurable prompts

## User Experience

### Home Screen Integration
- New button "Generate Deck with AI" placed next to existing "Create Deck" button
- Button styling matches Anki's existing UI design
- Tooltip on hover explaining the feature

### Generate Deck Dialog
- Modal dialog appears when button is clicked
- Clean, modern interface with two main sections:
  1. Input Method Selection
  2. Content Input Area

#### Input Method Selection
- Toggle switch between:
  - "Paste Text" (default)
  - "Upload PDF"
- Smooth transition between input methods
- Clear visual indication of selected method

#### Content Input Area
**For "Paste Text":**
- Large text area with placeholder text
- Minimum height: 300px
- Support for copy/paste
- Character count display
- Clear button to reset input

**For "Upload PDF":**
- Drag-and-drop zone
- "Browse" button for file selection
- File size limit indicator
- Supported file format (.pdf) information
- Preview of selected file name
- Option to remove selected file

### Processing Indicators
- Progress bar during processing
- Cancelable operation
- Clear error messages if processing fails
- Success confirmation when complete

### Output Preview
- Display generated cards in a scrollable list
- Allow editing of generated cards before saving
- Options to:
  - Accept all cards
  - Edit individual cards
  - Delete unwanted cards
  - Regenerate specific cards

## AI Settings Integration

### New Settings Section
Add "Deck Generation" section to existing AI Settings dialog:

```ini
[AI Settings Dialog]
├── Hint Generation
│   └── [Existing hint settings]
└── Deck Generation
    ├── Card Generation Prompt
    │   └── [Editable text area]
    ├── Default Parameters
    │   ├── Max cards per source
    │   ├── Temperature
    │   └── Max tokens
    └── Advanced Options
        └── [Future extensibility]
```

### Prompt Configuration
- Editable text area for card generation prompt
- Default prompt provided
- Reset to default button
- Syntax highlighting for prompt variables
- Template variables:
  - {{content}} - Source text
  - {{max_cards}} - Maximum cards to generate
  - {{style}} - Card style preference

## Technical Requirements

### PDF Processing
- Integration with pdfminer.six for text extraction
- Support for:
  - Text-based PDFs
  - Scanned PDFs with OCR
  - Multiple page documents
- Error handling for:
  - Corrupted files
  - Password-protected PDFs
  - Unsupported formats

### LLM Integration
- Utilize existing LLM infrastructure
- Support for:
  - OpenAI
  - Groq
  - Future providers
- Proper error handling and retry logic
- Rate limiting compliance

### Data Flow
```mermaid
graph LR
    A[User Input] --> B[Text Extraction]
    B --> C[LLM Processing]
    C --> D[Card Generation]
    D --> E[Preview]
    E --> F[Save to Deck]
```

## Performance Requirements
- PDF processing: < 5 seconds for typical document
- LLM response: < 10 seconds for initial cards
- UI responsiveness: < 100ms for interactions
- Support files up to 50MB
- Handle documents up to 100 pages

## Error Handling
- Clear error messages for:
  - File format issues
  - Size limitations
  - Processing failures
  - Network connectivity
  - API limits
- Graceful degradation when services unavailable
- Automatic retry for transient failures

## Future Considerations
1. Support for additional file formats
   - Word documents
   - HTML
   - Markdown
2. Batch processing of multiple files
3. Templates for different subjects
4. Community-shared prompts
5. Integration with external learning resources

## Success Metrics
- User adoption rate
- Time saved vs manual creation
- Card quality ratings
- User satisfaction surveys
- Error rate monitoring
- Processing success rate

## Release Strategy
1. Alpha testing with power users
2. Beta release to limited audience
3. Gradual rollout to all users
4. Monitoring and iteration based on feedback

## Documentation Requirements
- User guide
- Technical documentation
- API documentation
- Troubleshooting guide
- Best practices guide

## Maintenance Plan
- Regular prompt optimization
- Performance monitoring
- Error rate tracking
- User feedback collection
- Quarterly feature reviews

## Dependencies
- pdfminer.six library
- LLM API access
- UI framework updates
- Storage system modifications
- Testing infrastructure
