from .openai_helpers import get_summary as openai_get_summary
from .openai_helpers import get_resources as openai_get_resources
from .openai_helpers import generate_study_guide as openai_generate_study_guide
from .openai_helpers import generate_quiz as openai_generate_quiz
from .transcription import get_youtube_transcript, transcribe_audio
from .file_processor import process_file
import logging
import os
import io
import re
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

# Import free AI helpers as fallbacks
from .free_ai_helpers import get_summary as free_get_summary
from .free_ai_helpers import get_resources as free_get_resources
from .free_ai_helpers import generate_study_guide as free_generate_study_guide
from .free_ai_helpers import generate_quiz as free_generate_quiz
from .free_ai_helpers import generate_detailed_notes

# Try to download NLTK resources silently
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except:
    # Continue even if download fails
    pass

# Set up logging
logger = logging.getLogger(__name__)

def extract_main_topics(text, top_n=3):
    """
    Extract the main topics from a text using NLP techniques.
    
    Args:
        text (str): The text to extract topics from
        top_n (int): Number of topics to extract
        
    Returns:
        str: The main topic as a string
    """
    try:
        # Clean the text
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Try to find specific topic markers
        topic_keywords = ["topic:", "subject:", "about:", "focuses on:"]
        for keyword in topic_keywords:
            if keyword in text.lower():
                idx = text.lower().find(keyword) + len(keyword)
                end_idx = text.find('.', idx)
                if end_idx > 0:
                    topic = text[idx:end_idx].strip()
                    if 3 <= len(topic.split()) <= 10:
                        return topic
        
        # Find main topic from slide titles
        slide_pattern = r'Slide \d+:?\s*([^0-9\n]+?)(?:\d|$)'
        slide_titles = re.findall(slide_pattern, text)
        if slide_titles:
            # Get the most common meaningful slide title
            filtered_titles = [title.strip() for title in slide_titles 
                             if len(title.split()) <= 5 and len(title.strip()) > 3]
            if filtered_titles:
                return max(set(filtered_titles), key=filtered_titles.count)
        
        # Try to find the main subject using frequency analysis
        try:
            # Tokenize
            words = word_tokenize(text.lower())
            
            # Filter stop words and short words
            try:
                stop_words = set(stopwords.words('english'))
            except:
                # Fallback if NLTK data is not available
                stop_words = {"the", "and", "a", "an", "in", "on", "at", "with", "for", "to", "of", "is", "are"}
            
            words = [word for word in words if word not in stop_words and len(word) > 3]
            
            # Get the most frequent words
            word_freq = Counter(words)
            most_common_words = [word for word, _ in word_freq.most_common(15)]
            
            # Look for these words in sentences to extract key phrases
            sentences = sent_tokenize(text)
            topic_candidates = []
            
            for sent in sentences[:10]:  # Look at first 10 sentences
                for word in most_common_words:
                    if word in sent.lower():
                        topic_candidates.append(sent.strip())
                        break
            
            if topic_candidates:
                # Return the first good candidate
                for candidate in topic_candidates:
                    # Extract a reasonably sized phrase
                    if 10 <= len(candidate.split()) <= 30:
                        return ' '.join(candidate.split()[:7])  # First 7 words
                    elif len(candidate.split()) < 10:
                        return candidate
                
                # If we got here, return the shortest candidate
                shortest = min(topic_candidates, key=lambda x: len(x.split()))
                return ' '.join(shortest.split()[:5])  # First 5 words
        except:
            # If NLP processing fails, fall back to a simpler approach
            pass
        
        # Simple fallback: Extract first 3-5 meaningful words from first sentence
        first_sentence = text.split('.')[0]
        words = first_sentence.split()
        try:
            stop_words = set(stopwords.words('english'))
        except:
            # Fallback if NLTK data is not available
            stop_words = {"the", "and", "a", "an", "in", "on", "at", "with", "for", "to", "of", "is", "are"}
        clean_words = [w for w in words if len(w) > 3 and w.lower() not in stop_words][:5]
        
        # If we still have nothing, just return the first few words
        if not clean_words and words:
            return ' '.join(words[:5])
        
        return ' '.join(clean_words)
    
    except Exception as e:
        logger.exception(f"Error extracting main topics: {str(e)}")
        # Return first few words of text as a fallback
        return ' '.join(text.split()[:5])

