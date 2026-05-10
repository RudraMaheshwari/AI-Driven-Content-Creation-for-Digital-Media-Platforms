# AI Content Platform

End-to-end AI-driven content creation platform for digital media — text-only generation built on Google Gemini (via LangChain), a FastAPI backend, and a Next.js frontend.

Inspired by: *AI-Driven Content Creation for Digital Media Platforms* (Dr. Ajay Kumar Sharma, Chhavi Vinaik, GITS Udaipur).

## Architecture

```
+------------------+       +-----------------------+       +--------------------+
|  Next.js (UI)    | <---> |  FastAPI (backend)    | <---> |  Content Pipeline  |
|  - Prompt input  |  REST |  - /generate          |       |  (Gemini + chains) |
|  - History       |       |  - /generate/{id}     |       +---------+----------+
|  - Revise        |       |  - /history           |                 |
|  - Tone/platform |       |  - /content/refine    |                 v
+------------------+       |  - LangChain agent    |       +--------------------+
                           |    safety → brief →   |       |  Storage + SQLite  |
                           |    generate → score → |       +--------------------+
                           |    rewrite → persona  |
                           +-----------------------+
```

## Tech Stack

- **Backend:** FastAPI, LangChain, `langchain-google-genai` (Gemini), SQLAlchemy
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **LLM orchestration:** Deterministic LangChain pipeline — safety filter → prompt preprocessing → generation → quality evaluation → rewrite loop → personalization
- **Storage:** SQLite (dev) / Postgres (prod)

## Pipeline

Mirrors the methodology figure from the source paper, with an extra image step at the end:

1. **Safety filter** — keyword blocklist + Gemini binary classifier
2. **Prompt preprocessing** — extract structured brief (refined prompt + key points + must-avoid)
3. **Initial content generation** — Gemini draft from the brief
4. **Quality & safety check** — Gemini scores clarity/relevance/tone (0–1)
5. **Refinement loop** — if score < threshold, rewrite with feedback (up to N iterations)
6. **Personalization layer** — adapt for the audience profile
7. **Image-prompt synthesis** — Gemini turns the finished article into a one-paragraph visual brief
8. **Image rendering** — `gemini-2.5-flash-image` (or Imagen) renders a PNG, persisted on disk
9. **Platform-ready output** — text + image URL returned to UI, persisted in SQLite

## Project layout

```
ai-content-platform/
├── backend/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── factories/      # LangChain pipeline orchestrator
│   │   │   ├── monitoring/     # trace collector
│   │   │   ├── prompts/        # ChatPromptTemplates for each stage
│   │   │   └── tools/          # safety, refiner, generator, evaluator, rewriter, personalizer
│   │   ├── api/routes/         # FastAPI routers (/generate, /history, /content/refine, /health)
│   │   ├── config/settings.py  # pydantic-settings env loader
│   │   ├── database/           # SQLAlchemy models + repositories
│   │   ├── services/           # Gemini client, content service
│   │   └── utils/              # logger, exceptions, ids
│   ├── app.py                  # FastAPI entrypoint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                   # Next.js 14 app
├── docker-compose.yml
├── azure-pipeline.yml
└── README.md
```

## Local development

1. **Backend**

   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env      # then set GOOGLE_API_KEY
   python app.py
   ```

   The API is served at `http://localhost:8000` (docs at `/docs`).

2. **Frontend**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   The UI is served at `http://localhost:3000`.

3. **Docker (both services)**

   ```bash
   GOOGLE_API_KEY=your_key CONTENT_MOCK=false docker-compose up --build
   ```

## Environment variables

See `backend/.env.example` and `backend/README.md`. Required for real generation: `GOOGLE_API_KEY` (Gemini). All other vars have sensible defaults for local dev.

## Notes

- Default mode is **mock** (`CONTENT_MOCK=true`) so the UI works out-of-the-box with no API key.
- Switch to real Gemini by setting `CONTENT_MOCK=false` and providing `GOOGLE_API_KEY` in `backend/.env`.
- See `backend/README.md` for the toggles that switch between fast single-shot output and the full refined pipeline, plus the model latency table.
