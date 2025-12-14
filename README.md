🎤 AI Interview Practice App
This project showcases a sophisticated, voice-enabled AI application designed to help users practice technical interviews, specifically for roles like Data Scientist. The app provides a realistic interview experience, accepts both voice and text input, and delivers instant, constructive feedback in both audio and text formats.

It's built with a modern stack emphasizing real-time interaction, powered by cutting-edge Generative AI and speech technologies.

✨ Key Features
🎙️ Voice-Based Interviews: Users can speak their answers as they would in a real interview using the integrated microphone feature.

🤖 Role-Specific Questions: The app adapts its questions based on the selected interview type (e.g., Data Scientist), ensuring relevance.

📝 Text and Voice Input: Flexibility to type out answers or questions, or use Google Speech Recognition to capture voice input for a natural conversational flow.

💡 Instant Feedback: Receives structured and actionable feedback on responses from the AI interviewer (powered by Grok LLM).

🗣️ Audio & Text Feedback: Feedback is provided immediately in a structured text format and read aloud using Google TTS (Text-to-Speech).

📜 Conversation History: All questions, user answers, and AI feedback are logged and stored in the Interview Transcript for review and progress tracking.

⚡ Customizable Audio Speed: Users can adjust the playback speed of the AI's audio responses.


Category,Technology,Purpose
Frontend/UI,Streamlit,"Creating the interactive, clean, and intuitive user interface and web application framework."
Backend/API,FastAPI,"Serving the core application logic, handling real-time audio processing, and managing external API calls."
Generative AI,Grok LLM,"Generating complex interview questions, evaluating user responses against best practices, and formulating detailed feedback."
Speech-to-Text (STT),Google Speech Recognition,Accurately transcribing the user's voice input (answers/questions) into text for processing by the LLM.
Text-to-Speech (TTS),Google TTS (gTTS for audio output),Converting the AI's generated feedback text into natural-sounding audio responses for an immersive experience.

🖼️ Project Showcase
Here is a visual overview of the application's main screens and functionalities.

1. Interview Setup and Initial Question
The user selects the interview type (e.g., Data Scientist) and the AI interviewer presents the first question on a relevant technical topic.

2. Providing a Text Answer
The app allows users to type their detailed response as an alternative to voice input, which is then sent for evaluation.

3. Detailed AI Feedback with Audio Playback
The AI interviewer provides structured, constructive feedback on the user's answer, broken down into actionable points. This feedback is available in both text and an accompanying audio format.

4. Full Interview Script and History
The complete log of the interview, including the initial question, user answer, and all feedback, is maintained in the Interview Transcript for easy reference.

5. Normal Conversational Mode
The app also supports a general Q&A mode, allowing users to ask specific questions (e.g., "What is Positional Encoding?") and receive comprehensive, voice-supported answers.

🚀 Getting Started
To run this project locally, follow these steps:

Prerequisites
Python 3.8+

FastAPI and Streamlit dependencies

API keys for the services used (Grok LLM, Google Speech/TTS - if necessary for integration)

Installation
Clone the repository:

Bash

git clone https://github.com/yourusername/ai-interview-app.git
cd ai-interview-app
Create and activate a virtual environment:

Bash

python -m venv venv
source venv/bin/activate  # On Linux/macOS
# .\venv\Scripts\activate  # On Windows
Install the required packages:

Bash

pip install -r requirements.txt
Configuration
Set up Environment Variables: Create a file named .env in the root directory to store your API keys.

Code snippet

# .env file example
GROK_API_KEY="YOUR_GROK_LLM_KEY"
# Placeholder for other keys if needed (e.g., Google Service Account details for STT/TTS)
Running the Application
Run the Backend Server (FastAPI):

Bash

uvicorn app.api:app --reload
This will start the API server, typically accessible at http://127.0.0.1:8000.

Run the Frontend Application (Streamlit): Open a new terminal window, ensure your virtual environment is active, and run:

Bash

streamlit run app.py
The app will open in your default browser, usually at http://localhost:8501.

🤝 Contribution
Contributions, issues, and feature requests are highly welcome! Feel free to check the issues page for open tasks or submit a pull request with your improvements.