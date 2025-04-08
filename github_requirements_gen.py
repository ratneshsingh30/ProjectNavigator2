"""
GitHub Requirements Generator for AI Study Assistant

This script prints out the required packages for the AI Study Assistant
project when running it from GitHub or another environment.

Run this script to see the list of required packages that should be
included in your requirements.txt file.
"""

def print_requirements():
    """Print all requirements for the AI Study Assistant project."""
    requirements = [
        "streamlit>=1.30.0",
        "aiohttp>=3.9.1",
        "anthropic>=0.8.0",
        "faster-whisper>=0.9.0",
        "moviepy>=1.0.3",
        "nbformat>=5.9.2",
        "nltk>=3.8.1",
        "openai>=1.3.0",
        "pypdf2>=3.0.1",
        "python-docx>=1.0.1",
        "python-pptx>=0.6.21",
        "requests>=2.31.0",
        "speechrecognition>=3.10.0",
        "trafilatura>=1.6.0",
        "youtube-transcript-api>=0.6.1",
        "zipfile36>=0.1.3",
    ]
    
    print("# AI Study Assistant Requirements")
    print("# Copy these into your requirements.txt file for GitHub")
    print()
    for req in requirements:
        print(req)

if __name__ == "__main__":
    print_requirements()