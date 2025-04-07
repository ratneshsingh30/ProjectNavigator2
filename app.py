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

def reset_app():
    """Reset the app to its initial state"""
    st.session_state.processing_complete = False
    st.session_state.results = None
    st.session_state.processing = False
    st.session_state.error = None
    st.session_state.show_answers = {}
    st.rerun()

# Header section
st.title("🎓 AI Study Assistant")
st.write("Turn any lecture or topic into a complete learning kit in minutes.")

# Main content
if not st.session_state.processing_complete:
    # Input options
    st.subheader("Choose Your Input Method")
    
    tab1, tab2, tab3 = st.tabs(["✏️ Enter Topic", "🔗 YouTube URL", "🔊 Upload Audio"])
    
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

else:
    # Display results
    results = st.session_state.results
    
    # Add a reset button at the top
    if st.button("Start Over", key="reset_top"):
        reset_app()
    
    # Section 1: Key Concepts Summary
    st.header("🧠 Key Concepts Summary")
    if results["summary"]:
        st.markdown(results["summary"])
    else:
        st.info("No summary available.")
    
    # Section 2: Suggested Resources
    st.header("📚 Suggested Resources")
    if results["resources"]:
        resources = results["resources"].get("resources", [])
        for resource in resources:
            with st.expander(f"{resource['title']} ({resource['type']})"):
                st.write(resource['description'])
                st.markdown(f"[Link to resource]({resource['url']})")
    else:
        st.info("No resources available.")
    
    # Section 3: Study Guide & Flashcards
    st.header("📝 Study Guide & Flashcards")
    if results["study_guide"]:
        study_guide = results["study_guide"].get("study_guide", {})
        
        # Key Terms
        if "key_terms" in study_guide:
            st.subheader("Key Terms")
            terms_df = []
            for term_entry in study_guide["key_terms"]:
                with st.expander(f"{term_entry['term']}"):
                    st.write(term_entry['definition'])
        
        # Important Concepts
        if "important_concepts" in study_guide:
            st.subheader("Important Concepts")
            for i, concept in enumerate(study_guide["important_concepts"]):
                st.markdown(f"**{i+1}.** {concept}")
        
        # Flashcards
        if "flashcards" in study_guide:
            st.subheader("Flashcards")
            for i, card in enumerate(study_guide["flashcards"]):
                # Initialize show_answers state for this card if not present
                if i not in st.session_state.show_answers:
                    st.session_state.show_answers[i] = False
                
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
    else:
        st.info("No study guide available.")
    
    # Section 4: Practice Quiz
    st.header("❓ Practice Quiz")
    if results["quiz"]:
        quiz = results["quiz"].get("quiz", [])
        
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
                for i, question in enumerate(quiz):
                    st.markdown(f"**Question {i+1}:** {question['question']}")
                    options = question["options"]
                    st.session_state.quiz_answers[i] = st.radio(
                        f"Select your answer for question {i+1}:",
                        options.keys(),
                        format_func=lambda x: f"{x}: {options[x]}",
                        key=f"q_{i}",
                        index=None  # No default selection
                    )
                    st.write("---")
                
                submit_quiz = st.form_submit_button("Submit Quiz")
                
                if submit_quiz:
                    # Calculate score
                    correct_count = 0
                    for i, question in enumerate(quiz):
                        if st.session_state.quiz_answers.get(i) == question["correct_answer"]:
                            correct_count += 1
                    
                    st.session_state.quiz_score = correct_count
                    st.session_state.quiz_submitted = True
                    st.rerun()
        
        # Show quiz results
        else:
            st.subheader(f"Your Score: {st.session_state.quiz_score}/{len(quiz)}")
            
            for i, question in enumerate(quiz):
                user_answer = st.session_state.quiz_answers.get(i)
                correct_answer = question["correct_answer"]
                
                st.markdown(f"**Question {i+1}:** {question['question']}")
                options = question["options"]
                
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
        st.info("No quiz available.")
    
    # Add another reset button at the bottom
    if st.button("Start Over", key="reset_bottom"):
        reset_app()

# Footer
st.markdown("---")
st.markdown("🎓 **AI Study Assistant** | Made with ❤️ using Streamlit and AI APIs")
