import streamlit as st
import requests
import base64
from io import BytesIO
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Voice Conversation",
    page_icon="🎙️",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextArea textarea {
        font-size: 16px;
    }
    .success-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #0a0924;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        margin: 1rem 0;
    }
    h1 {
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        color: #7f8c8d;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .conversation-history {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background: #007bff;
        color: white;
        padding: 0.8rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
    }
    .ai-message {
        background: #28a745;
        color: white;
        padding: 0.8rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🎙️ AI Voice Conversation")
st.markdown('<p class="subtitle">Talk with AI using your microphone!</p>', unsafe_allow_html=True)

# API endpoint (BASE API)
API_URL = "http://localhost:8000/ask"

# Language mapping which supports multiple languages
LANGUAGES = {
    "English": "en",
    "Bengali": "bn",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh"
}

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'interview_mode' not in st.session_state:
    st.session_state.interview_mode = False
if 'interview_context' not in st.session_state:
    st.session_state.interview_context = ""


# this function will convert out input audio to text using speech recognition - it return text 
def transcribe_audio(audio_bytes):
    """Convert audio bytes to text using speech recognition"""
    try:
        recognizer = sr.Recognizer()
        
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        # it Loads our audio file
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
            
        # Recognize speech using Google Speech Recognition
        text = recognizer.recognize_google(audio_data)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return text
    
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results from speech recognition service: {e}")
        return None
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None
    finally:
        # Ensure our temp file is deleted properly
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass


## 
def send_question_to_api(question, speed, language_code, context=""):
    """Send question to API and get response"""
    try:
        # Add context if in interview mode
        full_question = question
        if context:
            full_question = f"{context}\n\nUser: {question}"
        
        response = requests.post(
            API_URL,
            data={
                "question": full_question,
                "speed": speed,
                "language": language_code
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

# Create tabs for different modes
tab1, tab2 = st.tabs(["💬 Normal Conversation", "🎯 Interview Mode"])

with tab1:
    # Normal conversation mode
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🎤 Voice Input")
        
        # Voice recorder function
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_name="microphone",
            icon_size="3x",
        )
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if st.button("🔄 Transcribe & Send", type="primary", use_container_width=True):
                with st.spinner("🎧 Transcribing your voice..."):
                    transcribed_text = transcribe_audio(audio_bytes)
                    
                    if transcribed_text:
                        st.success(f"✅ You said: {transcribed_text}")
                        st.session_state.current_question = transcribed_text
                        st.rerun()
                    else:
                        st.error("❌ Could not understand the audio. Please try again.")
        
        st.markdown("🅰️ You Can Type Your Question")
        
        # text area container for text question input
        question = st.text_area(
            "Enter your question:",
            value=st.session_state.get('current_question', ''),
            height=150,
            placeholder="Type your question or use voice input above...",
            key="normal_question"
        )
        
        # Clear button
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.current_question = ""
            st.rerun()
        
        # Speed control system
        st.markdown("### ⚡ Audio Speed")
        speed = st.slider(
            "Playback Speed:",
            min_value=0.5,
            max_value=2.0,
            value=1.0,
            step=0.1,
            key="normal_speed"
        )
        
        # Language selector list box
        st.markdown("### 🌍 Language")
        language_name = st.selectbox(
            "Audio Language:",
            list(LANGUAGES.keys()),
            index=0,
            key="normal_language"
        )
        language_code = LANGUAGES[language_name]
        
        # Generate button this will start generating responses by ai 
        generate_btn = st.button("🚀 Generate Response", type="primary", use_container_width=True, key="normal_generate")
        
        if generate_btn and question.strip():
            with st.spinner(f"🔄 Generating response at {speed}x speed..."):
                data = send_question_to_api(question, speed, language_code)
                
                if data:
                    st.session_state.last_response = data
                    st.session_state.conversation_history.append({
                        "user": question,
                        "ai": data['ai_answer'],
                        "audio": data['audio_base64']
                    })
                    st.success("✅ Response generated!")
                    st.session_state.current_question = ""
                    st.rerun()
    
    with col2:
        st.markdown("### 📊 Latest Response")
        
        if st.session_state.last_response:
            data = st.session_state.last_response
            
            st.markdown("#### 📝 Your Question:")
            st.info(data['your_question'])
            
            st.markdown("#### 🤖 AI Answer:")
            st.markdown(f"<div class='success-box'>{data['ai_answer']}</div>", unsafe_allow_html=True)
            
            st.markdown("#### 🔊 Audio Response:")
            try:
                audio_bytes = base64.b64decode(data['audio_base64'])
                st.audio(audio_bytes, format='audio/mp3')
                
                st.download_button(
                    label="📥 Download Audio",
                    data=audio_bytes,
                    file_name=f"response_{data.get('speed', 1.0)}x.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error playing audio: {str(e)}")
        
        # Conversation history for later uses 
        if st.session_state.conversation_history:
            st.markdown("### 📜 Conversation History")
            
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.conversation_history = []
                st.rerun()
            
            st.markdown("<div class='conversation-history'>", unsafe_allow_html=True)
            for i, conv in enumerate(reversed(st.session_state.conversation_history)):
                st.markdown(f"**You:** {conv['user']}")
                st.markdown(f"**AI:** {conv['ai']}")
                
                # Play button for each conversation
                audio_bytes = base64.b64decode(conv['audio'])
                st.audio(audio_bytes, format='audio/mp3')
                st.markdown("---")
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    # Interview mode
    st.markdown("### 🎯 AI Interview Practice")
    st.markdown("Practice interviews and get feedback on your responses!")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Interview setup
        st.markdown("#### 📋 Interview Setup")
        
        # Select Your Interview Types
        interview_type = st.selectbox(
            "Interview Type:",
            ["Software Engineer", "Data Scientist", "Product Manager", "Business Analyst", 
             "UX Designer", "Marketing Manager", "General Interview"]
        )
        
        if st.button("🎬 Start Interview", type="primary", use_container_width=True):
            st.session_state.interview_mode = True
            st.session_state.interview_context = f"""You are conducting a {interview_type} interview. 
Ask relevant questions one at a time. After the candidate answers, provide constructive feedback 
on their response and ask the next question. Be professional but encouraging."""
            
            # Generate first question
            with st.spinner("Preparing interview..."):
                first_q = f"Please ask me the first {interview_type} interview question."
                data = send_question_to_api(first_q, 1.0, "en", st.session_state.interview_context)
                
                if data:
                    st.session_state.conversation_history = []
                    st.session_state.conversation_history.append({
                        "user": "Start Interview",
                        "ai": data['ai_answer'],
                        "audio": data['audio_base64']
                    })
                    st.session_state.last_response = data
                    st.rerun()
        
        if st.session_state.interview_mode:
            st.markdown("#### 🎤 Your Answer")
            
            # Voice input for interview
            interview_audio = audio_recorder(
                text="Click to answer",
                recording_color="#e74c3c",
                neutral_color="#28a745",
                icon_name="microphone",
                icon_size="3x",
                key="interview_recorder"
            )
            
            if interview_audio:
                st.audio(interview_audio, format="audio/wav")
                
                if st.button("✅ Submit Answer", type="primary", use_container_width=True, key="submit_interview"):
                    with st.spinner("🎧 Processing your answer..."):
                        answer_text = transcribe_audio(interview_audio)
                        
                        if answer_text:
                            st.success(f"✅ Your answer: {answer_text}")
                            
                            # Send answer and get feedback
                            feedback_prompt = f"My answer: {answer_text}\n\nPlease provide feedback on my answer and ask the next question."
                            data = send_question_to_api(feedback_prompt, 1.0, "en", st.session_state.interview_context)
                            
                            if data:
                                st.session_state.conversation_history.append({
                                    "user": answer_text,
                                    "ai": data['ai_answer'],
                                    "audio": data['audio_base64']
                                })
                                st.session_state.last_response = data
                                st.rerun()
            
            st.markdown("#### 🗨️ Or Type Your Answer")
            typed_answer = st.text_area(
                "Type your answer:",
                height=150,
                key="interview_answer"
            )
            
            if st.button("📤 Send Typed Answer", use_container_width=True):
                if typed_answer.strip():
                    feedback_prompt = f"My answer: {typed_answer}\n\nPlease provide feedback and ask the next question."
                    data = send_question_to_api(feedback_prompt, 1.0, "en", st.session_state.interview_context)
                    
                    if data:
                        st.session_state.conversation_history.append({
                            "user": typed_answer,
                            "ai": data['ai_answer'],
                            "audio": data['audio_base64']
                        })
                        st.session_state.last_response = data
                        st.rerun()
            
            if st.button("🛑 End Interview", use_container_width=True):
                # Get final feedback
                final_prompt = "Please provide overall feedback on my interview performance."
                data = send_question_to_api(final_prompt, 1.0, "en", st.session_state.interview_context)
                
                if data:
                    st.session_state.conversation_history.append({
                        "user": "End Interview",
                        "ai": data['ai_answer'],
                        "audio": data['audio_base64']
                    })
                    st.session_state.last_response = data
                    st.session_state.interview_mode = False
                    st.rerun()
    
    with col2:
        st.markdown("### 🎙️ Interview Progress")
        
        if st.session_state.last_response:
            data = st.session_state.last_response
            
            st.markdown("#### 🤖 Interviewer:")
            st.markdown(f"<div class='success-box'>{data['ai_answer']}</div>", unsafe_allow_html=True)
            
            try:
                audio_bytes = base64.b64decode(data['audio_base64'])
                st.audio(audio_bytes, format='audio/mp3')
            except Exception as e:
                st.error(f"Error playing audio: {str(e)}")
        
        # Interview history
        if st.session_state.conversation_history:
            st.markdown("#### 📝 Interview Transcript")
            
            for i, conv in enumerate(st.session_state.conversation_history):
                with st.expander(f"Q{i+1}: {conv['user'][:50]}..."):
                    st.markdown(f"**Your Response:** {conv['user']}")
                    st.markdown(f"**Feedback:** {conv['ai']}")
                    audio_bytes = base64.b64decode(conv['audio'])
                    st.audio(audio_bytes, format='audio/mp3')

# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Voice Features:**
    - 🎤 Record your voice
    - 🎧 Get audio responses
    - 💬 Have natural conversations
    - 🎯 Practice interviews
    
    **Technologies:**
    - Groq LLM for responses
    - Google Speech Recognition
    - gTTS for audio output
    """)
    
    st.markdown("### 📊 API Status")
    try:
        health_response = requests.get(f"{API_URL.rsplit('/', 1)[0]}/health", timeout=2)
        if health_response.status_code == 200:
            st.success("🟢 API is running")
        else:
            st.error("🔴 API error")
    except:
        st.error("🔴 API is offline")
    
    st.markdown("### 🎯 Tips")
    st.markdown("""
    **For best results:**
    - Speak clearly into your microphone
    - Minimize background noise
    - Use headphones to avoid feedback
    - Practice with interview mode
    """)

# Footer
st.markdown(
    f"""
    <div style="
        text-align: center;
        color: #7f8c8d;
        font-size: 14px;
    ">
        🎙️ Voice Base AI Interview App | Built with Fast API + Streamlit <br/>
        © {datetime.now().year} • Developed by 
        <a href="https://github.com/GaziAdib" 
           target="_blank"
           style="color: #3498db; text-decoration: none; font-weight: 600;">
           @Gazi Adib
        </a>
    </div>
    """,
    unsafe_allow_html=True
)






# import streamlit as st
# import requests
# import base64
# from io import BytesIO
# from audio_recorder_streamlit import audio_recorder
# import speech_recognition as sr
# from pydub import AudioSegment
# import tempfile
# import os

# # Page configuration
# st.set_page_config(
#     page_title="AI Voice Conversation",
#     page_icon="🎙️",
#     layout="wide"
# )

# # Custom CSS for better styling
# st.markdown("""
#     <style>
#     .main {
#         padding: 2rem;
#     }
#     .stTextArea textarea {
#         font-size: 16px;
#     }
#     .success-box {
#         padding: 1.5rem;
#         border-radius: 0.5rem;
#         background-color: #0a0924;
#         border: 1px solid #c3e6cb;
#         margin: 1rem 0;
#     }
#     .info-box {
#         padding: 1rem;
#         border-radius: 0.5rem;
#         background-color: #d1ecf1;
#         border: 1px solid #bee5eb;
#         margin: 1rem 0;
#     }
#     .warning-box {
#         padding: 1rem;
#         border-radius: 0.5rem;
#         background-color: #fff3cd;
#         border: 1px solid #ffc107;
#         margin: 1rem 0;
#     }
#     h1 {
#         color: #2c3e50;
#         margin-bottom: 0.5rem;
#     }
#     .subtitle {
#         color: #7f8c8d;
#         font-size: 1.2rem;
#         margin-bottom: 2rem;
#     }
#     .conversation-history {
#         max-height: 400px;
#         overflow-y: auto;
#         padding: 1rem;
#         background: #f8f9fa;
#         border-radius: 0.5rem;
#         margin: 1rem 0;
#     }
#     .user-message {
#         background: #007bff;
#         color: white;
#         padding: 0.8rem;
#         border-radius: 1rem;
#         margin: 0.5rem 0;
#         max-width: 80%;
#     }
#     .ai-message {
#         background: #28a745;
#         color: white;
#         padding: 0.8rem;
#         border-radius: 1rem;
#         margin: 0.5rem 0;
#         max-width: 80%;
#         margin-left: auto;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Title and description
# st.title("🎙️ AI Voice Conversation")
# st.markdown('<p class="subtitle">Talk with AI using your microphone!</p>', unsafe_allow_html=True)

# # API endpoint
# API_URL = "http://localhost:8000/ask"

# # Language mapping
# LANGUAGES = {
#     "English": "en",
#     "Bengali": "bn",
#     "Hindi": "hi",
#     "Spanish": "es",
#     "French": "fr",
#     "German": "de",
#     "Italian": "it",
#     "Japanese": "ja",
#     "Korean": "ko",
#     "Chinese": "zh"
# }

# # Initialize session state
# if 'conversation_history' not in st.session_state:
#     st.session_state.conversation_history = []
# if 'last_response' not in st.session_state:
#     st.session_state.last_response = None
# if 'interview_mode' not in st.session_state:
#     st.session_state.interview_mode = False
# if 'interview_context' not in st.session_state:
#     st.session_state.interview_context = ""

# def transcribe_audio(audio_bytes):
#     """Convert audio bytes to text using speech recognition"""
#     try:
#         recognizer = sr.Recognizer()
        
#         # Save audio bytes to temporary file
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
#             tmp_file.write(audio_bytes)
#             tmp_path = tmp_file.name
        
#         # Load audio file
#         with sr.AudioFile(tmp_path) as source:
#             audio_data = recognizer.record(source)
            
#         # Recognize speech using Google Speech Recognition
#         text = recognizer.recognize_google(audio_data)
        
#         # Clean up temp file
#         os.unlink(tmp_path)
        
#         return text
    
#     except sr.UnknownValueError:
#         return None
#     except sr.RequestError as e:
#         st.error(f"Could not request results from speech recognition service; {e}")
#         return None
#     except Exception as e:
#         st.error(f"Error transcribing audio: {str(e)}")
#         return None
#     finally:
#         # Ensure temp file is deleted
#         try:
#             if os.path.exists(tmp_path):
#                 os.unlink(tmp_path)
#         except:
#             pass

# def send_question_to_api(question, speed, language_code, context=""):
#     """Send question to API and get response"""
#     try:
#         # Add context if in interview mode
#         full_question = question
#         if context:
#             full_question = f"{context}\n\nUser: {question}"
        
#         response = requests.post(
#             API_URL,
#             data={
#                 "question": full_question,
#                 "speed": speed,
#                 "language": language_code
#             },
#             timeout=60
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             st.error(f"API Error: {response.json().get('detail', 'Unknown error')}")
#             return None
#     except Exception as e:
#         st.error(f"Connection error: {str(e)}")
#         return None

# # Create tabs for different modes
# tab1, tab2 = st.tabs(["💬 Normal Conversation", "🎯 Interview Mode"])

# with tab1:
#     # Normal conversation mode
#     col1, col2 = st.columns([1, 1])
    
#     with col1:
#         st.markdown("### 🎤 Voice Input")
        
#         # Voice recorder
#         audio_bytes = audio_recorder(
#             text="Click to record",
#             recording_color="#e74c3c",
#             neutral_color="#3498db",
#             icon_name="microphone",
#             icon_size="3x",
#         )
        
#         if audio_bytes:
#             st.audio(audio_bytes, format="audio/wav")
            
#             if st.button("🔄 Transcribe & Send", type="primary", use_container_width=True):
#                 with st.spinner("🎧 Transcribing your voice..."):
#                     transcribed_text = transcribe_audio(audio_bytes)
                    
#                     if transcribed_text:
#                         st.success(f"✅ You said: {transcribed_text}")
#                         st.session_state.current_question = transcribed_text
#                         st.rerun()
#                     else:
#                         st.error("❌ Could not understand the audio. Please try again.")
        
#         st.markdown("### 💬 Or Type Your Question")
        
#         question = st.text_area(
#             "Enter your question:",
#             value=st.session_state.get('current_question', ''),
#             height=150,
#             placeholder="Type your question or use voice input above...",
#             key="normal_question"
#         )
        
#         # Clear button
#         if st.button("🗑️ Clear", use_container_width=True):
#             st.session_state.current_question = ""
#             st.rerun()
        
#         # Speed control
#         st.markdown("### ⚡ Audio Speed")
#         speed = st.slider(
#             "Playback Speed:",
#             min_value=0.5,
#             max_value=2.0,
#             value=1.0,
#             step=0.1,
#             key="normal_speed"
#         )
        
#         # Language selector
#         st.markdown("### 🌍 Language")
#         language_name = st.selectbox(
#             "Audio Language:",
#             list(LANGUAGES.keys()),
#             index=0,
#             key="normal_language"
#         )
#         language_code = LANGUAGES[language_name]
        
#         # Generate button
#         generate_btn = st.button("🚀 Generate Response", type="primary", use_container_width=True, key="normal_generate")
        
#         if generate_btn and question.strip():
#             with st.spinner(f"🔄 Generating response at {speed}x speed..."):
#                 data = send_question_to_api(question, speed, language_code)
                
#                 if data:
#                     st.session_state.last_response = data
#                     st.session_state.conversation_history.append({
#                         "user": question,
#                         "ai": data['ai_answer'],
#                         "audio": data['audio_base64']
#                     })
#                     st.success("✅ Response generated!")
#                     st.session_state.current_question = ""
#                     st.rerun()
    
#     with col2:
#         st.markdown("### 📊 Latest Response")
        
#         if st.session_state.last_response:
#             data = st.session_state.last_response
            
#             st.markdown("#### 📝 Your Question:")
#             st.info(data['your_question'])
            
#             st.markdown("#### 🤖 AI Answer:")
#             st.markdown(f"<div class='success-box'>{data['ai_answer']}</div>", unsafe_allow_html=True)
            
#             st.markdown("#### 🔊 Audio Response:")
#             try:
#                 audio_bytes = base64.b64decode(data['audio_base64'])
#                 st.audio(audio_bytes, format='audio/mp3')
                
#                 st.download_button(
#                     label="📥 Download Audio",
#                     data=audio_bytes,
#                     file_name=f"response_{data.get('speed', 1.0)}x.mp3",
#                     mime="audio/mp3",
#                     use_container_width=True
#                 )
#             except Exception as e:
#                 st.error(f"Error playing audio: {str(e)}")
        
#         # Conversation history
#         if st.session_state.conversation_history:
#             st.markdown("### 📜 Conversation History")
            
#             if st.button("🗑️ Clear History", use_container_width=True):
#                 st.session_state.conversation_history = []
#                 st.rerun()
            
#             st.markdown("<div class='conversation-history'>", unsafe_allow_html=True)
#             for i, conv in enumerate(reversed(st.session_state.conversation_history)):
#                 st.markdown(f"**You:** {conv['user']}")
#                 st.markdown(f"**AI:** {conv['ai']}")
                
#                 # Play button for each conversation
#                 audio_bytes = base64.b64decode(conv['audio'])
#                 st.audio(audio_bytes, format='audio/mp3')
#                 st.markdown("---")
#             st.markdown("</div>", unsafe_allow_html=True)

# with tab2:
#     # Interview mode
#     st.markdown("### 🎯 AI Interview Practice")
#     st.markdown("Practice interviews and get feedback on your responses!")
    
#     col1, col2 = st.columns([1, 1])
    
#     with col1:
#         # Interview setup
#         st.markdown("#### 📋 Interview Setup")
        
#         interview_type = st.selectbox(
#             "Interview Type:",
#             ["Software Engineer", "Data Scientist", "Product Manager", "Business Analyst", 
#              "UX Designer", "Marketing Manager", "General Interview"]
#         )
        
#         if st.button("🎬 Start Interview", type="primary", use_container_width=True):
#             st.session_state.interview_mode = True
#             st.session_state.interview_context = f"""You are conducting a {interview_type} interview. 
# Ask relevant questions one at a time. After the candidate answers, provide constructive feedback 
# on their response and ask the next question. Be professional but encouraging."""
            
#             # Generate first question
#             with st.spinner("Preparing interview..."):
#                 first_q = f"Please ask me the first {interview_type} interview question."
#                 data = send_question_to_api(first_q, 1.0, "en", st.session_state.interview_context)
                
#                 if data:
#                     st.session_state.conversation_history = []
#                     st.session_state.conversation_history.append({
#                         "user": "Start Interview",
#                         "ai": data['ai_answer'],
#                         "audio": data['audio_base64']
#                     })
#                     st.session_state.last_response = data
#                     st.rerun()
        
#         if st.session_state.interview_mode:
#             st.markdown("#### 🎤 Your Answer")
            
#             # Voice input for interview
#             interview_audio = audio_recorder(
#                 text="Click to answer",
#                 recording_color="#e74c3c",
#                 neutral_color="#28a745",
#                 icon_name="microphone",
#                 icon_size="3x",
#                 key="interview_recorder"
#             )
            
#             if interview_audio:
#                 st.audio(interview_audio, format="audio/wav")
                
#                 if st.button("✅ Submit Answer", type="primary", use_container_width=True, key="submit_interview"):
#                     with st.spinner("🎧 Processing your answer..."):
#                         answer_text = transcribe_audio(interview_audio)
                        
#                         if answer_text:
#                             st.success(f"✅ Your answer: {answer_text}")
                            
#                             # Send answer and get feedback
#                             feedback_prompt = f"My answer: {answer_text}\n\nPlease provide feedback on my answer and ask the next question."
#                             data = send_question_to_api(feedback_prompt, 1.0, "en", st.session_state.interview_context)
                            
#                             if data:
#                                 st.session_state.conversation_history.append({
#                                     "user": answer_text,
#                                     "ai": data['ai_answer'],
#                                     "audio": data['audio_base64']
#                                 })
#                                 st.session_state.last_response = data
#                                 st.rerun()
            
#             st.markdown("#### 💬 Or Type Your Answer")
#             typed_answer = st.text_area(
#                 "Type your answer:",
#                 height=150,
#                 key="interview_answer"
#             )
            
#             if st.button("📤 Send Typed Answer", use_container_width=True):
#                 if typed_answer.strip():
#                     feedback_prompt = f"My answer: {typed_answer}\n\nPlease provide feedback and ask the next question."
#                     data = send_question_to_api(feedback_prompt, 1.0, "en", st.session_state.interview_context)
                    
#                     if data:
#                         st.session_state.conversation_history.append({
#                             "user": typed_answer,
#                             "ai": data['ai_answer'],
#                             "audio": data['audio_base64']
#                         })
#                         st.session_state.last_response = data
#                         st.rerun()
            
#             if st.button("🛑 End Interview", use_container_width=True):
#                 # Get final feedback
#                 final_prompt = "Please provide overall feedback on my interview performance."
#                 data = send_question_to_api(final_prompt, 1.0, "en", st.session_state.interview_context)
                
#                 if data:
#                     st.session_state.conversation_history.append({
#                         "user": "End Interview",
#                         "ai": data['ai_answer'],
#                         "audio": data['audio_base64']
#                     })
#                     st.session_state.last_response = data
#                     st.session_state.interview_mode = False
#                     st.rerun()
    
#     with col2:
#         st.markdown("### 🎙️ Interview Progress")
        
#         if st.session_state.last_response:
#             data = st.session_state.last_response
            
#             st.markdown("#### 🤖 Interviewer:")
#             st.markdown(f"<div class='success-box'>{data['ai_answer']}</div>", unsafe_allow_html=True)
            
#             try:
#                 audio_bytes = base64.b64decode(data['audio_base64'])
#                 st.audio(audio_bytes, format='audio/mp3')
#             except Exception as e:
#                 st.error(f"Error playing audio: {str(e)}")
        
#         # Interview history
#         if st.session_state.conversation_history:
#             st.markdown("#### 📝 Interview Transcript")
            
#             for i, conv in enumerate(st.session_state.conversation_history):
#                 with st.expander(f"Q{i+1}: {conv['user'][:50]}..."):
#                     st.markdown(f"**Your Response:** {conv['user']}")
#                     st.markdown(f"**Feedback:** {conv['ai']}")
#                     audio_bytes = base64.b64decode(conv['audio'])
#                     st.audio(audio_bytes, format='audio/mp3')

# # Sidebar
# with st.sidebar:
#     st.markdown("### ℹ️ About")
#     st.markdown("""
#     **Voice Features:**
#     - 🎤 Record your voice
#     - 🎧 Get audio responses
#     - 💬 Have natural conversations
#     - 🎯 Practice interviews
    
#     **Technologies:**
#     - Groq LLM for responses
#     - Google Speech Recognition
#     - gTTS for audio output
#     """)
    
#     st.markdown("### 📊 API Status")
#     try:
#         health_response = requests.get(f"{API_URL.rsplit('/', 1)[0]}/health", timeout=2)
#         if health_response.status_code == 200:
#             st.success("🟢 API is running")
#         else:
#             st.error("🔴 API error")
#     except:
#         st.error("🔴 API is offline")
    
#     st.markdown("### 🎯 Tips")
#     st.markdown("""
#     **For best results:**
#     - Speak clearly into your microphone
#     - Minimize background noise
#     - Use headphones to avoid feedback
#     - Practice with interview mode
#     """)

# # Footer
# st.markdown("---")
# st.markdown(
#     "<div style='text-align: center; color: #7f8c8d;'>"
#     "🎙️ Voice-Enabled AI Conversation | Built with ❤️"
#     "</div>",
#     unsafe_allow_html=True
# )





















# import streamlit as st
# import requests
# import base64
# from io import BytesIO

# # Page configuration
# st.set_page_config(
#     page_title="AI Text-to-Speech",
#     page_icon="🎙️",
#     layout="wide"
# )

# # Custom CSS for better styling
# st.markdown("""
#     <style>
#     .main {
#         padding: 2rem;
#     }
#     .stTextArea textarea {
#         font-size: 16px;
#     }
#     .success-box {
#         padding: 1.5rem;
#         border-radius: 0.5rem;
#         background-color: #d4edda;
#         border: 1px solid #c3e6cb;
#         margin: 1rem 0;
#     }
#     .info-box {
#         padding: 1rem;
#         border-radius: 0.5rem;
#         background-color: #d1ecf1;
#         border: 1px solid #bee5eb;
#         margin: 1rem 0;
#     }
#     h1 {
#         color: #2c3e50;
#         margin-bottom: 0.5rem;
#     }
#     .subtitle {
#         color: #7f8c8d;
#         font-size: 1.2rem;
#         margin-bottom: 2rem;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Title and description
# st.title("🎙️ AI Text-to-Speech Generator")
# st.markdown('<p class="subtitle">Ask a question and hear the AI response with customizable speed!</p>', unsafe_allow_html=True)

# # API endpoint
# API_URL = "http://localhost:8000/ask"

# # Language mapping
# LANGUAGES = {
#     "English": "en",
#     "Bengali": "bn",
#     "Hindi": "hi",
#     "Spanish": "es",
#     "French": "fr",
#     "German": "de",
#     "Italian": "it",
#     "Japanese": "ja",
#     "Korean": "ko",
#     "Chinese": "zh"
# }

# # Create two columns for layout
# col1, col2 = st.columns([1, 1])

# with col1:
#     st.markdown("### 💬 Ask Your Question")
    
#     # Text input
#     question = st.text_area(
#         "Enter your question:",
#         height=150,
#         placeholder="Type your question here... (e.g., 'What is artificial intelligence?')",
#         help="Ask any question and the AI will respond with both text and audio"
#     )
    
#     # Speed control slider
#     st.markdown("### ⚡ Audio Speed Control")
#     speed = st.slider(
#         "Playback Speed:",
#         min_value=0.5,
#         max_value=2.0,
#         value=1.0,
#         step=0.1,
#         help="Adjust how fast the audio plays (0.5x = slower, 2.0x = faster)"
#     )
    
#     # Show speed description
#     speed_descriptions = {
#         0.5: "🐢 Very Slow (0.5x)",
#         0.7: "🐌 Slow (0.7x)",
#         0.9: "🚶 Slightly Slow (0.9x)",
#         1.0: "▶️ Normal Speed (1.0x)",
#         1.2: "🏃 Slightly Fast (1.2x)",
#         1.5: "🏃‍♂️ Fast (1.5x)",
#         2.0: "🚀 Very Fast (2.0x)"
#     }
    
#     # Find closest description
#     closest_speed = min(speed_descriptions.keys(), key=lambda x: abs(x - speed))
#     if abs(closest_speed - speed) < 0.15:
#         st.info(f"Selected: {speed_descriptions[closest_speed]}")
#     else:
#         st.info(f"Selected: {speed}x speed")
    
#     # Language selector
#     st.markdown("### 🌍 Language")
#     language_name = st.selectbox(
#         "Audio Language:",
#         list(LANGUAGES.keys()),
#         index=0,
#         help="Select the language for text-to-speech output"
#     )
#     language_code = LANGUAGES[language_name]
    
#     # Generate button
#     generate_btn = st.button("🚀 Generate Response", type="primary", use_container_width=True)
    
#     # Add some example questions
#     st.markdown("##### 💡 Example Questions:")
#     example_questions = [
#         "What is the capital of France?",
#         "Explain quantum computing in simple terms",
#         "Tell me a short joke",
#         "What is the meaning of life?"
#     ]
    
#     cols = st.columns(2)
#     for i, example in enumerate(example_questions):
#         with cols[i % 2]:
#             if st.button(f"📌 {example[:25]}...", key=f"example_{i}", use_container_width=True):
#                 question = example
#                 st.rerun()

# with col2:
#     st.markdown("### 📊 Response")
    
#     # Placeholder for results
#     result_container = st.container()

# # Initialize session state for storing results
# if 'last_response' not in st.session_state:
#     st.session_state.last_response = None

# # Process the request
# if generate_btn and question.strip():
#     with st.spinner(f"🔄 Generating response at {speed}x speed... Please wait..."):
#         try:
#             # Make API request with speed and language parameters
#             response = requests.post(
#                 API_URL,
#                 data={
#                     "question": question,
#                     "speed": speed,
#                     "language": language_code
#                 },
#                 timeout=60
#             )
            
#             if response.status_code == 200:
#                 data = response.json()
#                 st.session_state.last_response = data
#                 st.success(f"✅ Response generated successfully at {speed}x speed!")
#             else:
#                 error_detail = response.json().get('detail', 'Unknown error')
#                 st.error(f"❌ Error: {error_detail}")
#                 st.session_state.last_response = None
                
#         except requests.exceptions.ConnectionError:
#             st.error("❌ Cannot connect to the API. Make sure the FastAPI server is running on http://localhost:8000")
#             st.session_state.last_response = None
#         except requests.exceptions.Timeout:
#             st.error("❌ Request timed out. The server took too long to respond.")
#             st.session_state.last_response = None
#         except Exception as e:
#             st.error(f"❌ An error occurred: {str(e)}")
#             st.session_state.last_response = None

# elif generate_btn and not question.strip():
#     st.warning("⚠️ Please enter a question first!")

# # Display results if available
# if st.session_state.last_response:
#     data = st.session_state.last_response
    
#     with result_container:
#         # Display question
#         st.markdown("#### 📝 Your Question:")
#         st.info(data['your_question'])
        
#         # Display AI answer
#         st.markdown("#### 🤖 AI Answer:")
#         st.markdown(f"<div class='success-box'>{data['ai_answer']}</div>", unsafe_allow_html=True)
        
#         # Display audio info with speed
#         st.markdown("#### 🔊 Audio Response:")
#         info_text = f"""
#         Audio size: <strong>{data.get('audio_size_kb', 'N/A')} KB</strong> | 
#         Speed: <strong>{data.get('speed', 1.0)}x</strong> | 
#         Language: <strong>{data.get('language_name', 'English')}</strong> | 
#         Engine: <strong>{data.get('tts_engine', 'gTTS')}</strong>
#         """
#         st.markdown(f"<div class='info-box'>{info_text}</div>", unsafe_allow_html=True)
        
#         # Decode and play audio
#         try:
#             audio_bytes = base64.b64decode(data['audio_base64'])
#             st.audio(audio_bytes, format='audio/mp3')
            
#             # Download button
#             st.download_button(
#                 label="📥 Download Audio",
#                 data=audio_bytes,
#                 file_name=f"tts_{data.get('speed', 1.0)}x_{data['your_question'][:30].replace(' ', '_')}.mp3",
#                 mime="audio/mp3",
#                 use_container_width=True
#             )
            
#         except Exception as e:
#             st.error(f"Error playing audio: {str(e)}")

# # Sidebar with information
# with st.sidebar:
#     st.markdown("### ℹ️ About")
#     st.markdown("""
#     This application uses:
#     - **Groq LLM** for text generation
#     - **gTTS** (Google Text-to-Speech) for audio
#     - **Pydub** for speed adjustment
    
#     The AI will answer your questions and convert the response to natural-sounding speech at your preferred speed.
#     """)
    
#     st.markdown("### 🎚️ Speed Guide")
#     st.markdown("""
#     - **0.5x - 0.8x**: Slower, good for learning
#     - **0.9x - 1.1x**: Natural speaking pace
#     - **1.2x - 1.5x**: Faster, for quick listening
#     - **1.6x - 2.0x**: Very fast, for speed readers
#     """)
    
#     st.markdown("### 🔧 Setup Instructions")
#     st.markdown("""
#     1. Install dependencies:
#        ```
#        pip install pydub
#        ```
#     2. Make sure FastAPI server is running:
#        ```
#        python main.py
#        ```
#     3. The API should be accessible at:
#        ```
#        http://localhost:8000
#        ```
#     """)
    
#     st.markdown("### 📊 API Status")
    
#     # Check API health
#     try:
#         health_response = requests.get(f"{API_URL.rsplit('/', 1)[0]}/health", timeout=2)
#         if health_response.status_code == 200:
#             st.success("🟢 API is running")
#             health_data = health_response.json()
#             st.json(health_data)
#         else:
#             st.error("🔴 API is not responding correctly")
#     except:
#         st.error("🔴 API is offline")
#         st.markdown("Start the server with: `python main.py`")
    
#     st.markdown("### 🎯 Tips")
#     st.markdown("""
#     - Use **slower speeds** for learning new content
#     - Use **faster speeds** for familiar content
#     - Try different languages for multilingual responses
#     - Download audio for offline listening
#     """)

# # Footer
# st.markdown("---")
# st.markdown(
#     "<div style='text-align: center; color: #7f8c8d;'>"
#     "Built with ❤️ using Streamlit, FastAPI, Groq & gTTS | Speed Control Enabled ⚡"
#     "</div>",
#     unsafe_allow_html=True
# )