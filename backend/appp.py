import io
import uuid
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from pdfminer.high_level import extract_text
import spacy
import random

app = Flask(__name__)
CORS(app)

# Charger spaCy Transformers pour meilleures entités
nlp = spacy.load("en_core_web_trf")

# Stockage en mémoire (pour démo)
QUIZ_STORE = {}  # quiz_id -> {"answers": {...}, "questions": [...]}

# ------------------- Fonctions utilitaires -------------------

def extract_text_from_pdf(file_stream):
    try:
        text = extract_text(file_stream)
        return text
    except Exception:
        return ""

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_entities(text):
    """Extrait compétences depuis le texte du CV."""
    doc = nlp(text)
    entities = {
        "skills": []
    }

    # Reconnaissance de compétences par entités ou mots-clés
    skill_keywords = [
        "python", "java", "angular", "flask", "sql", "docker", "aws", 
        "machine learning", "react", "c++", "kotlin", "html", "css", "javascript"
    ]

    text_lower = text.lower()
    for word in skill_keywords:
     if re.search(rf"\b{re.escape(word)}\b", text_lower):
        entities["skills"].append(word)


    # Nettoyage doublons
    entities["skills"] = list(set(entities["skills"]))
    return entities

def build_professional_quiz(entities):
    """
    Génère un quiz basé sur les compétences extraites,
    avec des questions pédagogiques ou professionnelles.
    """
    questions = []

    skill_questions = {
    "python": [
        {"question": "Python is mainly used for?", "options": ["Web development", "Data analysis", "Mobile apps", "All of the above"], "type": "mcq", "answer_index": 3},
        {"question": "Python supports object-oriented programming.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which library is used for data analysis in Python?", "options": ["NumPy", "React", "Spring", "Django"], "type": "mcq", "answer_index": 0}
    ],
    "java": [
        {"question": "Java is a ___ language.", "options": ["Procedural", "Object-oriented", "Functional", "Markup"], "type": "mcq", "answer_index": 1},
        {"question": "Java runs on JVM.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which framework is commonly used with Java for web applications?", "options": ["Spring", "Angular", "Flask", "React"], "type": "mcq", "answer_index": 0}
    ],
    "angular": [
        {"question": "Angular is a framework for?", "options": ["Backend", "Frontend", "Database", "Operating System"], "type": "mcq", "answer_index": 1},
        {"question": "Angular uses TypeScript.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which directive is used for conditional rendering in Angular?", "options": ["*ngIf", "*ngFor", "*ngSwitch", "*ngModel"], "type": "mcq", "answer_index": 0}
    ],
    "react": [
        {"question": "React is mainly used for?", "options": ["Backend", "Frontend", "Database", "Networking"], "type": "mcq", "answer_index": 1},
        {"question": "React is a JavaScript library.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which hook is used to manage state in React?", "options": ["useState", "useEffect", "useReducer", "useContext"], "type": "mcq", "answer_index": 0}
    ],
    "docker": [
        {"question": "Docker is mainly used for?", "options": ["Containerization", "Database management", "Networking", "Machine Learning"], "type": "mcq", "answer_index": 0},
        {"question": "Docker allows isolated environments.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which command is used to build a Docker image?", "options": ["docker build", "docker run", "docker compose", "docker start"], "type": "mcq", "answer_index": 0}
    ],
    "aws": [
        {"question": "AWS is a cloud service provider.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which AWS service is for serverless functions?", "options": ["EC2", "Lambda", "S3", "RDS"], "type": "mcq", "answer_index": 1},
        {"question": "S3 is mainly used for?", "options": ["Compute", "Storage", "Networking", "Database"], "type": "mcq", "answer_index": 1}
    ],
    "sql": [
        {"question": "SQL is used for?", "options": ["Data querying", "Machine learning", "Web design", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "SQL databases are relational.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which SQL command is used to remove rows?", "options": ["DELETE", "DROP", "REMOVE", "TRUNCATE"], "type": "mcq", "answer_index": 0}
    ],
    "flask": [
        {"question": "Flask is a framework for?", "options": ["Backend Web Development", "Frontend", "Mobile Apps", "Database"], "type": "mcq", "answer_index": 0},
        {"question": "Flask is a microframework.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which command runs a Flask app?", "options": ["flask run", "python manage.py", "npm start", "docker run"], "type": "mcq", "answer_index": 0}
    ],
    "machine learning": [
        {"question": "Machine Learning is a subset of?", "options": ["AI", "Web development", "Databases", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "Supervised learning requires labeled data.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which library is used for ML in Python?", "options": ["scikit-learn", "React", "Angular", "Flask"], "type": "mcq", "answer_index": 0}
    ],
    "c++": [
        {"question": "C++ is mainly used for?", "options": ["System programming", "Web frontend", "Cloud management", "Database"], "type": "mcq", "answer_index": 0},
        {"question": "C++ supports object-oriented programming.", "options": ["True", "False"], "type": "tf", "answer_index": 0}
    ],
    "kotlin": [
        {"question": "Kotlin is mainly used for?", "options": ["Android development", "iOS development", "Web backend", "Machine Learning"], "type": "mcq", "answer_index": 0},
        {"question": "Kotlin is fully interoperable with Java.", "options": ["True", "False"], "type": "tf", "answer_index": 0}
    ],
    "html": [
        {"question": "HTML stands for?", "options": ["Hyper Text Markup Language", "High Text Machine Language", "Hyperlinks Text Markup Language", "Home Tool Markup Language"], "type": "mcq", "answer_index": 0},
        {"question": "HTML is used to structure web content.", "options": ["True", "False"], "type": "tf", "answer_index": 0}
    ],
    "css": [
        {"question": "CSS is used for?", "options": ["Styling web pages", "Backend development", "Database management", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "CSS stands for Cascading Style Sheets.", "options": ["True", "False"], "type": "tf", "answer_index": 0}
    ],
    "javascript": [
        {"question": "JavaScript is mainly used for?", "options": ["Frontend interactivity", "Database", "Operating System", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "JavaScript is a compiled language.", "options": ["True", "False"], "type": "tf", "answer_index": 1}
    ],
    "nodejs": [
        {"question": "Node.js is used for?", "options": ["Frontend", "Backend", "Database", "Networking"], "type": "mcq", "answer_index": 1},
        {"question": "Node.js uses JavaScript on the server-side.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which command initializes a Node.js project?", "options": ["npm init", "node start", "npm create", "node init"], "type": "mcq", "answer_index": 0}
    ],
    "django": [
        {"question": "Django is a framework for?", "options": ["Backend Web Development", "Frontend", "Database", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "Django follows the MTV (Model-Template-View) architecture.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which command starts a Django project?", "options": ["django-admin startproject", "python manage.py startproject", "npm start", "flask run"], "type": "mcq", "answer_index": 0}
    ],
    "git": [
        {"question": "Git is used for?", "options": ["Version Control", "Database", "Backend", "Cloud services"], "type": "mcq", "answer_index": 0},
        {"question": "Git allows collaboration between multiple developers.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which command stages files for commit?", "options": ["git add", "git commit", "git push", "git merge"], "type": "mcq", "answer_index": 0}
    ],
    "kubernetes": [
        {"question": "Kubernetes is used for?", "options": ["Container orchestration", "Frontend framework", "Database management", "AI model training"], "type": "mcq", "answer_index": 0},
        {"question": "Kubernetes automates deployment, scaling, and management of containers.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which Kubernetes object represents a single application instance?", "options": ["Pod", "Service", "Node", "ReplicaSet"], "type": "mcq", "answer_index": 0}
    ],
    "tensorflow": [
        {"question": "TensorFlow is a library for?", "options": ["Machine Learning", "Web development", "Database management", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "TensorFlow supports deep learning model development.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which type of neural network is commonly used for image processing?", "options": ["CNN", "RNN", "DNN", "SVM"], "type": "mcq", "answer_index": 0}
    ],
    "pandas": [
        {"question": "Pandas is a library in Python for?", "options": ["Data manipulation and analysis", "Frontend development", "Networking", "Cloud services"], "type": "mcq", "answer_index": 0},
        {"question": "Pandas provides DataFrame and Series data structures.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which method is used to read CSV files in pandas?", "options": ["read_csv()", "readExcel()", "readFile()", "open_csv()"], "type": "mcq", "answer_index": 0}
    ],
    "nlp": [
        {"question": "NLP stands for?", "options": ["Natural Language Processing", "Neural Learning Process", "Network Layer Protocol", "None of the above"], "type": "mcq", "answer_index": 0},
        {"question": "Tokenization is a common preprocessing step in NLP.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which Python library is widely used for NLP?", "options": ["spaCy", "Flask", "React", "Docker"], "type": "mcq", "answer_index": 0}
    ],
    "react native": [
        {"question": "React Native is used for?", "options": ["Mobile App Development", "Database management", "Cloud computing", "Networking"], "type": "mcq", "answer_index": 0},
        {"question": "React Native allows building apps for both Android and iOS.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which language is mainly used in React Native?", "options": ["JavaScript", "Python", "Java", "Kotlin"], "type": "mcq", "answer_index": 0}
    ],
    "cybersecurity": [
        {"question": "Which of the following is a cybersecurity practice?", "options": ["Penetration testing", "UI design", "Database normalization", "Backend API creation"], "type": "mcq", "answer_index": 0},
        {"question": "Encryption helps protect sensitive data.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which protocol is commonly used for secure web communication?", "options": ["HTTPS", "HTTP", "FTP", "SMTP"], "type": "mcq", "answer_index": 0}
    ],
    "rest api": [
        {"question": "REST API stands for?", "options": ["Representational State Transfer", "Random Server Transfer", "Relational Server Technique", "Remote State Transfer"], "type": "mcq", "answer_index": 0},
        {"question": "REST APIs use HTTP methods like GET, POST, PUT, DELETE.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which status code represents a successful request?", "options": ["200", "404", "500", "301"], "type": "mcq", "answer_index": 0}
    ],
    "devops": [
        {"question": "DevOps combines?", "options": ["Development and Operations", "Frontend and Backend", "Networking and Security", "Database and AI"], "type": "mcq", "answer_index": 0},
        {"question": "CI/CD pipelines are part of DevOps practices.", "options": ["True", "False"], "type": "tf", "answer_index": 0},
        {"question": "Which tool is used for continuous integration?", "options": ["Jenkins", "React", "Flask", "Docker"], "type": "mcq", "answer_index": 0}
    ]
}


    for skill in entities.get("skills", []):
        skill_lower = skill.lower()
        if skill_lower in skill_questions:
            q_list = skill_questions[skill_lower]
            for q in q_list:
                question_obj = {
                    "id": str(uuid.uuid4()),
                    "question": q["question"],
                    "options": q["options"],
                    "type": q["type"],
                    "_correct_answer": q.get("answer_index"),
                    "_correct_answer_text": q.get("answer_text")
                }
                questions.append(question_obj)

    random.shuffle(questions)
    return questions[:10]

# ------------------- Endpoints -------------------

@app.route("/generate-quiz", methods=["POST"])
def generate_quiz():
    text = ""

    # Récupération du texte du CV
    if "text" in request.form and request.form["text"].strip():
        text = request.form["text"]
    elif "file" in request.files:
        f = request.files["file"]
        content = f.read()
        filename = f.filename.lower()
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(io.BytesIO(content))
        else:
            try:
                text = content.decode("utf-8", errors="ignore")
            except:
                text = ""
    else:
        return jsonify({"error":"No CV provided (send 'file' or 'text')"}), 400

    text = clean_text(text)
    if not text:
        return jsonify({"error":"Empty CV text after extraction"}), 400

    # Extraction compétences et génération quiz
    entities = extract_entities(text)
    questions = build_professional_quiz(entities)

    # Préparer réponses
    answers_map = {}
    for q in questions:
        qid = q["id"]
        if q["type"] in ["mcq", "tf"]:
            answers_map[qid] = {"type": q["type"], "answer_index": q["_correct_answer"]}
        else:
            answers_map[qid] = {"type": "short", "answer_text": q["_correct_answer_text"].lower()}

        if "_correct_answer" in q: del q["_correct_answer"]
        if "_correct_answer_text" in q: del q["_correct_answer_text"]

    quiz_id = str(uuid.uuid4())
    QUIZ_STORE[quiz_id] = {"answers": answers_map, "questions": questions}

    return jsonify({"quiz_id": quiz_id, "questions": questions})

@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    data = request.get_json()
    if not data:
        return jsonify({"error":"Expected JSON body"}), 400

    quiz_id = data.get("quiz_id")
    answers = data.get("answers", [])

    if not quiz_id or quiz_id not in QUIZ_STORE:
        return jsonify({"error":"Invalid quiz_id"}), 400

    store = QUIZ_STORE[quiz_id]
    answers_map = store["answers"]

    total = len(answers_map)
    score = 0
    feedback = []

    prov = {a["id"]: a.get("answer") for a in answers}

    for qid, meta in answers_map.items():
        if qid not in prov:
            feedback.append({"id": qid, "correct": False, "reason":"no answer submitted"})
            continue
        submitted = prov[qid]
        if meta["type"] in ["mcq", "tf"]:
            correct_index = meta["answer_index"]
            try:
                submitted_index = int(submitted)
            except:
                feedback.append({"id": qid, "correct": False, "reason":"invalid answer type"})
                continue
            correct = submitted_index == correct_index
            if correct:
                score += 1
            feedback.append({"id": qid, "correct": correct, "correct_index": correct_index, "submitted_index": submitted_index})
        else:  # short answer
            expected = meta["answer_text"].lower()
            submitted_text = str(submitted).lower()
            correct = expected in submitted_text or submitted_text in expected
            if correct:
                score += 1
            feedback.append({"id": qid, "correct": correct, "expected": expected, "submitted": submitted_text})

    return jsonify({"score": score, "total": total, "feedback": feedback})

# ------------------- Main -------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
