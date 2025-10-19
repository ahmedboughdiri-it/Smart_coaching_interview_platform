import { Component, NgZone } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-front',
  templateUrl: './front.component.html',
  styleUrls: ['./front.component.css']
})
export class FrontComponent {
  private mediaRecorder: any;
  private recordedChunks: any[] = [];
  public recording = false;

  public facialResult: any = null;
  public transcriptionResult: string = '';

  // --- CV Variables ---
  public cvSummary: string = '';
  public generatedQuestions: string[] = [];
  public currentQuestionIndex = 0;
  public currentQuestion: string | null = null;
  public cvUploading = false;
  public interviewFinished = false;

  // --- TTS State ---
  public questionPlaying = false;

  // --- Feedback State ---
  public feedbackText: string | null = null;
  public feedbackLoading = false;
  public feedbackPlaying = false;

  constructor(private http: HttpClient, private zone: NgZone) {}

  // --- Upload CV + Generate Questions ---
  onCVSelected(event: any) {
    const file: File = event.target.files[0];
    if (!file) return;

    this.cvUploading = true;
    const formData = new FormData();
    formData.append('file', file, file.name);

    // Step 1: Summarize CV
    this.http.post<any>('http://127.0.0.1:8000/summarize_cv', formData)
      .subscribe({
        next: (res) => {
          this.cvSummary = res.summary || '';

          // Step 2: Generate AI Questions
          const questionsForm = new FormData();
          questionsForm.append('summary', this.cvSummary);
          // NOTE: keep API keys secure - this example uses the value you provided earlier
          questionsForm.append('api_key', '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');
          questionsForm.append('num_questions', '4');

          this.http.post('http://127.0.0.1:8000/generate_questions', questionsForm)
            .subscribe({
              next: (qRes: any) => {
                this.generatedQuestions = qRes.questions || [];
                this.currentQuestionIndex = 0;
                this.currentQuestion = this.generatedQuestions[0];
                this.cvUploading = false;
                this.interviewFinished = false;

                // Automatically play first AI-generated question
                if (this.generatedQuestions.length > 0) {
                  this.playCurrentQuestion();
                }
              },
              error: err => {
                console.error(err);
                this.generatedQuestions = ['Error generating questions'];
                this.cvUploading = false;
              }
            });
        },
        error: (err) => {
          console.error(err);
          this.cvSummary = 'Error summarizing CV';
          this.cvUploading = false;
        }
      });
  }

  // --- Play Question via TTS ---
  playCurrentQuestion() {
    if (!this.generatedQuestions || this.currentQuestionIndex >= this.generatedQuestions.length) return;

    this.currentQuestion = this.generatedQuestions[this.currentQuestionIndex];

    const formData = new FormData();
    formData.append('text', this.currentQuestion);

    this.questionPlaying = true;

    this.http.post('http://127.0.0.1:8000/text_to_speech', formData, { responseType: 'blob' })
      .subscribe({
        next: (res: Blob) => {
          const url = URL.createObjectURL(res);
          const audio = new Audio(url);
          audio.play();

          audio.onended = () => {
            this.questionPlaying = false;
            this.startRecording(); // Auto-start recording after TTS
          };
        },
        error: err => {
          console.error(err);
          this.questionPlaying = false;
          this.startRecording(); // fallback: start recording even if TTS fails
        }
      });
  }

  // --- Recording Logic ---
  async startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    const videoElement = document.getElementById('preview') as HTMLVideoElement;
    videoElement.srcObject = stream;
    try { videoElement.play(); } catch (e) { /* ignore autoplay blocking in some browsers */ }

    this.recordedChunks = [];
    this.mediaRecorder = new MediaRecorder(stream);

    this.mediaRecorder.ondataavailable = (event: any) => {
      if (event.data && event.data.size > 0) this.recordedChunks.push(event.data);
    };

    this.mediaRecorder.start();
    this.recording = true;

