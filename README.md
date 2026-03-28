# NeuroLearn AI

Behavior-driven adaptive learning platform with:
- React + Zustand frontend
- FastAPI backend
- MongoDB persistence
- LLM integration (Groq/OpenAI-compatible endpoint support)

This repository is structured and configured for both local development and Vercel deployment.

## Project Structure

root/
- frontend/
- backend/
- vercel.json
- .gitignore
- README.md

## Environment Variables

### Backend
Set in backend/.env for local development or Vercel project environment variables:

- GROQ_API_KEY
- GROQ_MODEL
- GENAI_USE_LIVE
- MONGODB_URI
- MONGODB_DB

Use backend/.env.example as the template.

### Frontend
Set in frontend/.env:

- VITE_API_URL

Recommended default for full-stack Vercel and local proxy-based development:

- VITE_API_URL=/api

## Local Development

### 1) Backend

From backend/:

1. Install dependencies from requirements.txt
2. Start API server with Uvicorn using app.main:app

Default local API URL:

- http://127.0.0.1:8000

### 2) Frontend

From frontend/:

1. Install dependencies from package.json
2. Start Vite dev server

Vite is configured to proxy /api to http://127.0.0.1:8000, so VITE_API_URL=/api works locally.

## API Routes

Backend endpoints are exposed under /api:

- /api/health
- /api/auth/*
- /api/diagnostic/*
- /api/user/*
- /api/learning/*

## Vercel Deployment Notes

- backend/api/index.py is the serverless entrypoint and exports handler = Mangum(app).
- vercel.json rewrites /api/* to backend/api/index.py.
- Set backend environment variables in Vercel Project Settings.
- Build frontend as usual with Vite.

## Security and GitHub Readiness

- No secrets are committed in this repo.
- .gitignore excludes local env files and build artifacts.
- Use .env.example files for sharing required configuration safely.

## Production Readiness Highlights

- FastAPI middleware-based error handling for consistent JSON error responses
- CORS enabled for API access
- Environment-based API URL on frontend
- Serverless adapter in place for Vercel
  - Adaptive response generation service (explanation, easier practice, next step)
  - MongoDB-backed persistence with seeded questions for demo flow

- Frontend React app with:
  - Learning screen (question, answer submit)
  - Adaptive feedback panel
  - Dashboard section (interactions, weak concepts, state breakdown)
  - Concept switching (`loops`, `arrays`)
  - Zustand state store + backend API integration

## Actual Folder Structure (Implemented)

backend/
- requirements.txt
- .env.example
- app/
  - main.py
  - routes/
    - health.py
    - learning.py
  - services/
    - behavior_engine.py
    - genai_service.py
  - models/
    - schemas.py
  - db/
    - memory_store.py

frontend/
- package.json
- .env.example
- vite.config.js
- src/
  - App.jsx
  - main.jsx
  - index.css
  - components/
    - QuestionCard.jsx
    - AdaptivePanel.jsx
  - pages/
    - DashboardPage.jsx
  - services/
    - api.js
  - store/
    - useLearningStore.js

## How To Run

### 1) Start Backend

From project root:

Ensure MongoDB is running locally on `mongodb://localhost:27017` (or set `MONGODB_URI` in `backend/.env`).

```powershell
C:/Users/Kaush/AppData/Local/Programs/Python/Python314/python.exe -m pip install -r backend/requirements.txt
C:/Users/Kaush/AppData/Local/Programs/Python/Python314/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### 2) Start Frontend

Open a second terminal from project root:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Frontend URL: `http://localhost:5173`
Backend URL: `http://127.0.0.1:8000`

## Next Implementation Steps

1. Add authentication and user session tracking.
2. Add advanced Gemini prompt orchestration/LangChain integration behind feature flags.
3. Add analytics page with behavior trend charts.
4. Add experiment logging for adaptive-vs-fixed path comparison.

## Diagnostic Pipeline (New)

Implemented a complete AI diagnostic flow with async FastAPI + MongoDB persistence.

### Endpoints

1. `POST /diagnostic/generate`
   - Request: `{ "topic": "recursion", "user_id": "demo-user-1" }`
  - Response: `{ "questions": [ ...3 diagnostic questions... ] }`

2. `POST /diagnostic/analyze`
   - Request:
     - `topic`
  - `responses[]`: `question_id`, `question`, `answer`, `confidence`
   - Response:
     - `evaluation`
     - `learning_plan`

### New Backend Modules

- `backend/app/routes/diagnostic.py`
- `backend/app/services/llm_service.py`
- `backend/app/services/diagnostic_service.py`
- `backend/app/db/mongo.py`

### LLM Configuration

Set these in `backend/.env`:

- `LLM_API_KEY`
- `LLM_BASE_URL` (OpenAI-compatible base URL, e.g. `https://api.openai.com/v1`)
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`

The service also supports fallback from `GOOGLE_API_KEY` + `GOOGLE_MODEL` using the Gemini OpenAI-compatible endpoint if `LLM_API_KEY` is not set.

## Latest Demo Status (March 2026)

The project now supports two end-to-end demo modes in the same UI:

1. Diagnostic Assessment Flow
- Topic input -> AI-generated diagnostic questions
- Response analysis with learner level, behavior, strengths/weaknesses, misconceptions, confidence gaps
- Personalized learning roadmap and practice questions

2. Adaptive Practice Loop
- Live question retrieval from `/api/learning/question`
- Attempt submission to `/api/learning/attempt`
- Behavior-driven feedback (`struggling`, `guessing`, `mastery`, `improving`, `neutral`)
- Auto-progression to next tuned question

### Integrated UI Views

- Landing page
- Diagnostic page
- Analysis/result page
- Behavior dashboard page
- Adaptive learning loop page

### AI Source Transparency

Diagnostic responses now expose model-source metadata:

- `ai_source`: `live` or `fallback`
- `stage_sources`: source for `evaluation` and `learning_plan`

This enables reliable demos even under provider rate limiting (429), while still clearly indicating whether output came from live model calls or the fallback path.

## User Learning History and Resume (New)

Implemented persistent per-user topic history using MongoDB collection `user_learning_history`.

### Endpoints

1. `POST /user/progress`
  - Save or update topic progress for a user
  - Appends latest diagnostic attempt into topic history

2. `GET /user/topics/{user_id}`
  - Returns all previously learned topics with:
    - topic
    - level
    - progress
    - weaknesses
    - last_updated

3. `GET /user/topic/{user_id}/{topic}`
  - Returns topic details for resume flow:
    - strengths/weaknesses/misconceptions
    - learning_plan
    - resume_message

### Behavior

- First-time topic: runs diagnostic and saves history automatically.
- Returning topic: frontend checks history and resumes directly from saved plan (skips fresh diagnostic by default).
- Learning-plan personalization now uses previously recorded weaknesses when revisiting a topic.