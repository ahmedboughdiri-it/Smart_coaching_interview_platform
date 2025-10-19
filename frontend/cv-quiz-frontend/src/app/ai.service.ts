import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AiService {
  private baseUrl = 'http://localhost:5000'; // your Python backend

  constructor(private http: HttpClient) {}

  getNextQuestion(state: any): Observable<any> {
    // state could be previous answers, user info, etc.
    return this.http.post(`${this.baseUrl}/next_question`, state);
  }

  submitAnswer(answer: string, context: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/submit_answer`, { answer, context });
  }
}
