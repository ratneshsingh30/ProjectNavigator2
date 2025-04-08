import os
import json
import requests
import logging
import random
import time
import re

# Set up logging
logger = logging.getLogger(__name__)

def get_reliable_url(topic, resource_type="Article"):
    """
    Generate a reliable URL for a given topic and resource type.
    
    Args:
        topic (str): The topic to generate a URL for
        resource_type (str): The type of resource (Article, Video, Course, etc.)
        
    Returns:
        str: A reliable URL to an educational resource
    """
    topic_formatted = topic.replace(' ', '-').lower()
    
    # Map of reliable educational websites by resource type
    url_templates = {
        "Video": [
            f"https://www.youtube.com/results?search_query={topic.replace(' ', '+')}+lecture",
            f"https://www.khanacademy.org/search?page_search_query={topic.replace(' ', '+')}",
            f"https://ed.ted.com/search?qs={topic.replace(' ', '+')}"
        ],
        "Course": [
            f"https://www.coursera.org/search?query={topic.replace(' ', '+')}",
            f"https://www.edx.org/search?q={topic.replace(' ', '+')}",
            f"https://ocw.mit.edu/search/?q={topic.replace(' ', '+')}"
        ],
        "Article": [
            f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
            f"https://www.khanacademy.org/search?page_search_query={topic.replace(' ', '+')}",
            f"https://www.britannica.com/search?query={topic.replace(' ', '+')}"
        ],
        "Book": [
            f"https://openlibrary.org/search?q={topic.replace(' ', '+')}",
            f"https://books.google.com/books?q={topic.replace(' ', '+')}"
        ]
    }
    
    # Default to Article if resource_type not found
    if resource_type not in url_templates:
        resource_type = "Article"
    
    # Return a random URL from the appropriate category
    return random.choice(url_templates[resource_type])

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
            f"Create a structured summary of key concepts from this text:\n\n"
            f"{truncated_text}\n\n"
            f"Structure your response with:\n"
            f"1. Major headings using markdown format (## Heading)\n"
            f"2. Under each heading, provide:\n"
            f"   - A clear definition or explanation\n"
            f"   - Key points as bullet points\n" 
            f"   - Important terms in **bold**\n"
            f"   - At least one example for each concept\n"
            f"   - If diagrams were described, add [DIAGRAM: brief description]\n\n"
            f"Include max {max_bullets} major headings. Use markdown formatting throughout."
        )
        
        # Try to get summary from free API
        generated_text = make_api_request(prompt)
        
        if generated_text:
            # Clean up and format the response
            summary_text = generated_text.strip()
            return {"success": True, "summary": summary_text}
        else:
            # Create a more structured fallback summary if all APIs fail
            logger.warning("Using fallback structured summary method")
            
            # Extract sentences and organize by potential topics
            sentences = re.split(r'(?<=[.!?])\s+', truncated_text)
            
            # Find capitalized phrases that might be topics or key terms
            topics = []
            key_terms = []
            
            for sentence in sentences:
                # Look for capitalized multi-word phrases that might be topics
                topic_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})', sentence)
                topics.extend(topic_matches)
                
                # Look for capitalized terms that might be key terms
                term_matches = re.findall(r'\b([A-Z][a-z]{3,})\b', sentence)
                key_terms.extend(term_matches)
            
            # Get unique topics and terms
            topics = list(set(topics))[:max_bullets]
            key_terms = list(set(key_terms))
            
            # Build structured summary
            structured_summary = "# Key Concepts Summary\n\n"
            
            # Add topics as sections
            for i, topic in enumerate(topics[:max_bullets]):
                # Create heading
                structured_summary += f"## {topic}\n\n"
                
                # Add definition - find sentences containing the topic
                topic_sentences = [s for s in sentences if topic in s]
                if topic_sentences:
                    structured_summary += f"{topic_sentences[0]}\n\n"
                
                # Add bullet points - use nearby sentences
                structured_summary += "Key points:\n\n"
                bullet_count = min(3, len(topic_sentences) - 1)
                for j in range(bullet_count):
                    idx = min(j + 1, len(topic_sentences) - 1)
                    point = topic_sentences[idx]
                    # Highlight any key terms
                    for term in key_terms:
                        if term in point:
                            point = point.replace(term, f"**{term}**")
                    structured_summary += f"• {point}\n"
                structured_summary += "\n"
            
            # If no topics were found, use generic headings
            if not topics:
                chunk_size = len(sentences) // max_bullets
                for i in range(min(max_bullets, len(sentences) // 5)):
                    start_idx = i * chunk_size
                    end_idx = min(start_idx + chunk_size, len(sentences))
                    chunk = sentences[start_idx:end_idx]
                    
                    structured_summary += f"## Topic {i+1}\n\n"
                    if chunk:
                        structured_summary += f"{chunk[0]}\n\n"
                        structured_summary += "Key points:\n\n"
                        for j in range(min(3, len(chunk) - 1)):
                            point = chunk[j + 1]
                            structured_summary += f"• {point}\n"
                    structured_summary += "\n"
            
            return {"success": True, "summary": structured_summary}
    
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
            
            # Use more reliable URLs and better resource descriptions when AI fails
            reliable_sources = [
                {
                    "title": f"Khan Academy: {topic}",
                    "type": "Learning Platform",
                    "description": f"Khan Academy offers free educational resources on {topic} with video lessons, practice exercises, and a personalized learning dashboard.",
                    "url": "https://www.khanacademy.org/search?referer=%2F&page_search_query=" + topic.replace(' ', '+')
                },
                {
                    "title": f"Coursera Courses on {topic}",
                    "type": "Online Courses",
                    "description": f"Find university-level courses on {topic} from top institutions, many of which offer free auditing options.",
                    "url": "https://www.coursera.org/search?query=" + topic.replace(' ', '+')
                },
                {
                    "title": f"{topic} on MIT OpenCourseWare",
                    "type": "Academic Resource",
                    "description": f"MIT OpenCourseWare offers free lecture notes, videos, and assignments from actual MIT courses related to {topic}.",
                    "url": "https://ocw.mit.edu/search/?q=" + topic.replace(' ', '+')
                },
                {
                    "title": f"{topic} - Learning Resources",
                    "type": "Educational Websites",
                    "description": f"Educational resources focusing on {topic} from multiple sources, with tutorials, guides, and interactive learning materials.",
                    "url": "https://www.google.com/search?q=" + topic.replace(' ', '+') + "+learning+resources"
                }
            ]
            
            # Include as many resources as requested, up to what we have available
            for i in range(min(max_resources, len(reliable_sources))):
                resources.append(reliable_sources[i])
            
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
                "url": res.get("url", get_reliable_url(topic, res.get("type", "Article")))
            }
            valid_resources.append(valid_resource)
            
        return {"success": True, "resources": {"resources": valid_resources}}
        
    except Exception as e:
        logger.exception(f"Error generating resources: {str(e)}")
        return {"success": False, "error": f"Error generating resources: {str(e)}"}
        
def generate_detailed_notes(text, max_sections=3):
    """
    Generate detailed notes with key points highlighted in bold.
    
    Args:
        text (str): The text to generate notes from
        max_sections (int): Maximum number of topic sections to include
        
    Returns:
        dict: Dictionary with success status and either notes or error message
    """
    try:
        # Truncate long inputs
        truncated_text = text[:10000] + "..." if len(text) > 10000 else text
        
        prompt = (
            f"Create detailed study notes on this content with {max_sections} main topic sections. "
            f"For each section include: \n"
            f"1. A clear title/heading\n"
            f"2. A concise definition of the topic\n"
            f"3. 3-5 key points marked in bold (**key point**)\n"
            f"4. At least one specific example\n"
            f"5. If applicable, mention where diagrams or visual aids would be helpful\n\n"
            f"Format each section as a complete unit with all these elements. "
            f"Use markdown formatting throughout.\n\n{truncated_text}"
        )
        
        # Try to get notes from free API
        generated_text = make_api_request(prompt)
        
        if not generated_text:
            # Create basic notes from the text if API fails
            sections = []
            sentences = re.split(r'(?<=[.!?])\s+', truncated_text)
            
            # Try to identify potential section topics
            potential_topics = []
            for i, sentence in enumerate(sentences):
                if len(sentence.split()) <= 10 and len(sentence.split()) >= 3:
                    # Short sentences might be headings/topics
                    if i < len(sentences) - 5:  # Ensure there's content after
                        potential_topics.append((i, sentence))
            
            # If we don't find potential topics, create artificial ones
            if not potential_topics or len(potential_topics) < max_sections:
                chunks = [sentences[i:i + len(sentences)//max_sections] for i in range(0, len(sentences), len(sentences)//max_sections)]
                for i, chunk in enumerate(chunks[:max_sections]):
                    if chunk:
                        # Extract key words for a topic
                        all_words = " ".join(chunk).split()
                        topic_words = [w for w in all_words if len(w) > 4 and w[0].isupper()]
                        
                        # Create a topic title
                        if topic_words and len(topic_words) >= 2:
                            topic = " ".join(topic_words[:2])
                        else:
                            topic = f"Topic {i+1}"
                        
                        # Create a definition (first sentence)
                        definition = chunk[0] if chunk else "No definition available."
                            
                        # Find key points (longer sentences)
                        key_points = []
                        for sentence in chunk:
                            if len(sentence.split()) >= 8:
                                key_points.append(sentence)
                            if len(key_points) >= 3:
                                break
                        
                        # Build content with the remaining sentences
                        remaining = [s for s in chunk if s not in key_points and s != definition]
                        content = " ".join(remaining[:5])  # First few sentences
                        
                        # Create examples
                        examples = []
                        for sentence in remaining:
                            if "example" in sentence.lower() or "instance" in sentence.lower() or "case" in sentence.lower():
                                examples.append(sentence)
                                
                        example = examples[0] if examples else "For example, " + (remaining[-1] if remaining else key_points[0])
                        
                        # Check for potential diagram references
                        diagrams = []
                        for sentence in chunk:
                            if any(term in sentence.lower() for term in ["diagram", "figure", "image", "picture", "illustration", "graph", "chart"]):
                                diagrams.append(sentence)
                        
                        # Add the section
                        sections.append({
                            "topic": topic,
                            "definition": definition,
                            "key_points": key_points[:3],
                            "content": content,
                            "examples": [example],
                            "diagrams": diagrams
                        })
            
            return {"success": True, "notes": sections}
        
        # Try to parse the generated text into sections
        sections = []
        
        # Split by markdown headers (## or # headers)
        section_texts = re.split(r'(?m)^#+\s+(.+?)$', generated_text)
        
        # Process each section
        current_title = None
        for i, text_block in enumerate(section_texts):
            if i % 2 == 0 and i > 0:  # Even indexes after 0 are content blocks
                # Extract key points (bolded text)
                key_points = re.findall(r'\*\*(.+?)\*\*', text_block)
                
                # Extract definition (first paragraph after title)
                paragraphs = text_block.split('\n\n')
                definition = paragraphs[0].strip() if paragraphs else "No definition available."
                
                # Extract examples
                examples = []
                example_matches = re.finditer(r'(?:Example|For example|For instance|e\.g\.)[:\s]+(.*?)(?=(?:\n\n)|$)', text_block, re.IGNORECASE | re.DOTALL)
                for match in example_matches:
                    examples.append(match.group(1).strip())
                
                if not examples:
                    examples = ["No specific example provided."]
                
                # Extract diagram references
                diagrams = []
                diagram_matches = re.finditer(r'(?:Diagram|Figure|Visual|Image|Picture|Illustration|Graph|Chart)[:\s]+(.*?)(?=(?:\n\n)|$)', text_block, re.IGNORECASE | re.DOTALL)
                for match in diagram_matches:
                    diagrams.append(match.group(1).strip())
                
                # Remove the key points from content for clarity
                content = text_block
                for point in key_points:
                    content = content.replace(f"**{point}**", point)
                
                # Clean up content
                content = re.sub(r'\n{3,}', '\n\n', content.strip())
                
                # Add the section
                sections.append({
                    "topic": current_title,
                    "definition": definition,
                    "key_points": key_points,
                    "content": content,
                    "examples": examples,
                    "diagrams": diagrams
                })
            elif i % 2 == 1:  # Odd indexes are section titles
                current_title = text_block.strip()
        
        # If no sections were extracted, use a simple approach
        if not sections:
            paragraphs = generated_text.split('\n\n')
            for i, para in enumerate(paragraphs[:max_sections]):
                if para.strip():
                    # Try to find a title in the paragraph
                    first_line = para.split('\n')[0].strip()
                    title = first_line if len(first_line.split()) <= 7 else f"Topic {i+1}"
                    
                    # Find key sentences (ones with key terms)
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    definition = sentences[0] if sentences else "No definition available."
                    
                    key_sentences = []
                    for sentence in sentences[1:]:  # Skip first sentence (definition)
                        if any(term in sentence.lower() for term in ["key", "important", "critical", "essential", "fundamental"]):
                            key_sentences.append(sentence)
                        if len(key_sentences) >= 3:
                            break
                    
                    # If no key sentences found, use the longest ones
                    if not key_sentences:
                        key_sentences = sorted(sentences[1:], key=len, reverse=True)[:3]
                    
                    # Look for examples
                    examples = []
                    for sentence in sentences:
                        if any(term in sentence.lower() for term in ["example", "instance", "e.g.", "such as"]):
                            examples.append(sentence)
                    
                    if not examples:
                        examples = ["Example: " + (sentences[-1] if len(sentences) > 1 else "No specific example available.")]
                    
                    # Look for diagram references
                    diagrams = []
                    for sentence in sentences:
                        if any(term in sentence.lower() for term in ["diagram", "figure", "visual", "image", "picture", "illustration", "graph", "chart"]):
                            diagrams.append(sentence)
                    
                    # Add the section
                    sections.append({
                        "topic": title,
                        "definition": definition,
                        "key_points": key_sentences,
                        "content": para,
                        "examples": examples,
                        "diagrams": diagrams
                    })
        
        return {"success": True, "notes": sections}
        
    except Exception as e:
        logger.exception(f"Error generating detailed notes: {str(e)}")
        return {"success": False, "error": f"Error generating detailed notes: {str(e)}"}

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