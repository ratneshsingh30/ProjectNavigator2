import streamlit as st
import re
import os
from utils.content_processor import process_input
import json

# Set page title and configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Set up logging for debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import personalized insights module
from utils.personal_insight import process_profile_data

# Check if OpenAI API key is available and provide info about alternatives
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    st.warning("⚠️ OpenAI API key not found. Using free AI APIs as fallback for generating study materials.")
    logger.warning("OpenAI API key not found. Will use free AI APIs.")
else:
    logger.info("OpenAI API key found. Will try OpenAI first, with free AI APIs as fallback.")

# Function to check if URL is a valid YouTube URL
def is_youtube_url(url):
    youtube_regex = r'^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$'
    return bool(re.match(youtube_regex, url))

# Initialize session state
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'error' not in st.session_state:
    st.session_state.error = None
if 'show_answers' not in st.session_state:
    st.session_state.show_answers = {}
if 'personal_insights' not in st.session_state:
    st.session_state.personal_insights = None

def reset_app():
    """Reset the app to its initial state"""
    st.session_state.processing_complete = False
    st.session_state.results = None
    st.session_state.processing = False
    st.session_state.error = None
    st.session_state.show_answers = {}
    st.session_state.personal_insights = None
    st.rerun()

# Header section
st.title("🎓 AI Study Assistant")
st.write("Turn any lecture or topic into a complete learning kit in minutes.")

# Main content
if not st.session_state.processing_complete:
    # Input options
    st.subheader("Choose Your Input Method")
    
    tab1, tab2, tab3, tab4 = st.tabs(["✏️ Enter Topic", "🔗 YouTube URL", "🔊 Upload Audio", "📄 Upload Files"])
    
    with tab1:
        text_input = st.text_area("Enter a topic or paste lecture text:", height=150, 
                                  placeholder="E.g., Photosynthesis process in plants...")
        text_submit = st.button("Generate Study Kit", key="text_submit")
        
        if text_submit and text_input.strip():
            st.session_state.processing = True
            with st.spinner("Processing your text..."):
                results = process_input("text", text_input)
                if results["success"]:
                    st.session_state.results = results
                    st.session_state.processing_complete = True
                    st.rerun()
                else:
                    st.session_state.error = results["error"]
                    st.error(f"Error: {results['error']}")
        elif text_submit:
            st.warning("Please enter some text first.")
    
    with tab2:
        youtube_url = st.text_input("Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")
        youtube_submit = st.button("Generate Study Kit", key="youtube_submit")
        
        if youtube_submit and youtube_url.strip():
            if is_youtube_url(youtube_url):
                st.session_state.processing = True
                with st.spinner("Processing YouTube video..."):
                    results = process_input("youtube", youtube_url)
                    if results["success"]:
                        st.session_state.results = results
                        st.session_state.processing_complete = True
                        st.rerun()
                    else:
                        st.session_state.error = results["error"]
                        st.error(f"Error: {results['error']}")
            else:
                st.warning("Please enter a valid YouTube URL.")
        elif youtube_submit:
            st.warning("Please enter a YouTube URL first.")
    
    with tab3:
        uploaded_file = st.file_uploader("Upload audio file (MP3):", type=["mp3"])
        audio_submit = st.button("Generate Study Kit", key="audio_submit")
        
        if audio_submit and uploaded_file is not None:
            st.session_state.processing = True
            with st.spinner("Transcribing and processing audio..."):
                results = process_input("audio", uploaded_file)
                if results["success"]:
                    st.session_state.results = results
                    st.session_state.processing_complete = True
                    st.rerun()
                else:
                    st.session_state.error = results["error"]
                    st.error(f"Error: {results['error']}")
        elif audio_submit:
            st.warning("Please upload an audio file first.")
            
    with tab4:
        st.write("Upload lecture notes, course materials, or multiple files for processing:")
        
        file_type_options = [
            "Document (.pdf, .docx, .pptx)",
            "Video (.mp4, .mov)",
            "Code (.py, .ipynb)",
            "Multiple Files (.zip)"
        ]
        
        file_type_choice = st.radio("Select file type:", file_type_options)
        
        # Set the file types based on the user's selection
        if "Document" in file_type_choice:
            allowed_types = ["pdf", "docx", "pptx"]
            upload_label = "Upload document files:"
        elif "Video" in file_type_choice:
            allowed_types = ["mp4", "mov", "avi", "mkv"]
            upload_label = "Upload video file (will extract audio):"
        elif "Code" in file_type_choice:
            allowed_types = ["py", "ipynb", "txt"]
            upload_label = "Upload code or text files:"
        elif "Multiple" in file_type_choice:
            allowed_types = ["zip"]
            upload_label = "Upload ZIP archive (containing multiple files):"
        
        uploaded_file = st.file_uploader(upload_label, type=allowed_types)
        
        file_submit = st.button("Generate Study Kit", key="file_submit")
        
        if file_submit and uploaded_file is not None:
            st.session_state.processing = True
            
            # Determine file extension
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            with st.spinner(f"Processing {file_extension.upper()} file..."):
                # Process file with appropriate message
                if file_extension == "zip":
                    status_message = "Extracting and processing files from ZIP archive..."
                elif file_extension in ["mp4", "mov", "avi", "mkv"]:
                    status_message = "Extracting audio from video and transcribing..."
                elif file_extension in ["docx", "pptx", "pdf"]:
                    status_message = f"Extracting text from {file_extension.upper()} document..."
                else:
                    status_message = f"Processing {file_extension.upper()} file..."
                
                st.info(status_message)
                results = process_input("file", uploaded_file)
                
                if results["success"]:
                    st.session_state.results = results
                    st.session_state.processing_complete = True
                    st.rerun()
                else:
                    st.session_state.error = results["error"]
                    st.error(f"Error: {results['error']}")
        elif file_submit:
            st.warning("Please upload a file first.")

