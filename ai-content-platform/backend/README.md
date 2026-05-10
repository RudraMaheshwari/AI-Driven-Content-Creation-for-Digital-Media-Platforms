# Backend — AI Content Platform

FastAPI service that orchestrates a Gemini/LangChain content-creation pipeline: safety → prompt preprocessing → generation → quality evaluation → rewrite loop → personalization → image-prompt synthesis → image rendering.

API entrypoint: `app.py` · Settings: `src/config/settings.py` · Pipeline: `src/agents/factories/content_agent.py` · Image: `src/services/image_service.py`

---

## Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env             # then set GOOGLE_API_KEY
python app.py
```

The API is served at `http://localhost:8000` (Swagger UI at `/docs`).

### Endpoints

| Method | Path                   | Purpose                                              |
| ------ | ---------------------- | ---------------------------------------------------- |
| POST   | `/generate`            | Run the content pipeline (returns `pending` record)  |
| GET    | `/generate/{id}`       | Fetch a single record by id                          |
| GET    | `/history`             | List recent generations (filter by platform/type)    |
| POST   | `/content/refine`      | One-shot rewrite of supplied content given feedback  |
| GET    | `/health`              | Health check (reports `mock_mode`, `model_id`)       |

---

## Environment variables

All env access lives in `src/config/settings.py`. Copy `.env.example` to `.env` and edit.

### App / CORS

| Variable             | Default                  | Notes                  |
| -------------------- | ------------------------ | ---------------------- |
| `APP_HOST`           | `0.0.0.0`                |                        |
| `APP_PORT`           | `8000`                   |                        |
| `APP_DEBUG`          | `true`                   |                        |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000`  | Comma-separated list   |

### Gemini (LangChain)

| Variable                    | Default              | Notes                                    |
| --------------------------- | -------------------- | ---------------------------------------- |
| `GOOGLE_API_KEY`            | *(required for real)*| Needed when `CONTENT_MOCK=false`         |
| `GEMINI_MODEL`              | `gemini-2.5-flash`   | See latency table below                  |
| `GEMINI_TEMPERATURE`        | `0.7`                | Higher = more creative                   |
| `GEMINI_MAX_OUTPUT_TOKENS`  | `1024`               | Cap on response length                   |

### Content pipeline

| Variable                            | Default        | Notes                                                            |
| ----------------------------------- | -------------- | ---------------------------------------------------------------- |
| `CONTENT_MOCK`                      | `true`         | **See toggle table below**                                       |
| `CONTENT_REFINEMENT_LOOP`           | `true`         | **See toggle table below**                                       |
| `CONTENT_REFINEMENT_MAX_ITERATIONS` | `2`            | Hard cap on rewrite iterations                                   |
| `CONTENT_QUALITY_THRESHOLD`         | `0.7`          | Loop stops once quality score crosses this                       |
| `CONTENT_PERSONALIZATION`           | `true`         | Apply audience-personalization layer                             |
| `CONTENT_SAFETY_FILTER`             | `true`         | Run keyword + Gemini safety classifier before generation         |
| `CONTENT_DEFAULT_TONE`              | `professional` | Used when client omits `tone`                                    |
| `CONTENT_DEFAULT_LENGTH`            | `medium`       | `short` / `medium` / `long`                                      |
| `CONTENT_DEFAULT_PLATFORM`          | `blog`         | Used when client omits `platform`                                |

### Image generation

| Variable                  | Default                              | Notes                                                                |
| ------------------------- | ------------------------------------ | -------------------------------------------------------------------- |
| `CONTENT_GENERATE_IMAGE`  | `true`                               | Master toggle for the image step (renders + persists a `.png`)       |
| `IMAGE_MODEL_ID`          | `gemini-2.5-flash-image`             | Gemini image-output model. Can switch to `imagen-3.0-generate-002`   |
| `IMAGE_STORAGE_DIR`       | `./storage/images`                   | Where rendered PNGs are written                                      |
| `PUBLIC_IMAGE_BASE_URL`   | `/static/images`                     | URL prefix served via FastAPI's `StaticFiles` mount                  |

The image step uses the **new** `google-genai` SDK (`from google import genai`). It is installed alongside the legacy `google-generativeai` shipped by `langchain-google-genai`.

### Storage

| Variable        | Default                              |
| --------------- | ------------------------------------ |
| `DATABASE_URL`  | `sqlite:///./storage/content.db`     |

---

