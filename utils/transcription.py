import os
import tempfile
import requests
from youtube_transcript_api import YouTubeTranscriptApi
import re
from faster_whisper import WhisperModel

# Initialize Whisper model
# Options for model size: "tiny", "base", "small", "medium", "large-v2"
model_size = "base"
whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")

def extract_youtube_id(url):
    """Extract YouTube video ID from a URL."""
    # Common YouTube URL patterns
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&\s]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([^\?\s]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^\?\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_transcript(youtube_url):
    """Get transcript from a YouTube video URL."""
    try:
        # Extract video ID from the URL
        video_id = extract_youtube_id(youtube_url)
        
        if not video_id:
            return {"success": False, "error": "Could not extract YouTube video ID from the URL."}
        
        # Get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first, then fall back to other languages
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # If no English transcript, get the first available and translate it
            try:
                transcript = transcript_list.find_transcript(transcript_list.list_transcripts())
                transcript = transcript.translate('en')
            except:
                # If all else fails, get the first available without translation
                transcript = list(transcript_list)[0]
        
        # Get the transcript text
        transcript_data = transcript.fetch()
        
        # Combine all text pieces
        full_transcript = ' '.join([entry['text'] for entry in transcript_data])
        
        return {"success": True, "transcript": full_transcript}
    
    except Exception as e:
        return {"success": False, "error": f"Error getting YouTube transcript: {str(e)}"}

def transcribe_audio(audio_file):
    """Transcribe audio file using Hugging Face's faster-whisper implementation."""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            # Write uploaded file to the temp file
            temp_file.write(audio_file.getvalue())
            temp_path = temp_file.name
        
        # Transcribe the audio file with faster-whisper
        segments, info = whisper_model.transcribe(temp_path, beam_size=5)
        
        # Combine all segments into a full transcript
        transcription_text = ""
        for segment in segments:
            transcription_text += segment.text + " "
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return {"success": True, "transcript": transcription_text.strip()}
    
    except Exception as e:
        # Clean up the temporary file if it exists
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
        except:
            pass
        
        return {"success": False, "error": f"Error transcribing audio: {str(e)}"}
