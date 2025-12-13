#pydub installed which is a package 
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
import os
from groq import Groq
from dotenv import load_dotenv
from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
from pydub.effects import speedup

load_dotenv()

app = FastAPI(title="Text → Voice using Groq + gTTS")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise Exception("Please set GROQ_API_KEY in .env file!")

groq_client = Groq(api_key=GROQ_API_KEY)


def adjust_audio_speed(audio_bytes: bytes, speed: float) -> bytes:
    """
    Adjust the playback speed of audio
    
    Args:
        audio_bytes: Original audio data
        speed: Speed multiplier (0.5 = half speed, 1.0 = normal, 2.0 = double speed)
    
    Returns:
        Modified audio bytes
    """
    try:
        # Load audio from bytes
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
        
        if speed != 1.0:
            # Method 1: Change playback speed (recommended)
            if speed > 1.0:
                # Speed up
                audio = speedup(audio, playback_speed=speed)
            else:
                # Slow down by changing frame rate
                audio = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(audio.frame_rate * speed)
                })
                audio = audio.set_frame_rate(audio.frame_rate)
        
        # Export back to bytes
        output_buffer = BytesIO()
        audio.export(output_buffer, format="mp3")
        output_buffer.seek(0)
        
        return output_buffer.read()
    
    except Exception as e:
        print(f"Error adjusting speed: {str(e)}")
        # Return original audio if speed adjustment fails
        return audio_bytes


@app.get("/")
async def root():
    return {
        "message": "Text-to-Speech API is running!",
        "endpoints": {
            "/ask": "POST - Generate text and audio from a question",
            "/health": "GET - Check API health"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "tts_engine": "gTTS (Google Text-to-Speech)",
        "features": ["speed_control", "multiple_languages"]
    }


@app.post("/ask")
async def ask(
    question: str = Form(...),
    speed: float = Form(1.0),
    language: str = Form("en")
):
    """
    Generate AI response and convert to speech with speed control
    
    Args:
        question: The text question to ask the AI
        speed: Audio playback speed (0.5 to 2.0, default 1.0)
        language: TTS language code (en, bn, hi, es, fr, etc.)
    
    Returns:
        JSON with question, AI answer, and base64 encoded audio
    """
    if not question.strip():
        raise HTTPException(status_code=400, detail="Please provide a question")
    
    # Validate speed
    if speed < 0.5 or speed > 2.0:
        raise HTTPException(status_code=400, detail="Speed must be between 0.5 and 2.0")

    # Validate language
    supported_languages = {
        "en": "English",
        "bn": "Bengali", 
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese"
    }
    
    if language not in supported_languages:
        language = "en"  # Default to English

    # -----------------------------
    # 1️⃣ Generate answer using Groq LLM
    # -----------------------------
    try:
        print(f"📝 Processing question: {question[:50]}...")
        print(f"🎚️ Speed: {speed}x | Language: {language}")
        
        llm_response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": question}],
            max_tokens=200,
            temperature=0.7
        )
        answer_text = llm_response.choices[0].message.content
        print(f"✅ LLM Response: {answer_text[:100]}...")
        
    except Exception as e:
        print(f"❌ Groq LLM Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Groq LLM failed: {str(e)}")

    # -----------------------------
    # 2️⃣ Convert answer to speech using gTTS
    # -----------------------------
    try:
        print("🎙️ Generating speech with gTTS...")
        
        # Check if we should use slow mode for gTTS
        use_slow_mode = speed < 0.8
        
        # Create gTTS object
        tts = gTTS(text=answer_text, lang=language, slow=use_slow_mode)
        
        # Save to BytesIO buffer
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        
        # Get audio bytes
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()
        
        # Validate audio data
        if len(audio_bytes) == 0:
            raise Exception("gTTS returned empty audio")
        
        print(f"✅ Initial audio generated: {len(audio_bytes) / 1024:.2f} KB")
        
        # Adjust speed if needed (and if not using gTTS slow mode)
        if speed != 1.0 and not use_slow_mode:
            print(f"⚡ Adjusting audio speed to {speed}x...")
            audio_bytes = adjust_audio_speed(audio_bytes, speed)
            print(f"✅ Speed-adjusted audio: {len(audio_bytes) / 1024:.2f} KB")
        
        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        print(f"✅ Audio generated successfully!")
        print(f"   Final audio size: {len(audio_bytes) / 1024:.2f} KB")
        
    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

    # -----------------------------
    # 3️⃣ Return both text + audio
    # -----------------------------
    return JSONResponse({
        "success": True,
        "your_question": question,
        "ai_answer": answer_text,
        "audio_base64": audio_b64,
        "audio_size_kb": round(len(audio_bytes) / 1024, 2),
        "tts_engine": "gTTS",
        "speed": speed,
        "language": language,
        "language_name": supported_languages.get(language, "English")
    })


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Text-to-Speech API server...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)