    // Reset results for current question
    this.facialResult = null;
    this.transcriptionResult = '';
    this.feedbackText = null;
  }

  stopRecording() {
    if (!this.mediaRecorder) return;

    this.mediaRecorder.stop();
    this.recording = false;

    this.mediaRecorder.onstop = () => {
      const blob = new Blob(this.recordedChunks, { type: 'video/mp4' });
      const videoFormData = new FormData();
      videoFormData.append('file', blob, 'interview.mp4');

      this.zone.run(() => {
        // Step 1: Analyze Facial Emotion
        this.http.post('http://127.0.0.1:8000/analyze_video', videoFormData)
          .subscribe({
            next: (res: any) => {
              this.facialResult = res;

              // Step 2: Transcribe Audio
              const audioFormData = new FormData();
              audioFormData.append('file', blob, 'interview.mp4');

              this.http.post('http://127.0.0.1:8000/transcribe_audio', audioFormData)
                .subscribe({
                  next: (audioRes: any) => {
                    this.transcriptionResult = audioRes.transcription || '';

                    // After both results are available, request feedback
                    this.requestFeedback();
                  },
                  error: err => {
                    console.error(err);
                    this.transcriptionResult = 'Error transcribing audio';

                    // still attempt feedback with what we have
                    this.requestFeedback();
                  }
                });
            },
            error: err => {
              console.error(err);
              this.facialResult = 'Error analyzing video';

              // proceed to transcription anyway
              const audioFormData = new FormData();
              audioFormData.append('file', blob, 'interview.mp4');

              this.http.post('http://127.0.0.1:8000/transcribe_audio', audioFormData)
                .subscribe({
                  next: (audioRes: any) => {
                    this.transcriptionResult = audioRes.transcription || '';
                    this.requestFeedback();
                  },
                  error: audioErr => {
                    console.error(audioErr);
                    this.transcriptionResult = 'Error transcribing audio';
                    this.requestFeedback();
                  }
                });
            }
          });
      });
    };
  }

  // --- Generate and Play Feedback ---
  private requestFeedback() {
    this.feedbackLoading = true;
    this.feedbackText = null;

    const fd = new FormData();
    fd.append('summary', this.transcriptionResult || '');
    try {
      fd.append('facial', typeof this.facialResult === 'string' ? this.facialResult : JSON.stringify(this.facialResult || {}));
    } catch (e) {
      fd.append('facial', '');
    }

    this.http.post<any>('http://127.0.0.1:8000/generate_feedback', fd)
      .subscribe({
        next: (res) => {
          this.feedbackText = res?.feedback || this.clientSideFeedbackFallback();
          this.feedbackLoading = false;

          // Auto-play the feedback
          if (this.feedbackText) {
            this.playFeedback();
          }
        },
        error: err => {
          console.error('Feedback generation error:', err);
          // Use client-side fallback
          this.feedbackText = this.clientSideFeedbackFallback();
          this.feedbackLoading = false;

          if (this.feedbackText) {
            this.playFeedback();
          }
        }
      });
  }

  public playFeedback() {
    if (!this.feedbackText) return;

    this.feedbackPlaying = true;

    const ttsForm = new FormData();
    ttsForm.append('text', this.feedbackText);

    this.http.post('http://127.0.0.1:8000/text_to_speech', ttsForm, { responseType: 'blob' })
      .subscribe({
        next: (res: Blob) => {
          const url = URL.createObjectURL(res);
          const audio = new Audio(url);
          audio.play();

          audio.onended = () => {
            this.feedbackPlaying = false;
          };
        },
        error: err => {
          console.error('Feedback TTS error:', err);
          this.feedbackPlaying = false;

          // If TTS failed, try Web Speech API as a last-resort client-side fallback
          //this.playFeedbackWithWebSpeech(this.feedbackText);
        }
      });
  }

  private playFeedbackWithWebSpeech(text: string) {
    const synth = (window as any).speechSynthesis;
    if (!synth) return;
    try {
      const utter = new SpeechSynthesisUtterance(text);
      utter.onend = () => {
        this.feedbackPlaying = false;
      };
      synth.speak(utter);
      this.feedbackPlaying = true;
    } catch (e) {
      console.error('Web Speech API failed:', e);
      this.feedbackPlaying = false;
    }
  }

  // Provide a small, deterministic client-side feedback if backend fails
  private clientSideFeedbackFallback(): string {
    let feedback = '';

    // Facial heuristics (adjust based on your backend's actual shape)
    if (this.facialResult && typeof this.facialResult === 'object') {
      if ('dominant_emotion' in this.facialResult) {
        feedback += `I detected a ${this.facialResult.dominant_emotion} expression. `;
      } else {
        const keys = Object.keys(this.facialResult || {});
        if (keys.length > 0) {
          feedback += `Facial analysis detected: ${keys.join(', ')}. `;
        }
      }
    } else if (typeof this.facialResult === 'string' && this.facialResult.startsWith('Error')) {
      feedback += 'Facial analysis was not available. ';
    }

    const words = (this.transcriptionResult || '').split(/\s+/).filter(Boolean).length;
    if (words === 0) {
      feedback += 'No speech detected. Try speaking more clearly and a bit louder.';
    } else if (words < 20) {
      feedback += 'Your answer was short; consider expanding with a brief example or two.';
    } else {
      feedback += 'Good length. Try to structure your answer with problem, action and result.';
    }

    return feedback.trim();
  }

  // --- Next Question ---
  nextQuestion() {
    if (this.currentQuestionIndex < this.generatedQuestions.length - 1) {
      this.currentQuestionIndex++;
      this.currentQuestion = this.generatedQuestions[this.currentQuestionIndex];
      this.facialResult = null;
      this.transcriptionResult = '';
      this.feedbackText = null;

      // Automatically read next question
      this.playCurrentQuestion();
    } else {
      this.interviewFinished = true;
    }
  }
}