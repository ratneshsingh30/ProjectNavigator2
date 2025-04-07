from .openai_helpers import get_summary, get_resources, generate_study_guide, generate_quiz
from .transcription import get_youtube_transcript, transcribe_audio
import logging

# Set up logging
logger = logging.getLogger(__name__)

def process_input(input_type, input_content):
    """
    Process the user input and generate study materials.
    
    Args:
        input_type (str): The type of input ('text', 'youtube', or 'audio')
        input_content: The actual content (text, YouTube URL, or audio file)
        
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
        
        else:
            logger.error(f"Invalid input type: {input_type}")
            return {"success": False, "error": "Invalid input type"}
        
        # If we have a valid transcript, proceed with generating study materials
        if result["success"] and result["transcript"]:
            # Determine the topic from the transcript (first few sentences)
            topic = ' '.join(result["transcript"].split()[:30])
            logger.info(f"Generated topic excerpt: {topic[:50]}...")
            
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
            
            logger.info("All processing completed successfully")
            result["success"] = True
            return result
        
        else:
            logger.error("Failed to process input: No valid transcript")
            return {"success": False, "error": "Failed to process input: No valid transcript"}
    
    except Exception as e:
        logger.exception(f"Unexpected error in process_input: {str(e)}")
        return {"success": False, "error": f"Error processing input: {str(e)}"}
