from .openai_helpers import get_summary, get_resources, generate_study_guide, generate_quiz
from .transcription import get_youtube_transcript, transcribe_audio

def process_input(input_type, input_content):
    """
    Process the user input and generate study materials.
    
    Args:
        input_type (str): The type of input ('text', 'youtube', or 'audio')
        input_content: The actual content (text, YouTube URL, or audio file)
        
    Returns:
        dict: Dictionary with all generated study materials and success status
    """
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
            result["transcript"] = input_content
            result["success"] = True
        
        elif input_type == "youtube":
            transcript_result = get_youtube_transcript(input_content)
            if transcript_result["success"]:
                result["transcript"] = transcript_result["transcript"]
                result["success"] = True
            else:
                return {"success": False, "error": transcript_result["error"]}
        
        elif input_type == "audio":
            transcript_result = transcribe_audio(input_content)
            if transcript_result["success"]:
                result["transcript"] = transcript_result["transcript"]
                result["success"] = True
            else:
                return {"success": False, "error": transcript_result["error"]}
        
        else:
            return {"success": False, "error": "Invalid input type"}
        
        # If we have a valid transcript, proceed with generating study materials
        if result["success"] and result["transcript"]:
            # Determine the topic from the transcript (first few sentences)
            topic = ' '.join(result["transcript"].split()[:30])
            
            # Step 2: Generate summary
            summary_result = get_summary(result["transcript"])
            if summary_result["success"]:
                result["summary"] = summary_result["summary"]
            else:
                result["error"] = summary_result["error"]
                return result
            
            # Step 3: Find resources
            resources_result = get_resources(topic)
            if resources_result["success"]:
                result["resources"] = resources_result["resources"]
            else:
                result["error"] = resources_result["error"]
                return result
            
            # Step 4: Generate study guide
            study_guide_result = generate_study_guide(result["transcript"])
            if study_guide_result["success"]:
                result["study_guide"] = study_guide_result["study_guide"]
            else:
                result["error"] = study_guide_result["error"]
                return result
            
            # Step 5: Generate quiz
            quiz_result = generate_quiz(result["transcript"])
            if quiz_result["success"]:
                result["quiz"] = quiz_result["quiz"]
            else:
                result["error"] = quiz_result["error"]
                return result
            
            result["success"] = True
            return result
        
        else:
            return {"success": False, "error": "Failed to process input"}
    
    except Exception as e:
        return {"success": False, "error": f"Error processing input: {str(e)}"}
