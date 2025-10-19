from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from io import BytesIO
import shutil, os, json, re

# Import your existing functions
from cv_utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    summarize_cv,
    generate_questions_with_ai,
    chat_with_ai,
    tts_to_audio,
    speech_to_text
)


# If you have a facial emotion module
from facial_emotion import analyze_facial_emotions
from audio_transcribe import transcribe_audio
import logging
# 8️⃣ Feedback Endpoint
from cv_utils import generate_feedback  # new function you will add


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Interview Backend")



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folders
os.makedirs("videos", exist_ok=True)
os.makedirs("audios", exist_ok=True)

# ---------------- Endpoints ---------------- #


@app.post("/feedback")
async def feedback_endpoint(
    question: str = Form(...),
    answer: str = Form(...),
    facial_result: str = Form(...)
):
    feedback_text = generate_feedback(question, answer, facial_result)
    return {"feedback": feedback_text}


@app.post("/generate_feedback")
async def generate_feedback_endpoint(
    summary: str = Form(''),
    facial: str = Form(''),
    question: str = Form('')
):
    """Compatibility endpoint for frontend: accepts 'summary' and 'facial' form fields.

    The underlying `generate_feedback` helper expects (question, answer, facial_result),
    so we map `summary` -> answer. `question` is optional.
    """
    try:
        feedback_text = generate_feedback(question or '', summary or '', facial or '')
    except Exception as e:
        feedback_text = f"Error generating feedback: {str(e)}"
    return {"feedback": feedback_text}

# 1️⃣ Facial emotion analysis
@app.post("/analyze_video")
async def analyze_video(file: UploadFile = File(...)):
    file_location = f"videos/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    result = analyze_facial_emotions(file_location)
    return result

# 2️⃣ Audio transcription
@app.post("/transcribe_audio")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    file_location = f"audios/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    text = transcribe_audio(file_location)
    return {"transcription": text}

# 3️⃣ CV summarization
@app.post("/summarize_cv")
async def summarize_cv_endpoint(file: UploadFile = File(...)):
    file_bytes = await file.read()
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
    summary = summarize_cv(text)
    return {"summary": summary}

# 4️⃣ Generate AI interview questions
@app.post("/generate_questions")
async def generate_questions_endpoint(summary: str = Form(...), api_key: str = Form(...), num_questions: int = Form(4)):
    questions = generate_questions_with_ai(summary, api_key, num_questions)
    return {"questions": questions}

# 5️⃣ Chat with AI about CV
@app.post("/chat_with_ai")
async def chat_with_ai_endpoint(
    message: str = Form(...),
    cv_summary: str = Form(...),
    conversation_history: str = Form(...),
    api_key: str = Form(...)
):
    history = json.loads(conversation_history)
    answer, error = chat_with_ai(message, cv_summary, history, api_key)
    if error:
        return {"error": error}
    return {"answer": answer}

# 6️⃣ Text-to-speech
@app.post("/text_to_speech")
async def text_to_speech_endpoint(text: str = Form(...)):
    audio_bytes, error = tts_to_audio(text)
    if error:
        return {"error": error}
    return StreamingResponse(BytesIO(audio_bytes), media_type="audio/mp3")

# 7️⃣ Speech-to-text (microphone)
@app.get("/speech_to_text")
async def speech_to_text_endpoint():
    text, error = speech_to_text()
    if error:
        return {"error": error}
    return {"transcription": text}