# from fastapi import FastAPI, Form, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# import base64
# import os
# from groq import Groq
# from dotenv import load_dotenv
# from gtts import gTTS
# from io import BytesIO

# load_dotenv()

# app = FastAPI(title="Text → Voice using Groq + gTTS")

# # Add CORS middleware for web interface testing
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify your domain
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -----------------------------
# # Load API key from .env
# # -----------------------------
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# if not GROQ_API_KEY:
#     raise Exception("Please set GROQ_API_KEY in .env file!")

# groq_client = Groq(api_key=GROQ_API_KEY)


# @app.get("/")
# async def root():
#     return {
#         "message": "Text-to-Speech API is running!",
#         "endpoints": {
#             "/ask": "POST - Generate text and audio from a question",
#             "/health": "GET - Check API health"
#         }
#     }


# @app.get("/health")
# async def health():
#     return {"status": "healthy", "tts_engine": "gTTS (Google Text-to-Speech)"}


# @app.post("/ask")
# async def ask(question: str = Form(...)):
#     """
#     Generate AI response and convert to speech
    
#     Args:
#         question: The text question to ask the AI
    
#     Returns:
#         JSON with question, AI answer, and base64 encoded audio
#     """
#     if not question.strip():
#         raise HTTPException(status_code=400, detail="Please provide a question")

#     # -----------------------------
#     # 1️⃣ Generate answer using Groq LLM
#     # -----------------------------
#     try:
#         print(f"📝 Processing question: {question[:50]}...")
        
#         llm_response = groq_client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[{"role": "user", "content": question}],
#             max_tokens=200,
#             temperature=0.7
#         )
#         answer_text = llm_response.choices[0].message.content
#         print(f"✅ LLM Response: {answer_text[:100]}...")
        
#     except Exception as e:
#         print(f"❌ Groq LLM Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Groq LLM failed: {str(e)}")

#     # -----------------------------
#     # 2️⃣ Convert answer to speech using gTTS
#     # -----------------------------
#     try:
#         print("🎙️ Generating speech with gTTS...")
        
#         # Create gTTS object
#         # lang options: 'en' (English), 'bn' (Bengali), 'es' (Spanish), etc.
#         tts = gTTS(text=answer_text, lang='en', slow=False)
        
#         # Save to BytesIO buffer instead of file
#         audio_buffer = BytesIO()
#         tts.write_to_fp(audio_buffer)
        
#         # Get audio bytes
#         audio_buffer.seek(0)
#         audio_bytes = audio_buffer.read()
        
#         # Validate audio data
#         if len(audio_bytes) == 0:
#             raise Exception("gTTS returned empty audio")
        
#         # Encode to base64
#         audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        
#         print(f"✅ Audio generated successfully!")
#         print(f"   Audio size: {len(audio_bytes) / 1024:.2f} KB")
#         print(f"   Base64 length: {len(audio_b64)} characters")
        
#     except Exception as e:
#         print(f"❌ TTS Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

#     # -----------------------------
#     # 3️⃣ Return both text + audio
#     # -----------------------------
#     return JSONResponse({
#         "success": True,
#         "your_question": question,
#         "ai_answer": answer_text,
#         "audio_base64": audio_b64,
#         "audio_size_kb": round(len(audio_bytes) / 1024, 2),
#         "tts_engine": "gTTS"
#     })


# # Optional: Add endpoint to save audio directly
# @app.post("/ask-with-file")
# async def ask_with_file(question: str = Form(...)):
#     """
#     Generate AI response and save audio to file
    
#     Args:
#         question: The text question to ask the AI
    
#     Returns:
#         JSON with question, AI answer, and file path
#     """
#     if not question.strip():
#         raise HTTPException(status_code=400, detail="Please provide a question")

#     # Generate answer
#     try:
#         llm_response = groq_client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[{"role": "user", "content": question}],
#             max_tokens=200
#         )
#         answer_text = llm_response.choices[0].message.content
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Groq LLM failed: {str(e)}")

#     # Generate speech and save to file
#     try:
#         # Create output directory if it doesn't exist
#         os.makedirs("audio_output", exist_ok=True)
        
#         # Generate filename
#         import time
#         filename = f"audio_output/response_{int(time.time())}.mp3"
        
#         # Generate and save audio
#         tts = gTTS(text=answer_text, lang='en', slow=False)
#         tts.save(filename)
        
#         print(f"✅ Audio saved to: {filename}")
        
#         return JSONResponse({
#             "success": True,
#             "your_question": question,
#             "ai_answer": answer_text,
#             "audio_file": filename
#         })
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


# if __name__ == "__main__":
#     import uvicorn
#     print("🚀 Starting Text-to-Speech API server...")
#     print("📍 API will be available at: http://localhost:8000")
#     print("📖 API docs at: http://localhost:8000/docs")
#     uvicorn.run(app, host="0.0.0.0", port=8000)






# from fastapi import FastAPI, Form, HTTPException
# from fastapi.responses import JSONResponse
# import requests
# import base64
# import os
# from groq import Groq
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI(title="Text → Voice using Groq + HuggingFace TTS")

