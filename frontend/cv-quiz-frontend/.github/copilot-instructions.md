<!-- .github/copilot-instructions.md - Guidance for AI coding agents working on this repo -->
# CvQuizFrontend — Copilot Instructions

This file contains concise, actionable information to help AI coding agents be immediately productive in this Angular frontend.

1) Big picture
- This is a small Angular 16 single-page frontend live at `src/` that communicates with two backend services:
  - Quiz API (expected at `http://localhost:5000`) — endpoints used in `src/app/quiz.service.ts`:
    - POST `/generate-quiz` accepts FormData (`file` or `text`) and returns { quiz_id, questions }
    - POST `/submit-quiz` accepts JSON { quiz_id, answers } and returns score/result
  - Analysis API (expected at `http://127.0.0.1:8000`) — used in `src/app/front/front.component.ts`:
    - POST `/analyze_video` with FormData `file` -> facial/visual analysis
    - POST `/transcribe_audio` with FormData `file` -> { transcription }

2) Where to look for patterns and examples
- `src/app/quiz.service.ts` — canonical example of how this app does HTTP calls, uses `FormData`, and the single `base` URL field to switch backends.
- `src/app/quiz/quiz.component.ts` — shows UI flow: file selection -> call `generateQuizFromFile` -> populate `questions` and `quizId` -> build `answers` array of shape [{id, answer}] for `submitQuiz`.
- `src/app/front/front.component.ts` — demonstrates MediaRecorder usage, chunked recording -> build `Blob` -> send as `video/mp4` FormData to analysis endpoints and update UI inside `NgZone`.
- `src/app/app.module.ts` — shows required imports: `HttpClientModule` and `FormsModule` (add new services/modules here if needed).

3) Build / test / debug workflows (concrete commands)
- Start dev server (hot reload): `npm start` (runs `ng serve`); dev server listens on http://localhost:4200 by default.
- Build for production: `npm run build` (runs `ng build`). Output goes to `dist/cv-quiz-frontend/` as configured in `angular.json`.
- Run unit tests: `npm test` (Karma/Jasmine). Tests live alongside components (`*.spec.ts`).
- Typical debug steps: run `npm start`, open Chrome DevTools → Console & Network. Look for CORS or connection errors to `localhost:5000` or `127.0.0.1:8000` and update `QuizService.base` or start the appropriate backend.

4) Project-specific conventions
- Service base URL is hard-coded in `QuizService.base` (edit it to point to staging or env-specific address). No environment.ts wiring is present.
- File uploads always use `FormData` and a field named `file` (or `text` for text-based generation). Keep that exact naming when implementing new endpoints.
- Questions returned from the backend are used directly in the template; each question must contain an `id` property — the client maps them to answers using `questions.map(q => ({ id: q.id, answer }))`.
- UI state use: components keep local state (`selectedFile`, `questions`, `userAnswers`, `quizId`, `result`) — prefer modifying these in-place rather than introducing global state for small changes.

5) Integration & Cross-component notes
- Two different backend hosts are used in the codebase: `http://localhost:5000` (quiz endpoints) and `http://127.0.0.1:8000` (video/audio analysis). Both must be running during end-to-end manual tests.
- CORS: backend must allow `http://localhost:4200` or disable CORS in dev. If you see HTTP 0 or blocked requests, check backend CORS and proxy config.

6) Quick code examples to follow
- To call the quiz generation endpoint (see `quiz.service.ts`):
  const form = new FormData();
  form.append('file', file, file.name);
  http.post(`${this.base}/generate-quiz`, form)

- To build answers for submission (see `quiz.component.ts`):
  const answers = questions.map(q => ({ id: q.id, answer: userAnswers[q.id] ?? "" }));

7) Small contract & edge-cases worth knowing
- Inputs: `generate-quiz` accepts `file` (binary) or `text` (string in FormData).
- Outputs: `generate-quiz` returns at least `{ quiz_id: string, questions: Array<{id: string, ...}> }`. `submit-quiz` accepts `{ quiz_id, answers }` and returns result object (shape is backend-defined).
- Edge cases to handle in PRs: missing `quiz_id`, questions without `id`, network errors (show `error` state in components), large files (MediaRecorder blob size), and incompatible video mime types.

8) Where to add work and tests
- Add new UI features under `src/app/` with matching component folder and `*.spec.ts` tests.
- Update `app.module.ts` to register new modules (e.g., ReactiveFormsModule) and import them in components.

9) Notes for maintainers / what AI should NOT change
- Do not change the two hard-coded backend URLs silently; prefer making them configurable via an `environment.ts` change and document it.
- Keep `FormData` field names (`file`, `text`) stable unless backend changes.

If anything in this file is unclear or incomplete, tell me which area you'd like expanded (API shapes, test strategy, environment wiring) and I will update the guidance.
