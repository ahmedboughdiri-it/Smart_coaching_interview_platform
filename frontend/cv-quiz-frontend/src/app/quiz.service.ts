import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class QuizService {
  base = 'http://localhost:5000'; // adapter si nécessaire

  constructor(private http: HttpClient) {}

  generateQuizFromFile(file: File): Observable<any> {
    const form = new FormData();
    form.append('file', file, file.name);
    return this.http.post(`${this.base}/generate-quiz`, form);
  }

  generateQuizFromText(text: string): Observable<any> {
    const form = new FormData();
    form.append('text', text);
    return this.http.post(`${this.base}/generate-quiz`, form);
  }

  submitQuiz(quizId: string, answers: any[]): Observable<any> {
    return this.http.post(`${this.base}/submit-quiz`, { quiz_id: quizId, answers });
  }
}