## Toggle: refined output vs raw initial draft

Two boolean flags decide what kind of content comes out of `/generate`:

| Flag                       | `true`                                                                  | `false`                                                              |
| -------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `CONTENT_MOCK`             | Returns a **mock placeholder** (no Gemini call, instant) — also draws a placeholder image | Runs the **real** Gemini pipeline + real image render                |
| `CONTENT_REFINEMENT_LOOP`  | Runs the **refined** pipeline: evaluate → rewrite → re-evaluate (slow)  | Returns the **original** initial draft only (single Gemini call)     |
| `CONTENT_PERSONALIZATION`  | Adapts the output for the supplied audience                             | Returns generic output regardless of audience                        |
| `CONTENT_GENERATE_IMAGE`   | Synthesises an image prompt then renders it via `IMAGE_MODEL_ID`        | Skips both steps — returns text only                                 |

So:

- **Quick mock for UI work** → `CONTENT_MOCK=true` (no API key needed, instant)
- **Original / raw draft (fast, single Gemini call)** → `CONTENT_MOCK=false`, `CONTENT_REFINEMENT_LOOP=false`
- **Refined / polished content (slow, evaluated and rewritten)** → `CONTENT_MOCK=false`, `CONTENT_REFINEMENT_LOOP=true`

When `CONTENT_REFINEMENT_LOOP=true`, the agent calls Gemini up to `1 + 2 × CONTENT_REFINEMENT_MAX_ITERATIONS` times per request (one generation, plus `evaluate + rewrite` per iteration). The loop exits early once the quality score crosses `CONTENT_QUALITY_THRESHOLD`.

The two outputs are persisted separately on each record:

- `initial_output` — raw first draft from Gemini
- `final_output` — what the user sees (after rewrite + personalization, or same as `initial_output` if loop was off)

Per-request override: clients can pass `refine_loop` and `personalize` booleans in the POST body to override the env defaults for a single call.

---

## Model latency

Set `GEMINI_MODEL` (text) and `IMAGE_MODEL_ID` (image) to pick the variant. Lower-latency models trade quality for speed; higher-latency ones spend more time on reasoning.

### Text models — `GEMINI_MODEL`

| Tier              | `GEMINI_MODEL`             | Notes                                                            |
| ----------------- | -------------------------- | ---------------------------------------------------------------- |
| **Lower latency** | `gemini-2.5-flash-lite`    | Cheapest and fastest; best for short captions, headlines, ad copy |
|                   | `gemini-2.5-flash`         | Default — good quality at low latency, fine for most posts        |
|                   | `gemini-2.0-flash`         | Older flash; slightly faster than 2.5-flash on some prompts       |
| **Higher latency**| `gemini-2.5-pro`           | Best reasoning and long-form coherence; noticeably slower         |
|                   | `gemini-1.5-pro`           | Older pro; long context (1M tokens) but slower per-token          |

### Image models — `IMAGE_MODEL_ID`

| Tier              | `IMAGE_MODEL_ID`                       | Notes                                                              |
| ----------------- | -------------------------------------- | ------------------------------------------------------------------ |
| **Lower latency** | `gemini-2.5-flash-image`               | Default — Gemini "Nano Banana"; fast, edit-aware, cheap            |
| **Higher latency**| `imagen-3.0-generate-002`              | Imagen 3 — better photoreal quality, slower per render             |
|                   | `imagen-3.0-fast-generate-001`         | Faster Imagen variant (between the two)                            |

Rule of thumb: **flash models → low latency** (good default for short-form social/ad content); **pro models → high latency** (use for long-form articles, scripts, and newsletters where coherence matters more than throughput). The refinement loop multiplies whichever text cost you pick by up to `1 + 2 × MAX_ITERATIONS` calls per request, plus one image-prompt call and one image render when `CONTENT_GENERATE_IMAGE=true`.

---

## Notes

- The content service uses lazy initialization — Gemini isn't contacted until the first non-mock request. Switching to `CONTENT_MOCK=true` means the API works with no `GOOGLE_API_KEY`.
- The pipeline is deterministic-by-stage (no ReAct loop) — every request runs the same chain of tools. This keeps latency predictable and the trace easy to read.
- Each record stores `agent_trace` (a list of stage events with durations) so you can debug what the pipeline actually did per request.

## Tests

```bash
CONTENT_MOCK=true pytest -q
```

Tests force mock mode so they never burn Gemini quota.