else:
    # Display results
    results = st.session_state.results
    
    # Add a reset button at the top
    if st.button("Start Over", key="reset_top"):
        reset_app()
    
    # Section 1: Key Concepts Summary
    st.header("🧠 Key Concepts Summary")
    try:
        if results and "summary" in results and results["summary"]:
            st.markdown(results["summary"])
        else:
            st.info("No summary available.")
    except Exception as e:
        st.error(f"Error displaying summary: {str(e)}")
        st.info("No summary available.")
    
    # Section 2: Suggested Resources
    st.header("📚 Suggested Resources")
    try:
        if results and "resources" in results and results["resources"]:
            resources = results["resources"].get("resources", []) if isinstance(results["resources"], dict) else []
            
            if resources and isinstance(resources, list) and len(resources) > 0:
                for resource in resources:
                    if isinstance(resource, dict) and "title" in resource and "type" in resource:
                        with st.expander(f"{resource['title']} ({resource['type']})"):
                            if "description" in resource:
                                st.write(resource['description'])
                            if "url" in resource:
                                st.markdown(f"[Link to resource]({resource['url']})")
            else:
                st.info("No resources details available.")
        else:
            st.info("No resources available.")
    except Exception as e:
        st.error(f"Error displaying resources: {str(e)}")
        st.info("No resources available.")
    
    # Section 3: Study Guide & Flashcards
    st.header("📝 Study Guide & Flashcards")
    
    # Handle the case where results["study_guide"] might be None or not a dictionary
    try:
        if results and "study_guide" in results and results["study_guide"]:
            # Try to get the study guide data safely
            study_guide = results["study_guide"].get("study_guide", {}) if isinstance(results["study_guide"], dict) else {}
            
            # Key Terms
            if study_guide and "key_terms" in study_guide and study_guide["key_terms"]:
                st.subheader("Key Terms")
                for term_entry in study_guide["key_terms"]:
                    if isinstance(term_entry, dict) and "term" in term_entry and "definition" in term_entry:
                        with st.expander(f"{term_entry['term']}"):
                            st.write(term_entry['definition'])
            
            # Important Concepts
            if study_guide and "important_concepts" in study_guide and study_guide["important_concepts"]:
                st.subheader("Important Concepts")
                for i, concept in enumerate(study_guide["important_concepts"]):
                    st.markdown(f"**{i+1}.** {concept}")
            
            # Flashcards
            if study_guide and "flashcards" in study_guide and study_guide["flashcards"]:
                st.subheader("Flashcards")
                for i, card in enumerate(study_guide["flashcards"]):
                    # Initialize show_answers state for this card if not present
                    if i not in st.session_state.show_answers:
                        st.session_state.show_answers[i] = False
                    
                    if isinstance(card, dict) and "question" in card and "answer" in card:
                        question = card["question"]
                        answer = card["answer"]
                        
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.info(f"**Q:** {question}")
                            
                            if st.session_state.show_answers[i]:
                                st.success(f"**A:** {answer}")
                        
                        with col2:
                            if st.button("Reveal" if not st.session_state.show_answers[i] else "Hide", key=f"fc_{i}"):
                                st.session_state.show_answers[i] = not st.session_state.show_answers[i]
                                st.rerun()
            
            if (not study_guide or 
                "key_terms" not in study_guide or 
                "important_concepts" not in study_guide or 
                "flashcards" not in study_guide):
                st.info("Some study guide components could not be generated.")
        else:
            st.info("No study guide available.")
    except Exception as e:
        st.error(f"Error displaying study guide: {str(e)}")
        st.info("No study guide available.")
    
    # Section 4: Practice Quiz
    st.header("❓ Practice Quiz")
    
    # Handle the case where results["quiz"] might be None or not a dictionary
    try:
        if results and "quiz" in results and results["quiz"]:
            # Try to get the quiz data safely
            quiz = results["quiz"].get("quiz", []) if isinstance(results["quiz"], dict) else []
            
            # Verify we have quiz questions
            if quiz and isinstance(quiz, list) and len(quiz) > 0:
                # Initialize session state for quiz scores if not present
                if 'quiz_submitted' not in st.session_state:
                    st.session_state.quiz_submitted = False
                if 'quiz_answers' not in st.session_state:
                    st.session_state.quiz_answers = {}
                if 'quiz_score' not in st.session_state:
                    st.session_state.quiz_score = 0
                
                # Show quiz questions
                if not st.session_state.quiz_submitted:
                    with st.form(key="quiz_form"):
                        valid_questions = 0
                        
                        for i, question in enumerate(quiz):
                            # Verify question has required fields
                            if not isinstance(question, dict) or "question" not in question or "options" not in question:
                                continue
                                
                            # Verify options is a dictionary
                            options = question.get("options", {})
                            if not isinstance(options, dict) or len(options) < 2:
                                continue
                                
                            valid_questions += 1
                            st.markdown(f"**Question {valid_questions}:** {question['question']}")
                            
                            st.session_state.quiz_answers[i] = st.radio(
                                f"Select your answer for question {valid_questions}:",
                                options.keys(),
                                format_func=lambda x: f"{x}: {options[x]}",
                                key=f"q_{i}",
                                index=None  # No default selection
                            )
                            st.write("---")
                        
                        # Only show submit if we have valid questions
                        if valid_questions > 0:
                            submit_quiz = st.form_submit_button("Submit Quiz")
                            
                            if submit_quiz:
                                # Calculate score
                                correct_count = 0
                                for i, question in enumerate(quiz):
                                    if (isinstance(question, dict) and 
                                        "correct_answer" in question and 
                                        st.session_state.quiz_answers.get(i) == question["correct_answer"]):
                                        correct_count += 1
                                
                                st.session_state.quiz_score = correct_count
                                st.session_state.quiz_submitted = True
                                st.rerun()
                        else:
                            st.info("No valid quiz questions available.")
                
                # Show quiz results
                else:
                    valid_questions = sum(1 for q in quiz if isinstance(q, dict) and "question" in q and "options" in q)
                    st.subheader(f"Your Score: {st.session_state.quiz_score}/{valid_questions}")
                    
                    for i, question in enumerate(quiz):
                        # Skip invalid questions
                        if not isinstance(question, dict) or "question" not in question or "options" not in question:
                            continue
                            
                        user_answer = st.session_state.quiz_answers.get(i)
                        correct_answer = question.get("correct_answer", "")
                        
                        st.markdown(f"**Question {i+1}:** {question['question']}")
                        options = question.get("options", {})
                        
                        for opt, text in options.items():
                            if opt == correct_answer:
                                st.success(f"✓ {opt}: {text} (Correct Answer)")
                            elif opt == user_answer:
                                st.error(f"✗ {opt}: {text} (Your Answer)")
                            else:
                                st.write(f"{opt}: {text}")
                        
                        st.info(f"**Explanation:** {question.get('explanation', 'No explanation provided.')}")
                        st.write("---")
                    
                    if st.button("Retake Quiz"):
                        st.session_state.quiz_submitted = False
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_score = 0
                        st.rerun()
            else:
                st.info("No quiz questions available.")
        else:
            st.info("No quiz available.")
    except Exception as e:
        st.error(f"Error displaying quiz: {str(e)}")
        st.info("No quiz available.")
    
    # Section 5: Detailed Notes with Examples
    st.header("📔 Detailed Topic Notes")
    
    try:
        if results and "detailed_notes" in results and results["detailed_notes"]:
            # Try to get the detailed notes data safely
            notes_data = results["detailed_notes"].get("notes", []) if isinstance(results["detailed_notes"], dict) else []
            
            # Verify we have notes sections
            if notes_data and isinstance(notes_data, list) and len(notes_data) > 0:
                for section in notes_data:
                    if isinstance(section, dict) and "title" in section:
                        with st.expander(f"📌 {section['title']}", expanded=True):
                            # Display key points in bold
                            if "key_points" in section and section["key_points"]:
                                st.subheader("Key Points:")
                                for point in section["key_points"]:
                                    st.markdown(f"**{point}**")
                                st.write("---")
                            
                            # Display content
                            if "content" in section and section["content"]:
                                st.write(section["content"])
                            
                            # Display example
                            if "example" in section and section["example"]:
                                st.subheader("Example:")
                                st.info(section["example"])
            else:
                st.info("No detailed notes available.")
        else:
            st.info("No detailed notes available.")
    except Exception as e:
        st.error(f"Error displaying detailed notes: {str(e)}")
        st.info("No detailed notes available.")
    
    # Section 6: Personalized Insights
    st.header("👤 Personalized Insights (Optional)")
    
    # Check if we already have generated insights
    if st.session_state.personal_insights:
        try:
            if isinstance(st.session_state.personal_insights, dict):
                # Try to safely access the insights
                if "insights" in st.session_state.personal_insights and st.session_state.personal_insights["insights"]:
                    insights = st.session_state.personal_insights["insights"]
                    
                    st.write("Here are personalized insights based on your professional profile:")
                    
                    # Check that all sections exist
                    if isinstance(insights, dict):
                        with st.expander("🔄 Relevance to Your Background", expanded=True):
                            st.write(insights.get("relevance", "No relevance information available."))
                        
                        with st.expander("🎯 Alignment with Your Skills"):
                            st.write(insights.get("alignment", "No alignment information available."))
                            
                        with st.expander("📈 Areas for Growth"):
                            st.write(insights.get("growth_areas", "No growth areas information available."))
                            
                        with st.expander("💡 Practical Applications"):
                            st.write(insights.get("applications", "No applications information available."))
                            
                        with st.expander("🛤️ Personalized Learning Path"):
                            st.write(insights.get("learning_path", "No learning path information available."))
                    else:
                        st.error("Invalid format for insights data.")
                else:
                    st.error("No insights data found in the generated results.")
                    
            if st.button("Reset Personalized Insights", key="reset_insights"):
                st.session_state.personal_insights = None
                st.rerun()
                
        except Exception as e:
            st.error(f"Error displaying personal insights: {str(e)}")
            if st.button("Reset Personalized Insights", key="reset_error"):
                st.session_state.personal_insights = None
                st.rerun()
    else:
        # Show form to upload profile data
        st.write("Upload your resume and/or LinkedIn profile to receive personalized insights about how this topic relates to your background and career path.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            resume_file = st.file_uploader("Upload your resume (PDF/DOCX):", type=["pdf", "docx"], key="resume_upload")
        
        with col2:
            linkedin_file = st.file_uploader("Upload your LinkedIn profile (PDF/DOCX/TXT):", type=["pdf", "docx", "txt"], key="linkedin_upload")
        
        if st.button("Generate Personalized Insights", key="generate_insights"):
            if resume_file is None and linkedin_file is None:
                st.warning("Please upload at least one file (resume or LinkedIn profile).")
            else:
                with st.spinner("Analyzing your profile and generating personalized insights..."):
                    # Get the study content from the results, with safe access
                    study_content = ""
                    if results and "transcript" in results and results["transcript"]:
                        study_content = results["transcript"]
                    
                    # Generate personalized insights
                    insights_result = process_profile_data(resume_file, linkedin_file, study_content)
                    
                    if insights_result["success"]:
                        st.session_state.personal_insights = insights_result
                        st.success("Personalized insights generated!")
                        st.rerun()
                    else:
                        st.error(f"Error generating personalized insights: {insights_result['error']}")
    
    # Add another reset button at the bottom
    if st.button("Start Over", key="reset_bottom"):
        reset_app()

# Footer
st.markdown("---")
st.markdown("🎓 **AI Study Assistant** | Made with ❤️ using Streamlit and AI APIs")
