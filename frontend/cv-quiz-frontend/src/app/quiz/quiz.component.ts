import { Component } from '@angular/core';
import { QuizService } from '../quiz.service';

@Component({
  selector: 'app-quiz',
  templateUrl: './quiz.component.html'
})
export class QuizComponent {
  selectedFile: File | null = null;
  quizId: string | null = null;
  questions: any[] = [];
  userAnswers: { [qid: string]: any } = {};
  result: any = null;
  loading = false;
  error: string | null = null;
j: any;
  constructor(private quizService: QuizService) {}

  onFileSelected(event: any) {
    const f = event.target.files[0];
    if (f) this.selectedFile = f;
  }

  uploadAndGenerate() {
    if (!this.selectedFile) { this.error = 'Select a file first'; return; }
    this.loading = true;
    this.quizService.generateQuizFromFile(this.selectedFile).subscribe({
      next: (res) => {
        this.quizId = res.quiz_id;
        this.questions = res.questions;
        this.userAnswers = {};
        this.result = null;
        this.loading = false;
      },
      error: (err) => {
        this.error = err?.error?.error || 'Erreur lors de la génération';
        this.loading = false;
      }
    });
  }

  // also optionally generate from raw text
  generateFromText(text: string) {
    this.loading = true;
    this.quizService.generateQuizFromText(text).subscribe({
      next: (res) => {
        this.quizId = res.quiz_id;
        this.questions = res.questions;
        this.userAnswers = {};
        this.result = null;
        this.loading = false;
      },
      error: (err) => { this.error = 'Erreur'; this.loading = false; }
    });
  }

  submit() {
    if (!this.quizId) return;
    // build answers array
    const answers = this.questions.map(q => {
      return { id: q.id, answer: this.userAnswers[q.id] ?? "" };
    });
    this.quizService.submitQuiz(this.quizId, answers).subscribe({
      next: (res) => { this.result = res; },
      error: (err) => { this.error = 'Erreur lors de la soumission'; }
    })
  }
}
