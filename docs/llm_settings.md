# AI Settings Feature

## Overview
The AI Settings feature adds a new button to Anki's main toolbar that allows users to customize their AI-powered hint generation experience. This feature provides a user-friendly interface to modify LLM model selection and hint generation prompts, with the ability to revert to default settings.

## User Story
As an Anki user studying with AI-powered hints, I want to be able to customize the AI model and hint generation prompts so that I can optimize the hints for my learning style and preferences.

## Requirements

### 1. UI Components

#### 1.1 Main Toolbar Button
- Add "AI Settings" button to the main Anki toolbar
- Position: After the existing buttons (Decks, Add, Browse, Stats, Sync)
- Icon: Use a gear/settings icon with an "AI" label
- Shortcut key: Alt+I

#### 1.2 Settings Dialog
- Modal dialog titled "AI Settings"
- Two main sections:
  1. Model Selection
  2. Hint Generation

### 2. Model Selection Section

#### 2.1 Model Dropdown
- Label: "LLM Model"
- Options: Available Groq models (e.g., llama-3.1-8b-instant, mixtral-8x7b-32768)
- Default: Current model from config.ini
- Description: Brief performance/capability description for each model

### 3. Hint Generation Section

#### 3.1 Prompt Editor
- Large text area for editing the hint generation prompt
- Default: Current "Dory Hint Preset Prompt"
- Character counter with reasonable limit
- Syntax highlighting for prompt template variables

#### 3.2 Prompt Management
- "Reset to Default" button to restore the original Dory prompt
- "Save as Preset" to save current prompt with a name
- Dropdown to load saved presets

### 4. Settings Storage

#### 4.1 Configuration File
- Store settings in the addon's config.json
- Structure:
  ```json
  {
    "llm": {
      "current_model": "llama-3.1-8b-instant",
      "current_prompt": "...",
      "saved_prompts": {
        "dory_default": "...",
        "custom_1": "..."
      }
    }
  }
  ```

#### 4.2 Persistence
- Settings persist across Anki restarts
- Settings are profile-independent
- Changes take effect immediately

### 5. Error Handling
- Validate prompt length and content
- Provide clear error messages for:
  - Invalid prompts
  - Failed model changes
  - Configuration save errors

## Technical Considerations

### 1. Integration Points
- Toolbar modification via `gui_hooks.top_toolbar_did_init_links`
- Settings storage using Anki's addon config system
- LLM interface through existing Groq client

### 2. Performance
- Settings changes should be instantaneous
- Prompt validation should be client-side
- Model switching should not require restart

### 3. Offline Support
- All settings should be modifiable offline
- Cache available model list for offline access
- Clearly indicate when online features are unavailable

## Default Values

### Default Prompt (Dory Hint Preset)
```
As a world-class instructor, create a helpful hint for a student studying with flashcards.
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
- Do NOT include any introductory text like "Here's a hint" - just output the hint directly
```

## Success Metrics
1. User engagement with custom prompts
2. Hint effectiveness ratings with different models
3. Settings modification frequency
4. Preset sharing between users

## Future Enhancements
1. Community prompt sharing
2. A/B testing different prompts
3. Advanced prompt templates
4. Per-deck prompt customization
5. Hint quality analytics

## Dependencies
- Anki 23.10+
- PyQt6
- Groq API client
- Internet connection (for model switching)

## Timeline
Phase 1 (MVP):
1. Basic settings dialog with model selection
2. Simple prompt editor with reset
3. Configuration persistence

Phase 2:
1. Preset management
2. Enhanced prompt editor
3. Usage analytics

Phase 3:
1. Community features
2. Advanced customization
3. Analytics dashboard