# # -----------------------------
# # Load API keys from .env
# # -----------------------------
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# HF_API_KEY = os.getenv("HF_API_KEY")

# if not GROQ_API_KEY or not HF_API_KEY:
#     raise Exception("Please set GROQ_API_KEY and HF_API_KEY in .env file!")

# groq_client = Groq(api_key=GROQ_API_KEY)

# # TTS Model (Hugging Face Hosted, free)
# TTS_MODEL = "anycoderapps/VibeVoice-Realtime-0.5B"  # change to beng for Bangla
# #microsoft/speecht5_tts
# #facebook/mms-tts-eng
# #anycoderapps/VibeVoice-Realtime-0.5B


# @app.post("/ask")
# async def ask(question: str = Form(...)):
#     if not question.strip():
#         raise HTTPException(status_code=400, detail="Please provide a question")

#     # -----------------------------
#     # 1️⃣ Generate answer using Groq LLM
#     # -----------------------------
#     try:
#         llm_response = groq_client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[{"role": "user", "content": question}],
#             max_tokens=200
#         )
#         answer_text = llm_response.choices[0].message.content
#         print('LLM Text', answer_text)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Groq LLM failed: {str(e)}")

#     # -----------------------------
#     # 2️⃣ Convert answer to speech (Hugging Face TTS)
#     # -----------------------------
#     #https://api-inference.huggingface.co/models/{TTS_MODEL}
#     #f"https://router.huggingface.co/models/{TTS_MODEL}",
#     try:
#         tts_payload = {"inputs": answer_text}
#         tts_response = requests.post(
#             f"https://router.huggingface.co/models/{TTS_MODEL}",
#             headers={
#                 "Authorization": f"Bearer {HF_API_KEY}",
#                 "Accept": "audio/wav"
#             },
#             json=tts_payload
#         )

#         if tts_response.status_code != 200:
#             raise HTTPException(status_code=500, detail=f"TTS failed: {tts_response.text}")

#         audio_bytes = tts_response.content
#         audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")

#     # -----------------------------
#     # 3️⃣ Return both text + audio
#     # -----------------------------
#     return JSONResponse({
#         "your_question": question,
#         "ai_answer": answer_text,
#         "audio_base64": audio_b64
#     })











# from fastapi import FastAPI, UploadFile, Form, HTTPException
# import requests
# import base64
# from fastapi.responses import JSONResponse
# from groq import Groq
# import os
# from dotenv import load_dotenv

# #pip install python-multipart

# load_dotenv()

# app = FastAPI()

# # Load API keys
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# HF_API_KEY = os.getenv("HF_API_KEY")

# if not GROQ_API_KEY or not HF_API_KEY:
#     raise Exception("❌ Missing GROQ_API_KEY or HF_API_KEY in .env file!")

# groq_client = Groq(api_key=GROQ_API_KEY)

# # 1. voice - text (whisper)

# def speech_to_text(audio_file: UploadFile):
#     url = "https://api-inference.huggingface.co/models/distil-whisper/distil-large-v3"

#     headers = {"Authorization": f"Bearer {HF_API_KEY}"}

#     audio_bytes = audio_file.file.read()

#     response = requests.post(url, headers=headers, data=audio_bytes)

#     if response.status_code != 200:
#         print('STT ERROR:', response.text)
#         return None
    
#     return response.json().get('text')


# # 2 - text to text 


# def generate_answer(question:str):
#     res = groq_client.chat.completions.create(
#         model="llama3-8b-8192",
#         messages=[{"role": "user", "content": question}],
#         max_tokens=200,
#         temperature=0.7
#     )

#     return res.choices[0].message.content




# def text_to_speech(text:str):
#     url = "https://api-inference.huggingface.co/models/coqui/XTTS-v2"
#     headers = {"Authorization": f"Bearer {HF_API_KEY}"}
#     data={'text':text}

#     res = requests.post(url, headers=headers, json=data)

#     if res.status_code != 200:
#         print("TTS ERROR:", res.text)
#         return None
    
#     audio_bytes = res.content
#     return base64.b64encode(audio_bytes).decode()


# # Main api 

# @app.post("/ask")
# async def ask(question: str = Form(""), audio: UploadFile = None):
#     # get user input
#     if audio:
#         print("🎤 Processing voice...")
#         question = speech_to_text(audio)

#     if not question:
#         return JSONResponse({"error": "No question provided!"}, status_code=400)

#     print("🤖 Generating answer...")
#     answer = generate_answer(question)

#     print("🔊 Converting answer to speech...")
#     audio_b64 = text_to_speech(answer)

#     return {
#         "input_text": question,
#         "ai_text": answer,
#         "ai_audio": audio_b64
#     }

# # ----------------------------------------------------------
# # 5️⃣ Root endpoint
# # ----------------------------------------------------------
# @app.get("/")
# def root():
#     return {"status": "Voice AI Server Running!"}