# BriefGen – AI Legal Draft Assistant

BriefGen turns short answers into **structured legal drafts** with an agent that asks clarifying questions, then exports **DOCX**.

## Run (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env (ADMIN_PASS, optionally OPENAI_API_KEY)
export $(grep -v '^#' .env | xargs -I{} echo {})
uvicorn app.main:app --reload
# http://localhost:8000
```

## Run (Docker)
```bash
cp .env.example .env
docker compose up --build
# http://localhost:8000
```

## Notes
- If no `OPENAI_API_KEY`, the app falls back to a rule-based draft so you can test the flow.
- Review outputs before filing.
