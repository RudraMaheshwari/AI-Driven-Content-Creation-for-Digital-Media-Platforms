# Frontend — AI Content Platform

Next.js 14 (App Router) UI for the content-creation backend. Talks to FastAPI via `lib/api.ts`.

---

## Setup

```bash
cd frontend
npm install
npm run dev
```

The UI is served at `http://localhost:3000`. The backend must be running at `http://localhost:8000` (or wherever `NEXT_PUBLIC_API_BASE_URL` points).

### Build / start

```bash
npm run build
npm run start
```

### Lint

```bash
npm run lint
```

---

## Environment variables

Create `frontend/.env.local` if you need to override the defaults:

| Variable                   | Default                  | Notes                                          |
| -------------------------- | ------------------------ | ---------------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000`  | Backend base URL. Read in `lib/api.ts:1`.      |

`NEXT_PUBLIC_*` variables are inlined at build time, so rebuild after changing them.

---

## Pages

- `/` — content generator (prompt + content type + platform + tone + length + audience, with toggles for refinement loop, personalization, and image generation).
- `/history` ("Archive") — recent compositions with their illustrations.

The form sends:

```ts
{ prompt, content_type, platform, tone, length, audience?, refine_loop?, personalize?, generate_image? }
```

…to `POST /generate`, then polls `GET /generate/{id}` until status flips to `completed` or `failed`. The result panel renders the generated illustration as a hero image above the article body and shows the editor's quality score.

A "Revise" box under the article calls `POST /content/refine` with the user's free-text feedback for one-off tweaks without re-running the full pipeline.

---

## How refined vs original content is produced

The UI itself doesn't pick refined vs original output — that's decided **on the backend** via `CONTENT_MOCK` and `CONTENT_REFINEMENT_LOOP` (see `backend/README.md`). The form's two checkboxes (`refine_loop`, `personalize`) override the backend defaults per-request.

| Backend / form state                                                                  | What the result panel shows                                                                |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `CONTENT_MOCK=true`                                                                   | Mock text placeholder + procedurally drawn placeholder image                               |
| `CONTENT_MOCK=false`, refine-loop **off**                                             | **Original** raw draft from a single Gemini call (fast) + optional Gemini-rendered image    |
| `CONTENT_MOCK=false`, refine-loop **on**                                              | **Refined** output: evaluate → rewrite → re-evaluate (slow) + optional Gemini-rendered image|
| `CONTENT_MOCK=false`, refine-loop **on**, personalization **on**, audience filled in  | Refined + audience-personalized output + optional Gemini-rendered image                     |
| `generate_image` **off** (form checkbox or `CONTENT_GENERATE_IMAGE=false` on backend) | Text only — no illustration rendered                                                       |

The result panel shows `q=<score>` and `<n> iter` so you can see what the pipeline actually did. The record's `initial_output` (the raw first draft) and `final_output` (what's displayed) are both persisted on the backend for inspection.

### Model latency, from a UI perspective

Latency the user sees is dominated by `GEMINI_MODEL` on the backend:

- **Lower latency** (sub-second to a few seconds): `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.0-flash`. Good defaults for short-form content (captions, social posts, ad copy).
- **Higher latency** (several seconds to ~15s): `gemini-2.5-pro`, `gemini-1.5-pro`. Use for long-form articles, scripts, and newsletters where coherence matters more than speed.

If the refinement loop is enabled, multiply the per-call latency by up to `1 + 2 × MAX_ITERATIONS`. The polling helper in `lib/api.ts` (`pollGeneration`) defaults to a 5-minute timeout, which comfortably covers both tiers.

---

## Project layout

```
frontend/
├── app/                # Next.js App Router pages
│   ├── page.tsx        # Generator page
│   ├── history/        # Gallery / history view
│   ├── layout.tsx
│   └── globals.css
├── components/
│   └── ContentForm.tsx # Prompt form + result panel + revise box
├── lib/
│   └── api.ts          # Typed client for the FastAPI backend
├── public/
├── tailwind.config.ts
└── next.config.mjs
```
