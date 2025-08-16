import os
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from itsdangerous import URLSafeSerializer, BadSignature
from pydantic import BaseModel
from sqlmodel import select, Session

from .db import init_db, get_session
from .models import Draft, User
from .schemas import AgentQuestionResponse
from . import agent as agent_mod
from passlib.context import CryptContext

APP_NAME = "BriefGen"
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

ADMIN_PASS = os.getenv("ADMIN_PASS", "changeme")
APP_SECRET = os.getenv("APP_SECRET", "briefgen-secret-key")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

app = FastAPI(title=APP_NAME)

class SignupIn(BaseModel):
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class MeOut(BaseModel):
    email: str

class ApiAuthIn(BaseModel):
    password: str

class TemplatesOut(BaseModel):
    templates: list[str]

class DraftCreateIn(BaseModel):
    template: str

class DraftCreateOut(BaseModel):
    draft_id: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

serializer = URLSafeSerializer(APP_SECRET, salt="briefgen-auth")

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_pw(p: str) -> str: return pwd_ctx.hash(p)
def verify_pw(p: str, h: str) -> bool: return pwd_ctx.verify(p, h)

def _get_session_token(user: str = "admin") -> str:
    return serializer.dumps({"user": user, "ts": int(time.time())})

def _set_session_cookie(response: JSONResponse | RedirectResponse, user: str = "admin"):
    token = _get_session_token(user)
    # same cookie name/shape as your HTML login
    response.set_cookie("briefgen_session", token, httponly=True, samesite="lax", secure=False, path="/")

def _check_session_token(token: str) -> bool:
    try:
        data = serializer.loads(token)
        return isinstance(data, dict) and isinstance(data.get("user"), str) and bool(data.get("user"))
    except BadSignature:
        return False

def _is_auth(request: Request) -> bool:
    token = request.cookies.get("briefgen_session")
    return bool(token and _check_session_token(token))

