import os
import whisper
import tempfile

# ✅ Load Whisper model once at startup
print("Loading Whisper model...")
model = whisper.load_model("small")  # You can also try "medium" or "large" for better accuracy
print("Whisper model loaded!")


def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file using Whisper.
    Forces transcription to English output regardless of input language.
    """

    # ✅ Create a temporary file path (avoid overwriting input)
    temp_wav = tempfile.mktemp(suffix=".wav", dir="audios")

    # ✅ Convert to WAV (mono, 16kHz)
    os.system(f"ffmpeg -y -i \"{file_path}\" -ar 16000 -ac 1 \"{temp_wav}\"")

    # ✅ Transcribe audio and force English translation
    result = model.transcribe(
        temp_wav,
        task="translate",      # ✅ ensures output is English text
        language="en"          # ✅ forces English mode
    )

    text = result["text"]

    # ✅ Clean up temporary file
    try:
        os.remove(temp_wav)
    except Exception:
        pass

    return text
