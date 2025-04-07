import os
import json
import requests
import logging
import random
import time
import re

# Set up logging
logger = logging.getLogger(__name__)

# List of free AI API endpoints
# These are public endpoints that might have usage limitations but don't require API keys
FREE_ENDPOINTS = [
    "https://api-inference.huggingface.co/models/google/flan-t5-xxl",
    "https://api-inference.huggingface.co/models/facebook/bart-large-cnn", 
    "https://api-inference.huggingface.co/models/t5-base"
]

def get_random_endpoint():
    """Get a random endpoint from the list of free endpoints."""
    return random.choice(FREE_ENDPOINTS)

def make_api_request(prompt, max_retries=3, endpoint=None):
    """
    Make a request to a free AI API endpoint.
    
    Args:
        prompt (str): The prompt to send to the API
        max_retries (int): Maximum number of retries on failure
        endpoint (str, optional): Specific endpoint to use, or random if None
        
    Returns:
        str: The API response or None if all requests failed
    """
    if not endpoint:
        endpoint = get_random_endpoint()
    
    # Add Hugging Face API token if available
    headers = {"Content-Type": "application/json"}
    hf_token = os.environ.get("HUGGINGFACE_API_KEY")
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
    
    data = {"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.7}}
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Making request to free AI endpoint: {endpoint}")
            response = requests.post(endpoint, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()[0]["generated_text"]
            
            # If rate limited, wait and retry
            if response.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limited. Waiting {wait_time:.2f} seconds before retry.")
                time.sleep(wait_time)
                continue
                
            logger.error(f"API request failed with status code: {response.status_code}")
            # Try a different endpoint
            endpoint = get_random_endpoint()
            
        except Exception as e:
            logger.exception(f"Error making API request: {str(e)}")
            # Try a different endpoint
            endpoint = get_random_endpoint()
    
    return None

def get_summary(text, max_bullets=7):
    """
    Generate a summary of the given text in bullet points using free AI APIs.
    
    Args:
        text (str): The text to summarize
        max_bullets (int): Maximum number of bullet points to generate
        
    Returns:
        dict: Dictionary with success status and either summary or error message
    """
    try:
        # Truncate long inputs
        truncated_text = text[:10000] + "..." if len(text) > 10000 else text
        
        prompt = (
            f"Summarize the following text into {max_bullets} bullet points, "
            f"highlighting the key concepts:\n\n{truncated_text}"
        )
        
        # Try to get summary from free API
        generated_text = make_api_request(prompt)
        
        if generated_text:
            # Clean up and format the response
            summary_text = generated_text.strip()
            return {"success": True, "summary": summary_text}
        else:
            # Fallback to a very simple summary if all APIs fail
            sentences = truncated_text.split('. ')
            simple_summary = ". ".join(sentences[:max_bullets]) + "."
            logger.warning("Using fallback simple summary method")
            return {"success": True, "summary": simple_summary}
    
    except Exception as e:
        return {"success": False, "error": f"Error generating summary: {str(e)}"}

def get_resources(topic, max_resources=3):
    """
    Generate suggested resources for the given topic using free AI APIs.
    
    Args:
        topic (str): The topic to find resources for
        max_resources (int): Maximum number of resources to suggest
        
    Returns:
        dict: Dictionary with success status and either resources or error message
    """
    try:
        prompt = (
            f"Suggest {max_resources} educational resources about '{topic}'. "
            f"For each resource, provide: title, type (video, article, book, etc.), "
            f"a brief description, and a URL. Format as JSON list."
        )
        
        # Try to get resources from free API
        generated_text = make_api_request(prompt)
        
        if not generated_text:
            # If all APIs fail, create generic resources
            resources = []
            resource_types = ["Article", "Video", "Book"]
            
            for i in range(min(max_resources, 3)):
                resources.append({
                    "title": f"Resource for {topic} - {i+1}",
                    "type": resource_types[i % len(resource_types)],
                    "description": f"A resource about {topic}.",
                    "url": f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}"
                })
            
            return {"success": True, "resources": {"resources": resources}}
            
        # Try to parse JSON from the response
        try:
            # Check if the response contains JSON data enclosed in ```json ... ``` or similar
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', generated_text)
            
            if json_match:
                json_str = json_match.group(1)
                resources_data = json.loads(json_str)
            else:
                # Try to parse the whole response as JSON
                resources_data = json.loads(generated_text)
                
        except json.JSONDecodeError:
            # If JSON parsing fails, extract data with regex
            resource_pattern = r'- Title: "?(.*?)"?,\s*Type: "?(.*?)"?,\s*Description: "?(.*?)"?,\s*URL: "?(https?://[^"\s]+)'
            matches = re.findall(resource_pattern, generated_text)
            
            resources_data = []
            for match in matches:
                title, type_, description, url = match
                resources_data.append({
                    "title": title.strip(),
                    "type": type_.strip(),
                    "description": description.strip(),
                    "url": url.strip()
                })
        
        # Ensure the output is properly formatted
        if isinstance(resources_data, list):
            resources = resources_data
        else:
            resources = resources_data.get("resources", [])
            
        # Verify structure of resources and limit to max_resources
        valid_resources = []
        for i, res in enumerate(resources):
            if i >= max_resources:
                break
                
            valid_resource = {
                "title": res.get("title", f"Resource {i+1}"),
                "type": res.get("type", "Article"),
                "description": res.get("description", f"A resource about {topic}"),
                "url": res.get("url", f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}")
            }
            valid_resources.append(valid_resource)
            
        return {"success": True, "resources": {"resources": valid_resources}}
        
    except Exception as e:
        logger.exception(f"Error generating resources: {str(e)}")
        return {"success": False, "error": f"Error generating resources: {str(e)}"}
        
def generate_study_guide(text):
    """
    Generate a study guide with definitions, key terms, and flashcards using free AI APIs.
    
    Args:
        text (str): The text to generate a study guide from
        
    Returns:
        dict: Dictionary with success status and either study guide or error message
    """
    try:
        # Truncate long inputs
        truncated_text = text[:10000] + "..." if len(text) > 10000 else text
        
        prompt = (
            f"Create a study guide from this text with: "
            f"1. 5 key terms with definitions, "
            f"2. 5 important concepts, "
            f"3. 5 flashcards (question-answer pairs):\n\n{truncated_text}"
        )
        
        # Try to get study guide from free API
        generated_text = make_api_request(prompt)
        
        if not generated_text:
            # Simple fallback if all APIs fail
            return {"success": False, "error": "Unable to generate study guide from free APIs"}
        
        # Process and structure the response
        sections = {
            "key_terms": [],
            "important_concepts": [],
            "flashcards": []
        }
        
        # Extract key terms
        terms_pattern = r'(?:Key Terms?|Terms?|Definitions?)(?::|;|\n)(.*?)(?:(?:Important Concepts)|(?:Concepts)|(?:Flashcards)|$)'
        terms_match = re.search(terms_pattern, generated_text, re.DOTALL | re.IGNORECASE)
        
        if terms_match:
            terms_text = terms_match.group(1).strip()
            term_entries = re.findall(r'[\d\*\-\•]*\s*([^:]+)[:]\s*(.*?)(?=(?:[\d\*\-\•])|$)', terms_text, re.DOTALL)
            
            for term, definition in term_entries:
                if term and definition:
                    sections["key_terms"].append({
                        "term": term.strip(),
                        "definition": definition.strip()
                    })
        
        # Extract important concepts
        concepts_pattern = r'(?:Important Concepts|Concepts)(?::|;|\n)(.*?)(?:(?:Flashcards)|$)'
        concepts_match = re.search(concepts_pattern, generated_text, re.DOTALL | re.IGNORECASE)
        
        if concepts_match:
            concepts_text = concepts_match.group(1).strip()
            concept_entries = re.findall(r'[\d\*\-\•]*\s*(.*?)(?=(?:[\d\*\-\•])|$)', concepts_text, re.DOTALL)
            
            for concept in concept_entries:
                if concept.strip():
                    sections["important_concepts"].append(concept.strip())
        
        # Extract flashcards
        cards_pattern = r'(?:Flashcards)(?::|;|\n)(.*?)$'
        cards_match = re.search(cards_pattern, generated_text, re.DOTALL | re.IGNORECASE)
        
        if cards_match:
            cards_text = cards_match.group(1).strip()
            card_entries = re.findall(r'[\d\*\-\•]*\s*(?:Q:|Question:)?\s*([^?]*\?)\s*(?:A:|Answer:)?\s*(.*?)(?=(?:[\d\*\-\•](?:\s*(?:Q:|Question:)))|$)', cards_text, re.DOTALL | re.IGNORECASE)
            
            for question, answer in card_entries:
                if question and answer:
                    sections["flashcards"].append({
                        "question": question.strip(),
                        "answer": answer.strip()
                    })
        
        # If parsing fails, create minimal items
        if not sections["key_terms"]:
            words = re.findall(r'\b[A-Z][a-z]{5,}\b', truncated_text)
            for i, word in enumerate(set(words)):
                if i >= 5:
                    break
                sections["key_terms"].append({
                    "term": word,
                    "definition": f"A concept related to the main topic."
                })
        
        if not sections["important_concepts"]:
            sentences = re.split(r'(?<=[.!?])\s+', truncated_text)
            for i, sentence in enumerate(sentences):
                if i >= 5 or i >= len(sentences):
                    break
                if len(sentence.split()) > 5:
                    sections["important_concepts"].append(sentence)
        
        if not sections["flashcards"]:
            sentences = re.split(r'(?<=[.!?])\s+', truncated_text)
            for i in range(min(5, len(sentences) // 2)):
                if 2*i+1 < len(sentences):
                    sections["flashcards"].append({
                        "question": f"What is described in this sentence? '{sentences[2*i]}'",
                        "answer": sentences[2*i+1] if 2*i+1 < len(sentences) else "See the text for details."
                    })
        
        return {"success": True, "study_guide": {"study_guide": sections}}
    
    except Exception as e:
        logger.exception(f"Error generating study guide: {str(e)}")
        return {"success": False, "error": f"Error generating study guide: {str(e)}"}
        
def generate_quiz(text, num_questions=5):
    """
    Generate multiple-choice quiz questions based on the text using free AI APIs.
    
    Args:
        text (str): The text to generate questions from
        num_questions (int): Number of questions to generate
        
    Returns:
        dict: Dictionary with success status and either quiz or error message
    """
    try:
        # Truncate long inputs
        truncated_text = text[:10000] + "..." if len(text) > 10000 else text
        
        prompt = (
            f"Create {num_questions} multiple-choice quiz questions based on this text. "
            f"For each question, provide 4 options (A, B, C, D), indicate the correct answer, "
            f"and give a brief explanation for the answer:\n\n{truncated_text}"
        )
        
        # Try to get quiz from free API
        generated_text = make_api_request(prompt)
        
        if not generated_text:
            # Simple fallback if all APIs fail
            return {"success": False, "error": "Unable to generate quiz from free APIs"}
        
        # Process and structure the response
        quiz_questions = []
        
        # Extract questions, options, answers and explanations
        questions = re.split(r'\d+\.\s+', generated_text)
        # Remove empty first element if split creates it
        if questions and not questions[0].strip():
            questions = questions[1:]
        
        for i, q_text in enumerate(questions):
            if not q_text.strip() or i >= num_questions:
                continue
                
            # Extract question text
            question_match = re.match(r'([^\n]+)', q_text)
            if not question_match:
                continue
            
            question = question_match.group(1).strip()
            
            # Extract options
            options = {}
            option_matches = re.findall(r'([A-D])(?:\.|\))\s+([^\n]+)', q_text)
            
            for opt, text in option_matches:
                options[opt] = text.strip()
            
            # If not enough options found, create placeholders
            while len(options) < 4:
                missing = [opt for opt in "ABCD" if opt not in options]
                if not missing:
                    break
                options[missing[0]] = f"Option {missing[0]}"
            
            # Extract correct answer
            correct_match = re.search(r'(?:Answer|Correct(?:\s+Answer)?|The correct answer is)[^A-D]*([A-D])', q_text, re.IGNORECASE)
            correct_answer = correct_match.group(1) if correct_match else "A"
            
            # Extract explanation
            explanation_match = re.search(r'(?:Explanation|Reason)[^\n]*:\s*([^\n]+)', q_text, re.IGNORECASE)
            explanation = explanation_match.group(1).strip() if explanation_match else "See the text for details."
            
            quiz_questions.append({
                "question": question,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": explanation
            })
        
        # Ensure we have the requested number of questions
        if len(quiz_questions) < num_questions:
            # Extract sentences for basic questions if needed
            sentences = re.split(r'(?<=[.!?])\s+', truncated_text)
            keywords = re.findall(r'\b[A-Z][a-z]{5,}\b', truncated_text)
            
            for i in range(len(quiz_questions), num_questions):
                if i < len(sentences) and len(sentences[i].split()) > 5:
                    # Create a question from a sentence
                    sentence = sentences[i]
                    words = sentence.split()
                    
                    if len(words) > 3:
                        # Replace a key word with blank
                        blank_idx = random.randint(1, len(words) - 2)
                        blank_word = words[blank_idx]
                        question_text = " ".join(words[:blank_idx] + ["_____"] + words[blank_idx+1:])
                        
                        options = {
                            "A": blank_word,
                            "B": keywords[i % len(keywords)] if i < len(keywords) else "alternative",
                            "C": keywords[(i+1) % len(keywords)] if i+1 < len(keywords) else "option",
                            "D": keywords[(i+2) % len(keywords)] if i+2 < len(keywords) else "choice"
                        }
                        
                        quiz_questions.append({
                            "question": f"Fill in the blank: {question_text}",
                            "options": options,
                            "correct_answer": "A",
                            "explanation": f"The complete sentence is: {sentence}"
                        })
        
        return {"success": True, "quiz": {"quiz": quiz_questions}}
    
    except Exception as e:
        logger.exception(f"Error generating quiz: {str(e)}")
        return {"success": False, "error": f"Error generating quiz: {str(e)}"}