def _require_auth(request: Request):
    if not _is_auth(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

RATE_LIMIT_RPS = 1.0
RATE_LIMIT_BURST = 5
_bucket: Dict[str, Dict[str, Any]] = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "local"
    now = time.time()
    bucket = _bucket.get(client_ip) or {"tokens": RATE_LIMIT_BURST, "ts": now}
    elapsed = now - bucket["ts"]
    bucket["tokens"] = min(RATE_LIMIT_BURST, bucket["tokens"] + elapsed * RATE_LIMIT_RPS)
    bucket["ts"] = now
    if bucket["tokens"] < 1.0:
        _bucket[client_ip] = bucket
        return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
    bucket["tokens"] -= 1.0
    _bucket[client_ip] = bucket
    response = await call_next(request)
    return response

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/api/signup", response_model=MeOut)
def api_signup(body: SignupIn, request: Request, session: Session = Depends(get_session)):
    # allow signup only if there are no users yet
    exists = session.exec(select(User.id).limit(1)).first()
    if exists is not None:
        raise HTTPException(status_code=403, detail="Sign-ups disabled")

    email = body.email.strip().lower()
    if not email or not body.password:
        raise HTTPException(400, "Email and password required")

    # create user
    user = User(email=email, password_hash=hash_pw(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    # set cookie
    resp = JSONResponse({"email": user.email})
    _set_session_cookie(resp, user=user.email)
    return resp

@app.post("/api/login", response_model=MeOut)
def api_login(body: LoginIn, request: Request, session: Session = Depends(get_session)):
    email = body.email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_pw(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    resp = JSONResponse({"email": user.email})
    _set_session_cookie(resp, user=user.email)
    return resp

@app.get("/api/me", response_model=MeOut)
def api_me(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get("briefgen_session")
    if not token:
        raise HTTPException(401, "Unauthorized")
    try:
        data = serializer.loads(token)
        return {"email": data.get("user")}
    except BadSignature:
        raise HTTPException(401, "Unauthorized")

@app.post("/api/auth")
def api_auth(body: ApiAuthIn):
    if body.password != ADMIN_PASS:
        raise HTTPException(status_code=401, detail="Invalid password")
    resp = JSONResponse({"ok": True})
    _set_session_cookie(resp)
    return resp

@app.get("/api/templates", response_model=TemplatesOut)
def api_templates():
    # Drives the template picker
    return {"templates": list(agent_mod.TEMPLATES.keys())}

@app.post("/api/drafts", response_model=DraftCreateOut)
def api_create_draft(body: DraftCreateIn, request: Request, session: Session = Depends(get_session)):
    _require_auth(request)
    if body.template not in agent_mod.TEMPLATES:
        raise HTTPException(status_code=400, detail="Unknown template")
    d = Draft(template=body.template)
    session.add(d); session.commit(); session.refresh(d)
    return {"draft_id": d.id}

@app.get("/healthz")
def healthz():
    return {"ok": True, "app": APP_NAME}

@app.get("/auth", response_class=HTMLResponse)
def auth_page(request: Request):
    if _is_auth(request):
        return RedirectResponse(url="/", status_code=302)
    tpl = TEMPLATES_DIR / "auth.html"
    if tpl.exists():
        return templates.TemplateResponse("auth.html", {"request": request, "app_name": APP_NAME})
    html = "<h2>Login</h2><form method='post' action='/auth'><input type='password' name='password'><button>Login</button></form>"
    return HTMLResponse(html)

@app.post("/auth")
def auth_login(request: Request, password: str = Form(...)):
    if password != ADMIN_PASS:
        return HTMLResponse("<h3>Invalid password</h3><a href='/auth'>Try again</a>", status_code=401)
    token = _get_session_token()
    resp = RedirectResponse(url="/", status_code=302)
    resp.set_cookie("briefgen_session", token, httponly=True, samesite="lax", secure=False)
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/auth", status_code=302)
    resp.delete_cookie("briefgen_session")
    return resp

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not _is_auth(request):
        return RedirectResponse(url="/auth", status_code=302)
    templates_list = list(agent_mod.TEMPLATES.keys())
    return templates.TemplateResponse("home.html", {"request": request, "templates": templates_list, "app_name": APP_NAME})

@app.post("/drafts")
def create_draft(request: Request, template: str = Form(...), session: Session = Depends(get_session)):
    _require_auth(request)
    if template not in agent_mod.TEMPLATES:
        raise HTTPException(400, "Unknown template")
    d = Draft(template=template)
    session.add(d); session.commit(); session.refresh(d)
    return RedirectResponse(url=f"/drafts/{d.id}", status_code=302)

@app.get("/drafts", response_class=HTMLResponse)
def list_drafts(request: Request, session: Session = Depends(get_session)):
    _require_auth(request)
    drafts = session.exec(select(Draft).order_by(Draft.created_at.desc())).all()
    return templates.TemplateResponse("drafts.html", {"request": request, "drafts": drafts, "app_name": APP_NAME})

@app.get("/drafts/{draft_id}", response_class=HTMLResponse)
def draft_detail(draft_id: str, request: Request, session: Session = Depends(get_session)):
    _require_auth(request)
    d = session.get(Draft, draft_id)
    if not d: raise HTTPException(404, "Not found")
    return templates.TemplateResponse("draft_detail.html", {"request": request, "draft": d, "app_name": APP_NAME})

class AgentNextIn(BaseModel):
    draft_id: str
    last_answer: Optional[Dict[str, Any]] = None

@app.post("/agent/next", response_model=AgentQuestionResponse)
async def agent_next(body: AgentNextIn, request: Request, session: Session = Depends(get_session)):
    _require_auth(request)
    d = session.get(Draft, body.draft_id)
    if not d: raise HTTPException(404, "Draft not found")
    if body.last_answer:
        field = body.last_answer.get("field"); text = body.last_answer.get("text")
        if field:
            answers = dict(d.answers_json or {}); answers[field] = text
            d.answers_json = answers; d.status = "collecting"
            session.add(d); session.commit(); session.refresh(d)
    result = await agent_mod.get_next_question_or_final(d.template, d.answers_json or {})
    if result.get("type") == "final":
        d.draft_json = result.get("draft"); d.status = "drafted"
        session.add(d); session.commit(); session.refresh(d)
    return result

@app.get("/export/{draft_id}.docx")
def export_docx(draft_id: str, request: Request, session: Session = Depends(get_session)):
    _require_auth(request)
    d = session.get(Draft, draft_id)
    if not d: raise HTTPException(404, "Not found")
    if not d.draft_json: raise HTTPException(400, "Draft not ready")
    from .exporter import build_docx_from_draft
    out_dir = BASE_DIR / "exports"; out_dir.mkdir(exist_ok=True)
    fname = f"{d.template.replace(' ','_')}-{d.id}.docx"
    path = out_dir / fname
    build_docx_from_draft(d.draft_json, str(path), title=d.template)
    return FileResponse(str(path), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=fname)

@app.get("/legal/{page}", response_class=HTMLResponse)
def legal_page(page: str, request: Request):
    pages = {"tos":"tos.html","privacy":"privacy.html","disclaimer":"disclaimer.html"}
    name = pages.get(page)
    if not name: raise HTTPException(404, "Not found")
    return templates.TemplateResponse(name, {"request": request, "app_name": APP_NAME})
