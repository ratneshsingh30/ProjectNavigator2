# 🎓 AI Study Assistant

An AI-powered study companion that transforms learning content into personalized, interactive study materials using cutting-edge technologies and intelligent design.

## Features

- **Multiple Input Sources**: Process text, YouTube URLs, audio files, and various document formats (PDF, DOCX, PPTX, Python files, Jupyter notebooks)
- **Comprehensive Study Materials**: Generate summaries, flashcards, quizzes, resource suggestions, and detailed topic notes
- **Fallback Mechanisms**: Robust error handling with multiple AI service options and static fallbacks
- **Interactive UI**: Clean, intuitive Streamlit interface for easy navigation
- **Export Options**: Download study materials in multiple formats

## Requirements

To run this project, you'll need Python 3.8+ and the following packages:

```
streamlit>=1.30.0
aiohttp>=3.9.1
anthropic>=0.8.0
faster-whisper>=0.9.0
moviepy>=1.0.3
nbformat>=5.9.2
nltk>=3.8.1
openai>=1.3.0
pypdf2>=3.0.1
python-docx>=1.0.1
python-pptx>=0.6.21
requests>=2.31.0
speechrecognition>=3.10.0
trafilatura>=1.6.0
youtube-transcript-api>=0.6.1
zipfile36>=0.1.3
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-study-assistant.git
   cd ai-study-assistant
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys (optional, app has fallback mechanisms):
   ```
   export OPENAI_API_KEY="your-openai-api-key"
   export HUGGINGFACE_API_KEY="your-huggingface-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

## Usage

Run the Streamlit app:
```
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Project Structure

- `app.py`: Main Streamlit application
- `utils/`: Utility modules
  - `content_processor.py`: Core logic for processing different types of content
  - `static_fallbacks.py`: Fallback generators when API services fail
  - `file_processor.py`: Handles various file formats
  - `transcription.py`: Audio and video transcription utilities
  - `openai_helpers.py`: OpenAI API integration
  - `free_ai_helpers.py`: Alternative free AI services
  - `personal_insight.py`: Personalized content based on user profiles
  - `export_utils.py`: Export functionality

## License

[MIT License](LICENSE)