# Define fallback wrapper functions that try OpenAI first, then free APIs
def get_summary(text, max_bullets=7):
    """Wrapper that tries OpenAI first, then free AI helper."""
    try:
        # Try OpenAI first
        logger.info("Trying OpenAI for summary")
        result = openai_get_summary(text, max_bullets)
        if result["success"]:
            return result
        
        # If OpenAI fails, try free AI helper
        logger.info("OpenAI failed, trying free AI for summary")
        result = free_get_summary(text, max_bullets)
        return result
    except Exception as e:
        logger.exception(f"Error in get_summary fallback: {str(e)}")
        # If all else fails, try free API directly
        return free_get_summary(text, max_bullets)

def get_resources(topic, max_resources=3):
    """Wrapper that tries OpenAI first, then free AI helper."""
    try:
        # Try OpenAI first
        logger.info("Trying OpenAI for resources")
        result = openai_get_resources(topic, max_resources)
        if result["success"]:
            return result
        
        # If OpenAI fails, try free AI helper
        logger.info("OpenAI failed, trying free AI for resources")
        result = free_get_resources(topic, max_resources)
        return result
    except Exception as e:
        logger.exception(f"Error in get_resources fallback: {str(e)}")
        # If all else fails, try free API directly
        return free_get_resources(topic, max_resources)

def generate_study_guide(text):
    """Wrapper that tries OpenAI first, then free AI helper."""
    try:
        # Try OpenAI first
        logger.info("Trying OpenAI for study guide")
        result = openai_generate_study_guide(text)
        if result["success"]:
            return result
        
        # If OpenAI fails, try free AI helper
        logger.info("OpenAI failed, trying free AI for study guide")
        result = free_generate_study_guide(text)
        return result
    except Exception as e:
        logger.exception(f"Error in generate_study_guide fallback: {str(e)}")
        # If all else fails, try free API directly
        return free_generate_study_guide(text)

def generate_quiz(text, num_questions=5):
    """Wrapper that tries OpenAI first, then free AI helper."""
    try:
        # Try OpenAI first
        logger.info("Trying OpenAI for quiz")
        result = openai_generate_quiz(text, num_questions)
        if result["success"]:
            return result
        
        # If OpenAI fails, try free AI helper
        logger.info("OpenAI failed, trying free AI for quiz")
        result = free_generate_quiz(text, num_questions)
        return result
    except Exception as e:
        logger.exception(f"Error in generate_quiz fallback: {str(e)}")
        # If all else fails, try free API directly
        return free_generate_quiz(text, num_questions)

def generate_topic_notes(text, max_sections=3):
    """Generate detailed notes for each topic with key points in bold and examples."""
    try:
        logger.info("Generating detailed topic notes")
        # No OpenAI version yet, just use the free AI helper
        result = generate_detailed_notes(text, max_sections)
        if not result["success"]:
            logger.error(f"Failed to generate detailed notes: {result.get('error', 'Unknown error')}")
        return result
    except Exception as e:
        logger.exception(f"Error in generate_topic_notes: {str(e)}")
        return {"success": False, "error": f"Error generating detailed notes: {str(e)}"}

