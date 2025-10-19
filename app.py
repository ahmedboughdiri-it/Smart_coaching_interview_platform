import streamlit as st
import os
from io import BytesIO
import tempfile
import requests
import re
import time
import speech_recognition as sr
from gtts import gTTS

# PDF and DOCX parsing
def extract_text_from_pdf(file_bytes):
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file_bytes):
    try:
        from docx import Document
        doc = Document(BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {e}"

def extract_cv_content_intelligent(lines):
    """
    Intelligent extraction when no clear section headers are found
    """
    sections = {
        'profile': [],
        'skills': [],
        'experience': [],
        'education': [],
        'projects': [],
        'languages': [],
        'certifications': []
    }
    
    # Keywords for classification
    skill_keywords = ['python', 'java', 'javascript', 'react', 'node', 'docker', 'kubernetes', 
                     'aws', 'azure', 'gcp', 'ci/cd', 'devops', 'git', 'sql', 'mongodb',
                     'framework', 'library', 'database', 'tool', 'technology', 'angular', 'vue']
    
    experience_keywords = ['intern', 'developer', 'engineer', 'manager', 'analyst', 'consultant',
                          'worked', 'developed', 'implemented', 'led', 'managed', 'designed']
    
    education_keywords = ['university', 'college', 'school', 'degree', 'bachelor', 'master',
                         'diploma', 'baccalaureate', 'engineering', 'computer science', 'esprit']
    
    project_keywords = ['project', 'platform', 'application', 'system', 'website', 'app',
                       'developed', 'built', 'created', 'implemented']
    
    cert_keywords = ['certification', 'certificate', 'certified', 'ccna', 'aws certified',
                    'training', 'course']
    
    language_keywords = ['english', 'french', 'arabic', 'spanish', 'german', 'fluent', 'native']
    
    for line in lines:
        line_lower = line.lower()
        
        # Skip very short lines
        if len(line) < 10:
            continue
        
        # Classify line based on keywords
        if any(kw in line_lower for kw in education_keywords):
            sections['education'].append(line)
        elif any(kw in line_lower for kw in cert_keywords):
            sections['certifications'].append(line)
        elif any(kw in line_lower for kw in language_keywords) and len(line) < 100:
            sections['languages'].append(line)
        elif any(kw in line_lower for kw in project_keywords):
            sections['projects'].append(line)
        elif any(kw in line_lower for kw in experience_keywords):
            sections['experience'].append(line)
        elif any(kw in line_lower for kw in skill_keywords):
            sections['skills'].append(line)
        elif re.search(r'\d{4}', line) and any(kw in line_lower for kw in ['tunis', 'intern', 'engineer']):
            sections['experience'].append(line)
    
    return sections

def summarize_cv(text):
    """
    Parse and summarize CV content into structured sections
    """
    # Clean and normalize text
    text = text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    
    # Initialize sections
    sections = {
        'profile': [],
        'skills': [],
        'experience': [],
        'education': [],
        'projects': [],
        'languages': [],
        'certifications': []
    }
    
    current_section = None
    buffer = []
    
    # Section header patterns
    section_headers = {
        'profile': r'^(profile|summary|about|objective|introduction)$',
        'skills': r'^(skills?|technical skills?|competenc|technologies|expertise)$',
        'experience': r'^(experience|work experience|employment|professional experience)$',
        'education': r'^(education|academic|qualifications?)$',
        'projects': r'^(projects?|portfolio|work samples?)$',
        'languages': r'^(languages?|linguistic skills?)$',
        'certifications': r'^(certifications?|certificates?|training|courses?)$'
    }
    
    # Detect section headers and group content
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if this is a major section header
        is_section_header = False
        if len(line.split()) <= 4:  # Section headers are usually short
            for section_name, pattern in section_headers.items():
                if re.match(pattern, line_lower, re.I):
                    # Save previous section
                    if current_section and buffer:
                        sections[current_section].extend(buffer)
                    
                    current_section = section_name
                    buffer = []
                    is_section_header = True
                    break
        
        # Add content to buffer if not a header
        if not is_section_header and line:
            # Filter out very short lines and page numbers
            if len(line) > 5 and not re.match(r'^\d+$', line):
                buffer.append(line)
    
    # Save last section
    if current_section and buffer:
        sections[current_section].extend(buffer)
    
    # If no clear sections detected, try intelligent extraction
    if not any(sections.values()):
        sections = extract_cv_content_intelligent(lines)
    
    # Build formatted summary
    summary = ""
    
    # Profile/Summary
    if sections['profile']:
        summary += "## Professional Profile\n\n"
        for item in sections['profile'][:3]:
            summary += f"{item}\n\n"
    
    # Education (show first for students/recent grads)
    if sections['education']:
        summary += "## Education\n\n"
        for item in sections['education'][:5]:
            if not item.startswith(('•', '-', '●', '○')):
                summary += f"- {item}\n"
            else:
                summary += f"{item}\n"
        summary += "\n"
    
    # Skills
    if sections['skills']:
        summary += "## Technical Skills\n\n"
        # Group skills if they contain colons (e.g., "Languages: Python, Java")
        for item in sections['skills'][:20]:
            if ':' in item and len(item.split(':')[0]) < 30:
                # This is a categorized skill
                summary += f"**{item.split(':')[0]}:** {item.split(':', 1)[1].strip()}\n\n"
            else:
                if not item.startswith(('•', '-', '●', '○')):
                    summary += f"- {item}\n"
                else:
                    summary += f"{item}\n"
        summary += "\n"
    
    # Experience
    if sections['experience']:
        summary += "## Professional Experience\n\n"
        for item in sections['experience'][:15]:
            # Check if it's a job title/company line (usually shorter and contains dates)
            if re.search(r'\d{4}|\d{2}/\d{4}', item) and len(item) < 150:
                summary += f"\n**{item}**\n"
            else:
                if not item.startswith(('•', '-', '●', '○')):
                    summary += f"  - {item}\n"
                else:
                    summary += f"  {item}\n"
        summary += "\n"
    
    # Projects
    if sections['projects']:
        summary += "## Projects\n\n"
        for item in sections['projects'][:12]:
            # Check if it's a project title (usually has | or – separator)
            if '|' in item or '–' in item or '—' in item:
                summary += f"\n**{item}**\n"
            else:
                if not item.startswith(('•', '-', '●', '○')):
                    summary += f"  - {item}\n"
                else:
                    summary += f"  {item}\n"
        summary += "\n"
    
    # Languages
    if sections['languages']:
        summary += "## Languages\n\n"
        for item in sections['languages'][:5]:
            if not item.startswith(('•', '-', '●', '○')):
                summary += f"- {item}\n"
            else:
                summary += f"{item}\n"
        summary += "\n"
    
    # Certifications
    if sections['certifications']:
        summary += "## Certifications\n\n"
        for item in sections['certifications'][:8]:
            if not item.startswith(('•', '-', '●', '○')):
                summary += f"- {item}\n"
            else:
                summary += f"{item}\n"
        summary += "\n"
    
    # Fallback if nothing was extracted
    if not summary.strip():
        summary = "## CV Content\n\n"
        summary += "Unable to parse CV structure. Here's the extracted content:\n\n"
        for line in lines[:30]:
            if len(line) > 10:
                summary += f"- {line}\n"
    
    return summary.strip()

def generate_questions_with_ai(summary, api_key, num_questions=4):
    """
    Use OpenRouter AI (Llama 3.3 70B) to generate intelligent, contextual interview questions
    """
    try:
        # Prepare the prompt for AI
        prompt = f"""You are an experienced technical recruiter conducting job interviews. Based on the following candidate's CV summary, generate exactly {num_questions} insightful interview questions.

Requirements for questions:
1. Be SPECIFIC to the candidate's actual experience, skills, and projects mentioned in their CV
2. Test both technical knowledge and problem-solving abilities
3. Be open-ended to encourage detailed responses
4. Cover different aspects: technical skills, projects, experience, and soft skills
5. Make questions conversational and professional

CV Summary:
{summary}

Generate exactly {num_questions} interview questions. Format each question on a new line, numbered 1-{num_questions}. Do not add any other text or explanations."""

        # Call OpenRouter API with Llama 3.3 70B
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/your-repo',
                'X-Title': 'CV Interview Assistant'
            },
            json={
                'model': 'meta-llama/llama-3.3-70b-instruct:free',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert technical recruiter. Generate interview questions based on the candidate\'s CV. Be specific and relevant.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            questions_text = result['choices'][0]['message']['content']
            
            st.success("✅ AI generated personalized questions from your CV!")
            
            # Parse questions from response
            questions = []
            lines = questions_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                # Match patterns like "1.", "1)", "Q1:", "Question 1:", etc.
                if re.match(r'^(question\s+)?[\d]+[\.\):]?\s+', line, re.IGNORECASE):
                    # Remove the number prefix
                    question = re.sub(r'^(question\s+)?[\d]+[\.\):]?\s+', '', line, flags=re.IGNORECASE).strip()
                    if question and len(question) > 10:
                        questions.append(question)
            
            # Ensure we have exactly num_questions
            if len(questions) >= num_questions:
                return questions[:num_questions]
            else:
                st.warning(f"AI generated only {len(questions)} questions. Adding fallback questions to reach {num_questions}.")
                # Add fallback questions to reach the target
                fallback = generate_questions_fallback(summary, num_questions)
                questions.extend(fallback[len(questions):])
                return questions[:num_questions]
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            st.info("Using fallback questions based on your CV content.")
            return generate_questions_fallback(summary, num_questions)
            
    except Exception as e:
        st.error(f"AI question generation failed: {str(e)}")
        st.info("Using fallback questions based on your CV content.")
        return generate_questions_fallback(summary, num_questions)

def generate_questions_fallback(summary, num_questions=4):
    """
    Fallback method to generate questions without AI - ALWAYS returns exactly num_questions
    """
    questions = []
    
    # Check what sections exist in the summary
    has_skills = "Skills" in summary or "Competencies" in summary
    has_experience = "Experience" in summary or "Professional" in summary
    has_projects = "Projects" in summary
    has_education = "Education" in summary
    
    # Extract specific technologies/skills mentioned
    tech_keywords = ['Python', 'Java', 'JavaScript', 'React', 'Node', 'AWS', 'Docker', 
                     'Kubernetes', 'DevOps', 'CI/CD', 'WebSocket', 'WebRTC', 'AI', 'ML']
    mentioned_tech = [tech for tech in tech_keywords if tech.lower() in summary.lower()]
    
    # Generate contextual questions
    if has_skills:
        if mentioned_tech:
            questions.append(f"Can you elaborate on your experience with {', '.join(mentioned_tech[:3])}?")
        else:
            questions.append("What are your strongest technical skills?")
    
    if has_experience or has_projects:
        questions.append("Can you describe your most impactful project and the challenges you overcame?")
    
    if has_projects:
        questions.append("What technologies did you use in your recent projects and why did you choose them?")
    
    if "cloud" in summary.lower() or "devops" in summary.lower():
        questions.append("What is your experience with cloud platforms and DevOps practices?")
    
    if has_education:
        questions.append("How has your educational background prepared you for this role?")
    
    # Add more generic questions to reach num_questions
    generic_questions = [
        "What motivates you in your work?",
        "How do you approach problem-solving in your projects?",
        "Can you describe a challenging situation you faced and how you resolved it?",
        "What are your career goals for the next few years?",
        "How do you stay updated with new technologies and industry trends?",
        "What makes you a good fit for this position?"
    ]
    
    # Add generic questions until we have enough
    for gq in generic_questions:
        if len(questions) >= num_questions:
            break
        if gq not in questions:
            questions.append(gq)
    
    # Ensure we always return exactly num_questions
    while len(questions) < num_questions:
        questions.append(f"Tell me more about your professional experience and skills.")
    
    return questions[:num_questions]

def chat_with_ai(message, cv_summary, conversation_history, api_key):
    """
    Interactive chat with AI interviewer about the CV
    """
    try:
        # Build conversation context
        system_prompt = f"""You are an experienced technical interviewer conducting an interview. 
You have reviewed the candidate's CV:

{cv_summary}

Your role is to:
- Ask insightful follow-up questions based on their responses
- Probe deeper into their technical experience
- Assess their problem-solving abilities
- Be professional but conversational
- Keep responses concise (2-3 sentences max)"""

        messages = [{'role': 'system', 'content': system_prompt}]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append(msg)
        
        # Add current message
        messages.append({'role': 'user', 'content': message})
        
        # Call Ollama API
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'meta-llama/llama-3.3-70b-instruct:free',
                'messages': messages
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return ai_response, None
        else:
            return None, f"API Error: {response.status_code}"
            
    except Exception as e:
        return None, f"Error: {str(e)}"

def tts_to_audio(text, api_key=None, speaker_wav=None, language="en"):
    """
    Use Google Text-to-Speech (gTTS) - No API key needed!
    Works reliably and sounds natural
    """
    try:
        # Clean text for TTS (remove markdown formatting)
        clean_text = text.replace("**", "").replace("*", "").replace("-", "").replace("•", "").strip()
        clean_text = re.sub(r'##\s+[^\n]+', '', clean_text)  # Remove markdown headers
        clean_text = re.sub(r'[🎯💼🚀🎓🌐📜👤📄⚠️💡✅❓]', '', clean_text)  # Remove emojis
        
        # Limit text length
        if len(clean_text) > 500:
            clean_text = clean_text[:500]
            last_period = clean_text.rfind('.')
            if last_period > 100:
                clean_text = clean_text[:last_period + 1]
        
        # Remove newlines and extra spaces
        clean_text = " ".join(clean_text.split())
        
        if not clean_text or len(clean_text) < 10:
            return None, "Text too short for TTS"
        
        # Generate speech using Google TTS
        tts = gTTS(text=clean_text, lang='en', slow=False)
        
        # Save to BytesIO object
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        return audio_fp.read(), None
        
    except ImportError:
        return None, "gTTS library not installed. Run: pip install gtts"
    except Exception as e:
        return None, f"TTS Error: {str(e)}"

def speech_to_text():
    """
    Convert speech to text using speech_recognition library
    """
    try:
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            
        st.info("Processing your speech...")
        text = recognizer.recognize_google(audio)
        return text, None
        
    except sr.WaitTimeoutError:
        return None, "No speech detected. Please try again."
    except sr.UnknownValueError:
        return None, "Could not understand audio. Please speak clearly."
    except sr.RequestError as e:
        return None, f"Speech recognition service error: {e}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def main():
    st.set_page_config(page_title="CV Analyzer", layout="wide")
    
    st.title("🎯 AI Interview Assistant")
    st.markdown("Upload your CV and experience an AI-powered interview with personalized evaluation.")
    
    # Auto-enable all features (no sidebar)
    enable_ai = True
    ollama_api_key = "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"
    show_raw_text = False
    enable_tts = True
    tts_enabled = True
    speaker_wav = None
    
    # Main content
    uploaded_file = st.file_uploader("Choose your CV file", type=["pdf", "docx"])
    
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        # Extract text
        file_bytes = uploaded_file.read()
        if uploaded_file.name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)
        elif uploaded_file.name.lower().endswith(".docx"):
            text = extract_text_from_docx(file_bytes)
        else:
            text = "Unsupported file type."
        
        # Show raw text if requested
        if show_raw_text:
            with st.expander("Extracted Text", expanded=False):
                st.text_area("Raw CV Text", text, height=300)
        
        # Generate and display summary
        st.markdown("---")
        st.subheader("CV Summary")
        
        with st.spinner("Analyzing your CV..."):
            summary = summarize_cv(text)
        
        st.markdown(summary)
        
        # Audio for summary
        if tts_enabled and summary:
            with st.expander("Listen to Summary", expanded=False):
                with st.spinner("Generating audio..."):
                    audio_bytes, error = tts_to_audio(summary)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/wav")
                    else:
                        if error:
                            st.warning(f"Warning: {error}")
                        else:
                            st.info("TTS is optional. You can still read the summary below.")
        
        # Generate and display questions
        st.markdown("---")
        st.subheader("Interview Questions")
        
        # Use AI to generate questions if enabled
        if enable_ai and ollama_api_key:
            with st.spinner("AI is generating personalized interview questions..."):
                questions = generate_questions_with_ai(summary, ollama_api_key)
        else:
            questions = generate_questions_fallback(summary)
        
        for i, q in enumerate(questions, 1):
            with st.container():
                st.markdown(f"**Q{i}: {q}**")
                if tts_enabled:
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.button(f"Play", key=f"q_{i}"):
                            with st.spinner("Generating audio..."):
                                q_audio, q_error = tts_to_audio(q)
                                if q_audio:
                                    st.audio(q_audio, format="audio/wav")
                                else:
                                    if q_error:
                                        st.warning(f"Warning: {q_error}")
                st.markdown("")
        
        # Conversational AI Interview with Speech-to-Text
        if enable_ai and ollama_api_key:
            st.markdown("---")
            st.subheader("🎙️ AI Interview Session")
            
            # Initialize session state for automatic interview
            if 'interview_started' not in st.session_state:
                st.session_state.interview_started = False
            if 'current_question_index' not in st.session_state:
                st.session_state.current_question_index = 0
            if 'interview_questions' not in st.session_state:
                st.session_state.interview_questions = questions
            if 'interview_conversation' not in st.session_state:
                st.session_state.interview_conversation = []
            if 'interview_complete' not in st.session_state:
                st.session_state.interview_complete = False
            if 'waiting_for_answer' not in st.session_state:
                st.session_state.waiting_for_answer = False
            if 'play_audio_on_load' not in st.session_state:
                st.session_state.play_audio_on_load = False
            if 'pending_transition_audio' not in st.session_state:
                st.session_state.pending_transition_audio = None
            
            # Start button
            if not st.session_state.interview_started:
                st.markdown("**Ready to begin your interview?**")
                st.info("Click the button below to start a conversational interview with the AI recruiter.")
                
                if st.button("🚀 Start Interview", type="primary", key="start_interview"):
                    st.session_state.interview_started = True
                    
                    # Add welcome message
                    welcome_msg = "Hello! Welcome to the interview. I'm excited to learn more about your background and experience. Let's begin with the first question."
                    st.session_state.interview_conversation.append({
                        'type': 'ai',
                        'message': welcome_msg
                    })
                    
                    # Add first question
                    first_question = st.session_state.interview_questions[0]
                    st.session_state.interview_conversation.append({
                        'type': 'ai',
                        'message': first_question
                    })
                    
                    st.session_state.waiting_for_answer = True
                    st.rerun()
            
            # Interview in progress
            if st.session_state.interview_started and not st.session_state.interview_complete:
                # Minimal CSS
                st.markdown("""
                <style>
                .interview-box {
                    padding: 30px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }
                .question-num {
                    font-size: 14px;
                    color: #666;
                    margin-bottom: 15px;
                }
                .question-display {
                    font-size: 20px;
                    color: #333;
                    margin: 20px 0;
                    font-weight: 500;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Display conversation history (minimal)
                for i, msg in enumerate(st.session_state.interview_conversation):
                    if msg['type'] == 'ai':
                        st.markdown(f"**AI:** {msg['message']}")
                    else:
                        st.markdown(f"**You:** {msg['message']}")
                    st.markdown("")
                
                # Check if waiting for answer
                if st.session_state.waiting_for_answer:
                    st.markdown("---")
                    
                    # Get current question
                    current_question = st.session_state.interview_questions[st.session_state.current_question_index]
                    
                    # Display question
                    st.markdown(f"""
                    <div class="interview-box">
                        <div class="question-num">Question {st.session_state.current_question_index + 1} of 4</div>
                        <div class="question-display">{current_question}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Auto-play audio for questions
                    if st.session_state.pending_transition_audio:
                        # Play transition message first, then question
                        transition_msg = st.session_state.pending_transition_audio
                        combined_msg = f"{transition_msg} {current_question}"
                        audio_bytes, _ = tts_to_audio(combined_msg)
                        if audio_bytes:
                            import base64
                            audio_base64 = base64.b64encode(audio_bytes).decode()
                            st.markdown(f"""
                            <audio autoplay>
                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            </audio>
                            """, unsafe_allow_html=True)
                        st.session_state.pending_transition_audio = None
                        st.session_state.play_audio_on_load = False
                    elif st.session_state.play_audio_on_load:
                        # Play audio for current question after page reload
                        audio_bytes, _ = tts_to_audio(current_question)
                        if audio_bytes:
                            import base64
                            audio_base64 = base64.b64encode(audio_bytes).decode()
                            st.markdown(f"""
                            <audio autoplay>
                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            </audio>
                            """, unsafe_allow_html=True)
                        st.session_state.play_audio_on_load = False
                    elif len(st.session_state.interview_conversation) == 2 and st.session_state.current_question_index == 0:
                        # First question - play welcome + question
                        welcome_msg = st.session_state.interview_conversation[0]['message']
                        combined_msg = f"{welcome_msg} {current_question}"
                        audio_bytes, _ = tts_to_audio(combined_msg)
                        if audio_bytes:
                            import base64
                            audio_base64 = base64.b64encode(audio_bytes).decode()
                            st.markdown(f"""
                            <audio autoplay>
                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            </audio>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("### Choose how to answer:")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**✍️ Type Your Answer**")
                        text_answer = st.text_area(
                            "Your response:",
                            key=f"text_answer_{st.session_state.current_question_index}",
                            height=120,
                            placeholder="Type your answer here..."
                        )
                        
                        if st.button("Submit Answer", key=f"submit_text_{st.session_state.current_question_index}", type="primary"):
                            if text_answer.strip():
                                # Process answer
                                st.session_state.interview_conversation.append({
                                    'type': 'user',
                                    'message': text_answer
                                })
                                
                                st.session_state.current_question_index += 1
                                
                                # Check if more questions (must be less than 4 AND within array bounds)
                                if st.session_state.current_question_index < 4 and st.session_state.current_question_index < len(st.session_state.interview_questions):
                                    st.session_state.waiting_for_answer = True
                                    transition_messages = [
                                        "Great answer! Let me ask you the next question.",
                                        "Excellent response! Moving on to the next question.",
                                        "Thank you for sharing that. Here's my next question.",
                                        "Nice response! Let's continue."
                                    ]
                                    msg_index = min(st.session_state.current_question_index - 1, len(transition_messages) - 1)
                                    transition_msg = transition_messages[msg_index]
                                    
                                    st.session_state.interview_conversation.append({
                                        'type': 'ai',
                                        'message': transition_msg
                                    })
                                    
                                    # Add next question - with bounds check
                                    next_question = st.session_state.interview_questions[st.session_state.current_question_index]
                                    st.session_state.interview_conversation.append({
                                        'type': 'ai',
                                        'message': next_question
                                    })
                                    
                                    # Store transition message to play with question
                                    st.session_state.pending_transition_audio = transition_msg
                                    st.session_state.play_audio_on_load = True
                                else:
                                    # Interview complete
                                    st.session_state.waiting_for_answer = False
                                    closing_msg = "Thank you for your time! That concludes our interview."
                                    st.session_state.interview_conversation.append({
                                        'type': 'ai',
                                        'message': closing_msg
                                    })
                                    
                                    audio_bytes, _ = tts_to_audio(closing_msg)
                                    if audio_bytes:
                                        import base64
                                        audio_base64 = base64.b64encode(audio_bytes).decode()
                                        st.markdown(f"""
                                        <audio autoplay>
                                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                                        </audio>
                                        """, unsafe_allow_html=True)
                                    
                                    st.session_state.interview_complete = True
                                
                                st.rerun()
                            else:
                                st.warning("Please provide an answer.")
                    
                    with col2:
                        st.markdown("**🎤 Use Voice**")
                        st.info("Click to record your answer")
                        
                        if st.button("🎙️ Record Answer", key=f"record_{st.session_state.current_question_index}"):
                            with st.spinner("🎤 Listening..."):
                                speech_text, error = speech_to_text()
                                
                                if speech_text:
                                    st.success(f"✅ Recorded: {speech_text}")
                                    
                                    # Process answer
                                    st.session_state.interview_conversation.append({
                                        'type': 'user',
                                        'message': speech_text
                                    })
                                    
                                    st.session_state.current_question_index += 1
                                    
                                    # Check if more questions (must be less than 4 AND within array bounds)
                                    if st.session_state.current_question_index < 4 and st.session_state.current_question_index < len(st.session_state.interview_questions):
                                        st.session_state.waiting_for_answer = True
                                        transition_messages = [
                                            "Great answer! Let me ask you the next question.",
                                            "Excellent response! Moving on to the next question.",
                                            "Thank you for sharing that. Here's my next question.",
                                            "Nice response! Let's continue."
                                        ]
                                        msg_index = min(st.session_state.current_question_index - 1, len(transition_messages) - 1)
                                        transition_msg = transition_messages[msg_index]
                                        
                                        st.session_state.interview_conversation.append({
                                            'type': 'ai',
                                            'message': transition_msg
                                        })
                                        
                                        # Add next question - with bounds check
                                        next_question = st.session_state.interview_questions[st.session_state.current_question_index]
                                        st.session_state.interview_conversation.append({
                                            'type': 'ai',
                                            'message': next_question
                                        })
                                        
                                        # Store transition message to play with question
                                        st.session_state.pending_transition_audio = transition_msg
                                        st.session_state.play_audio_on_load = True
                                    else:
                                        # Interview complete
                                        st.session_state.waiting_for_answer = False
                                        closing_msg = "Thank you for your time! That concludes our interview."
                                        st.session_state.interview_conversation.append({
                                            'type': 'ai',
                                            'message': closing_msg
                                        })
                                        
                                        audio_bytes, _ = tts_to_audio(closing_msg)
                                        if audio_bytes:
                                            import base64
                                            audio_base64 = base64.b64encode(audio_bytes).decode()
                                            st.markdown(f"""
                                            <audio autoplay>
                                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                                            </audio>
                                            """, unsafe_allow_html=True)
                                        
                                        st.session_state.interview_complete = True
                                    
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Could not hear you. Error: {error}")
            
            # Interview complete
            elif st.session_state.interview_complete:
                st.success("🎉 Interview Complete!")
                
                # Generate score if not already generated
                if 'interview_score' not in st.session_state:
                    with st.spinner("Evaluating your responses..."):
                        # Prepare conversation for scoring
                        user_responses = []
                        for msg in st.session_state.interview_conversation:
                            if msg['type'] == 'user':
                                user_responses.append(msg['message'])
                        
                        # Call AI to score the interview
                        score_prompt = f"""You are an experienced technical recruiter evaluating a candidate's interview performance.

Interview Questions and Candidate's Responses:
"""
                        for i, (question, response) in enumerate(zip(st.session_state.interview_questions, user_responses), 1):
                            score_prompt += f"\nQuestion {i}: {question}\nCandidate's Response: {response}\n"
                        
                        score_prompt += """
Based on the candidate's responses, evaluate their performance on the following criteria:
1. Technical knowledge and expertise
2. Communication skills and clarity
3. Problem-solving abilities
4. Relevance and depth of answers
5. Overall professionalism

Provide a score from 0 to 10 (where 10 is excellent) and a brief 2-3 sentence feedback explaining the score.

Format your response EXACTLY as:
SCORE: [number from 0-10]
FEEDBACK: [your 2-3 sentence feedback]"""

                        try:
                            response = requests.post(
                                'https://openrouter.ai/api/v1/chat/completions',
                                headers={
                                    'Authorization': f'Bearer {ollama_api_key}',
                                    'Content-Type': 'application/json'
                                },
                                json={
                                    'model': 'meta-llama/llama-3.3-70b-instruct:free',
                                    'messages': [
                                        {
                                            'role': 'system',
                                            'content': 'You are an expert technical recruiter evaluating interview performance. Be fair but constructive in your evaluation.'
                                        },
                                        {
                                            'role': 'user',
                                            'content': score_prompt
                                        }
                                    ],
                                    'temperature': 0.3,
                                    'max_tokens': 300
                                },
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                ai_evaluation = result['choices'][0]['message']['content']
                                
                                # Parse score and feedback
                                score_match = re.search(r'SCORE:\s*(\d+(?:\.\d+)?)', ai_evaluation, re.IGNORECASE)
                                feedback_match = re.search(r'FEEDBACK:\s*(.+)', ai_evaluation, re.IGNORECASE | re.DOTALL)
                                
                                if score_match:
                                    score = float(score_match.group(1))
                                    score = min(10, max(0, score))  # Ensure score is between 0-10
                                else:
                                    score = 7.0  # Default score if parsing fails
                                
                                if feedback_match:
                                    feedback = feedback_match.group(1).strip()
                                else:
                                    feedback = "Good effort in the interview. Keep practicing to improve your responses."
                                
                                st.session_state.interview_score = score
                                st.session_state.interview_feedback = feedback
                            else:
                                # Fallback scoring
                                st.session_state.interview_score = 7.0
                                st.session_state.interview_feedback = "Thank you for completing the interview. Your responses showed good understanding of the topics discussed."
                        except Exception as e:
                            # Fallback scoring
                            st.session_state.interview_score = 7.0
                            st.session_state.interview_feedback = "Thank you for completing the interview. Your responses showed good understanding of the topics discussed."
                
                # Display score
                st.markdown("---")
                st.markdown("### 📊 Interview Evaluation")
                
                score = st.session_state.interview_score
                feedback = st.session_state.interview_feedback
                
                # Color code based on score
                if score >= 8:
                    score_color = "#28a745"  # Green
                    score_emoji = "🌟"
                    score_label = "Excellent"
                elif score >= 6:
                    score_color = "#ffc107"  # Yellow
                    score_emoji = "👍"
                    score_label = "Good"
                else:
                    score_color = "#dc3545"  # Red
                    score_emoji = "💪"
                    score_label = "Needs Improvement"
                
                st.markdown(f"""
                <div style="padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; text-align: center; margin: 20px 0;">
                    <h1 style="color: white; font-size: 72px; margin: 0;">{score_emoji}</h1>
                    <h2 style="color: white; margin: 10px 0;">Your Score</h2>
                    <h1 style="color: {score_color}; font-size: 64px; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{score:.1f}/10</h1>
                    <h3 style="color: white; margin: 10px 0;">{score_label}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**Feedback:**")
                st.info(feedback)
                
                st.markdown("---")
                st.markdown("### 📝 Interview Transcript")
                
                # Display full conversation (minimal)
                for msg in st.session_state.interview_conversation:
                    if msg['type'] == 'ai':
                        st.markdown(f"**AI:** {msg['message']}")
                    else:
                        st.markdown(f"**You:** {msg['message']}")
                    st.markdown("")
                
                st.markdown("---")
                
                # Voice recording section
                st.markdown("### 🎤 Additional Voice Recording")
                st.info("Click the button below to record additional comments or feedback")
                
                if 'additional_recordings' not in st.session_state:
                    st.session_state.additional_recordings = []
                
                # Display previous recordings
                if st.session_state.additional_recordings:
                    st.markdown("**Previous Recordings:**")
                    for idx, recording in enumerate(st.session_state.additional_recordings, 1):
                        st.markdown(f"**Recording {idx}:** {recording}")
                        st.markdown("")
                
                # Record button
                if st.button("🎙️ Record Voice", type="primary", key="record_additional"):
                    with st.spinner("🎤 Listening... Speak now!"):
                        speech_text, error = speech_to_text()
                        
                        if speech_text:
                            st.session_state.additional_recordings.append(speech_text)
                            st.success(f"✅ Recorded: {speech_text}")
                            st.rerun()
                        else:
                            st.error(f"❌ Could not hear you. Error: {error}")
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Create transcript for download
                    transcript = "INTERVIEW TRANSCRIPT\n" + "="*50 + "\n\n"
                    
                    # Add score to transcript
                    transcript += f"INTERVIEW SCORE: {st.session_state.interview_score:.1f}/10\n"
                    transcript += f"FEEDBACK: {st.session_state.interview_feedback}\n\n"
                    transcript += "="*50 + "\n\n"
                    
                    for msg in st.session_state.interview_conversation:
                        if msg['type'] == 'ai':
                            transcript += f"AI RECRUITER: {msg['message']}\n\n"
                        else:
                            transcript += f"YOU: {msg['message']}\n\n"
                    
                    # Add additional recordings
                    if st.session_state.additional_recordings:
                        transcript += "\n" + "="*50 + "\n"
                        transcript += "ADDITIONAL VOICE RECORDINGS\n" + "="*50 + "\n\n"
                        for idx, recording in enumerate(st.session_state.additional_recordings, 1):
                            transcript += f"Recording {idx}: {recording}\n\n"
                    
                    st.download_button(
                        label="📥 Download Transcript",
                        data=transcript,
                        file_name="interview_transcript.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    if st.session_state.additional_recordings:
                        if st.button("🗑️ Clear Recordings"):
                            st.session_state.additional_recordings = []
                            st.rerun()
        
        # Download summary option
        st.markdown("---")
        st.download_button(
            label="Download Summary",
            data=summary,
            file_name="cv_summary.txt",
            mime="text/plain"
        )
    else:
        st.info("Please upload a CV file (PDF or DOCX) to begin analysis.")
        
        # Show example
        with st.expander("How it works"):
            st.markdown("""
            1. **Upload** your CV in PDF or DOCX format
            2. The app **extracts** and **analyzes** your CV content
            3. Get a **structured summary** of your skills, experience, projects, and education
            4. Receive **personalized interview questions** based on your CV
            5. **Listen** to the summary and questions with text-to-speech (optional)
            
            **Tips for best results:**
            - Use a well-structured CV with clear section headers (Skills, Experience, Education, etc.)
            - Ensure your CV is in a standard format
            - Add your Hugging Face API key in the sidebar for audio features
            """)

if __name__ == "__main__":
    main()
