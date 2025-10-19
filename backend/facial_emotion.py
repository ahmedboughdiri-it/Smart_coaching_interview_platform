from deepface import DeepFace
import cv2
from collections import Counter
import numpy as np

def analyze_facial_emotions(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_interval = fps * 1  # analyze 1 frame every second
    frame_id = 0
    results = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_id % frame_interval == 0:
            try:
                analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                emotion = analysis[0]['dominant_emotion']
                timestamp = int(frame_id / fps)
                results.append({"second": timestamp, "emotion": emotion})
            except:
                pass
        frame_id += 1

    cap.release()

    # summarize emotions
    emotion_counts = Counter([r["emotion"] for r in results])
    total = sum(emotion_counts.values())
    summary = {k: round(v / total, 2) for k, v in emotion_counts.items()}
    dominant = max(summary, key=summary.get)

    output = {
        "dominant_emotion": dominant,
        "emotion_summary": summary,
        "timeline": results,
        "you appeared most of the time":dominant
    }

    return output


