# BriefGen Frontend (Vite + React + TS + Tailwind)

A small SPA for your BriefGen FastAPI backend with Together.ai agent.

## Prereqs
- Node 18+
- Backend running on `http://127.0.0.1:8000`

Create a `.env` file (or use `.env.example`):
```
VITE_API_BASE=http://127.0.0.1:8000
```

## Run
```
npm install
npm run dev
```
Open http://localhost:5173

## Backend notes
This SPA expects JSON-based endpoints in addition to your existing HTML routes:

- `POST /api/auth` body `{ "password": "..." }` → sets the same `briefgen_session` cookie and returns `{ "ok": true }`
- `GET /api/templates` → `{ "templates": ["Legal Notice","Petition","Affidavit"] }`
- `POST /api/drafts` body `{ "template": "Legal Notice" }` → `{ "draft_id": "..." }`

The app will **fallback** to:
- using the HTML `/auth` form if `/api/auth` is missing
- using a **default** templates array if `/api/templates` is missing

> Draft creation **needs** `/api/drafts`. Add the small snippet shown earlier so the SPA can create a draft ID.

Also, enable CORS in FastAPI:
```py
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

And set in docker-compose:
```yaml
environment:
  - FRONTEND_ORIGIN=${FRONTEND_ORIGIN:-http://localhost:5173}
```

## Flow
1) Login with the admin password (cookie session)
2) Pick a template
3) Answer questions one by one
4) Download the generated `.docx`

## Build
```
npm run build
npm run preview
```