def process_input(input_type, input_content):
    """
    Process the user input and generate study materials.
    
    Args:
        input_type (str): The type of input ('text', 'youtube', 'audio', or 'file')
        input_content: The actual content (text, YouTube URL, audio file, or uploaded file)
        
    Returns:
        dict: Dictionary with all generated study materials and success status
    """
    logger.info(f"Processing input of type: {input_type}")
    
    result = {
        "success": False,
        "transcript": None,
        "summary": None,
        "resources": None,
        "study_guide": None,
        "quiz": None,
        "detailed_notes": None,
        "error": None
    }
    
    try:
        # Step 1: Get the text content based on input type
        if input_type == "text":
            logger.info("Processing text input")
            result["transcript"] = input_content
            result["success"] = True
        
        elif input_type == "youtube":
            logger.info(f"Processing YouTube URL: {input_content}")
            transcript_result = get_youtube_transcript(input_content)
            if transcript_result["success"]:
                logger.info("Successfully retrieved YouTube transcript")
                result["transcript"] = transcript_result["transcript"]
                result["success"] = True
            else:
                logger.error(f"Failed to get YouTube transcript: {transcript_result['error']}")
                return {"success": False, "error": transcript_result["error"]}
        
        elif input_type == "audio":
            logger.info("Processing audio file")
            transcript_result = transcribe_audio(input_content)
            if transcript_result["success"]:
                logger.info("Successfully transcribed audio")
                result["transcript"] = transcript_result["transcript"]
                result["success"] = True
            else:
                logger.error(f"Failed to transcribe audio: {transcript_result['error']}")
                return {"success": False, "error": transcript_result["error"]}
                
        elif input_type == "file":
            logger.info(f"Processing file: {input_content.name}")
            # Check if it's a video file that needs audio extraction
            file_extension = input_content.name.split('.')[-1].lower()
            
            if file_extension in ['mp4', 'mov', 'avi', 'mkv']:
                logger.info("Processing video file for audio extraction")
                video_result = process_file(input_content)
                
                if video_result["success"] and "audio_file" in video_result:
                    logger.info("Successfully extracted audio from video, transcribing...")
                    # Now transcribe the extracted audio
                    transcript_result = transcribe_audio(video_result["audio_file"])
                    
                    if transcript_result["success"]:
                        logger.info("Successfully transcribed audio from video")
                        result["transcript"] = transcript_result["transcript"]
                        result["success"] = True
                    else:
                        logger.error(f"Failed to transcribe audio from video: {transcript_result['error']}")
                        return {"success": False, "error": transcript_result["error"]}
                else:
                    logger.error(f"Failed to process video file: {video_result.get('error', 'Unknown error')}")
                    return {"success": False, "error": video_result.get("error", "Failed to process video file")}
            else:
                # For all other file types, extract text content
                file_result = process_file(input_content)
                
                if file_result["success"]:
                    logger.info(f"Successfully processed file")
                    result["transcript"] = file_result["text"]
                    result["success"] = True
                    
                    # If it's a ZIP file, add a note about processing multiple files
                    if file_extension == 'zip' and 'file_count' in file_result:
                        logger.info(f"Processed {file_result['file_count']} files from ZIP archive")
                        result["transcript"] = f"[Processed {file_result['file_count']} files from ZIP archive]\n\n" + result["transcript"]
                else:
                    logger.error(f"Failed to process file: {file_result.get('error', 'Unknown error')}")
                    return {"success": False, "error": file_result.get("error", "Failed to process file")}
        else:
            logger.error(f"Invalid input type: {input_type}")
            return {"success": False, "error": "Invalid input type"}
        
        # If we have a valid transcript, proceed with generating study materials
        if result["success"] and result["transcript"]:
            # Extract main topic using our improved topic extraction function
            topic = extract_main_topics(result["transcript"])
            logger.info(f"Extracted main topic: {topic}")
            
            # Step 2: Generate summary
            logger.info("Generating summary")
            summary_result = get_summary(result["transcript"])
            if summary_result["success"]:
                logger.info("Summary generated successfully")
                result["summary"] = summary_result["summary"]
            else:
                logger.error(f"Failed to generate summary: {summary_result['error']}")
                result["error"] = summary_result["error"]
                return result
            
            # Step 3: Find resources
            logger.info("Finding resources")
            resources_result = get_resources(topic)
            if resources_result["success"]:
                logger.info("Resources found successfully")
                result["resources"] = resources_result["resources"]
            else:
                logger.error(f"Failed to find resources: {resources_result['error']}")
                result["error"] = resources_result["error"]
                return result
            
            # Step 4: Generate study guide
            logger.info("Generating study guide")
            study_guide_result = generate_study_guide(result["transcript"])
            if study_guide_result["success"]:
                logger.info("Study guide generated successfully")
                result["study_guide"] = study_guide_result["study_guide"]
            else:
                logger.error(f"Failed to generate study guide: {study_guide_result['error']}")
                result["error"] = study_guide_result["error"]
                return result
            
            # Step 5: Generate quiz
            logger.info("Generating quiz")
            quiz_result = generate_quiz(result["transcript"])
            if quiz_result["success"]:
                logger.info("Quiz generated successfully")
                result["quiz"] = quiz_result["quiz"]
            else:
                logger.error(f"Failed to generate quiz: {quiz_result['error']}")
                result["error"] = quiz_result["error"]
                return result
            
            # Step 6: Generate detailed notes with examples
            logger.info("Generating detailed topic notes")
            notes_result = generate_topic_notes(result["transcript"])
            if notes_result["success"]:
                logger.info("Detailed notes generated successfully")
                result["detailed_notes"] = {"notes": notes_result["notes"]}
            else:
                logger.error(f"Failed to generate detailed notes: {notes_result['error']}")
                # Don't return error here, as this is a bonus feature
                # Just continue without detailed notes
                
            logger.info("All processing completed successfully")
            result["success"] = True
            return result
        
        else:
            logger.error("Failed to process input: No valid transcript")
            return {"success": False, "error": "Failed to process input: No valid transcript"}
    
    except Exception as e:
        logger.exception(f"Unexpected error in process_input: {str(e)}")
        return {"success": False, "error": f"Error processing input: {str(e)}"}
