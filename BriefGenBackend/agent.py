# BriefGenBackend/agent.py
import os, json, uuid, re, asyncio, logging
from typing import Dict, Any, Optional, List
from jsonschema import validate, ValidationError

try:
    from together import Together  # pip install together
except Exception:  # library not installed
    Together = None

# ---------- logging ----------
log = logging.getLogger("briefgen.agent")
if not log.handlers:  # ensure logs appear even with uvicorn defaults
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
    log.addHandler(_h)
log.setLevel(logging.INFO)

# ---------- schema ----------
FINAL_SCHEMA = {
    "type": "object",
    "required": ["title","parties","facts","grounds","prayer","annexures","citations","notes"],
    "properties": {
        "title": {"type": "string"},
        "parties": {"type": "array", "items": {"type": "string"}},
        "facts": {"type": "array", "items": {"type": "string"}},
        "grounds": {"type": "array", "items": {"type": "string"}},
        "prayer": {"type": "array", "items": {"type": "string"}},
        "annexures": {"type": "array", "items": {"type": "string"}},
        "citations": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"}
    }
}

# ---------- templates / questions ----------
TEMPLATES = {
    "Legal Notice": {
        "fields": [
            ("sender_name", "Your full name or firm name", "e.g., Upadhyay & Associates"),
            ("sender_address", "Your address", "Street, city, pincode"),
            ("recipient_name", "Recipient (individual/company) name", "e.g., Sattik Packaging Pvt Ltd"),
            ("recipient_address", "Recipient address", "Street, city, pincode"),
            ("amount_due", "Total amount due (INR)", "e.g., 855974"),
            ("last_payment_date", "Date of last payment", "YYYY-MM-DD"),
            ("invoice_refs", "Invoice numbers / references", "Comma-separated"),
            ("deadline_days", "Demand deadline (days)", "e.g., 7 or 15"),
            ("jurisdiction", "Jurisdiction / court", "e.g., Kolkata / Alipore"),
            ("facts_summary", "Short factual background", "1-3 sentences")
        ]
    },
    "Petition": {
        "fields": [
            ("petitioner", "Petitioner full name", ""),
            ("respondent", "Respondent full name", ""),
            ("court", "Court / forum", "e.g., Commercial Court at Alipore"),
            ("cause_of_action", "Cause of action", ""),
            ("reliefs", "Reliefs sought (comma-separated)", ""),
            ("facts_summary", "Factual chronology (1-4 bullets)", ""),
            ("annexures_list", "Annexures (comma-separated)", "")
        ]
    },
    "Affidavit": {
        "fields": [
            ("deponent_name", "Deponent name", ""),
            ("deponent_address", "Deponent address", ""),
            ("court", "Court / forum", ""),
            ("statements", "Statements to affirm (semicolon-separated)", ""),
            ("place", "Place of verification", ""),
            ("date", "Date of verification", "YYYY-MM-DD")
        ]
    }
}

SYSTEM_INSTRUCTIONS = (
    "You are a legal drafting assistant for India-focused documents.\n"
    "Return a SINGLE JSON object ONLY (no markdown, no commentary), matching this schema:\n"
    "{title: string, parties: string[], facts: string[], grounds: string[], prayer: string[], annexures: string[], citations: string[], notes: string}\n"
    "Guidelines:\n"
    "- Use formal, precise legal drafting language suitable for a pre-litigation notice.\n"
    "- Expand the user's facts into complete, coherent paragraphs in 'facts'.\n"
    "- In 'grounds', articulate the legal basis in plain language (no case citations unless provided).\n"
    "- In 'prayer', include clear numbered demands and timelines.\n"
    "- Do not invent real case citations; if not provided, use '[citation needed]'."
)

# ---------- helpers ----------
def _next_required_field(template: str, answers: Dict[str, Any]) -> Optional[Dict[str,str]]:
    fields = TEMPLATES[template]["fields"]
    for key, text, hint in fields:
        if not answers.get(key):
            return {"id": uuid.uuid4().hex, "field": key, "text": text, "hint": hint or ""}
    return None

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Try to recover a JSON object from an LLM response that may include fences/prose."""
    if not text:
        return None
    # strip code fences
    text = re.sub(r"```(?:json)?", "", text)
    text = text.replace("```", "")
    # naive largest-braces grab
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

# ---------- richer rule-based fallback ----------
def _rule_based_final(template: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    if template == "Legal Notice":
        sender = answers.get('sender_name','[Sender]')
        s_addr = answers.get('sender_address','[Address]')
        recp   = answers.get('recipient_name','[Recipient]')
        r_addr = answers.get('recipient_address','[Address]')
        amt    = answers.get('amount_due','[Amount]')
        last   = answers.get('last_payment_date','[Date]')
        inv    = answers.get('invoice_refs','[Refs]')
        days   = answers.get('deadline_days','[X]')
        juris  = answers.get('jurisdiction','[Jurisdiction]')
        sumry  = answers.get('facts_summary','[Summary]')

        title = f"Legal Notice for Non-Payment against {recp}"

        parties = [
            f"Sender: {sender}",
            f"Recipient: {recp}"
        ]

        facts: List[str] = [
            f"1. That the Sender, {sender}, having its office at {s_addr}, supplied goods/services to you, {recp}, at {r_addr}.",
            f"2. That invoices bearing references {inv} were duly raised and rendered; payments were expected within the agreed credit period.",
            f"3. That despite repeated requests and reminders, an outstanding sum of INR {amt} remains unpaid; your last payment, if any, was on {last}.",
            f"4. That by reason of the aforesaid default, the Sender has suffered financial prejudice and is constrained to issue this formal notice.",
            f"5. Background: {sumry}"
        ]

        grounds = [
            "Breach of contractual obligation to make timely payment for goods/services supplied.",
            "Unjust retention of amounts due despite invoices and reminders.",
            "Right to recover principal together with reasonable interest and recovery costs under applicable law and contract."
        ]

        prayer = [
            f"1. Pay INR {amt} in full within {days} days from receipt of this notice.",
            "2. Pay reasonable interest on the delayed amount as per the agreed terms or, in the alternative, at a reasonable commercial rate.",
            "3. Reimburse costs and expenses incurred for issuance of this notice and recovery."
        ]

        annexures = [
            f"Copies of invoices: {inv}",
            "Statement of account",
            "Proof of delivery / service completion (as applicable)"
        ]

        citations = ["[citation needed]"]  # do not fabricate case law

        notes = f"Jurisdiction/venue: {juris}. This is a pre-litigation demand without prejudice to the Sender’s rights and remedies."

        return {
            "title": title, "parties": parties, "facts": facts,
            "grounds": grounds, "prayer": prayer, "annexures": annexures,
            "citations": citations, "notes": notes
        }

    elif template == "Petition":
        title = f"Petition by {answers.get('petitioner','[Petitioner]')} against {answers.get('respondent','[Respondent]')}"
        parties = [
            f"Petitioner: {answers.get('petitioner','[Petitioner]')}",
            f"Respondent: {answers.get('respondent','[Respondent]')}"
        ]
        facts = [
            f"Chronology: {answers.get('facts_summary','[Facts]')}"
        ]
        grounds = [answers.get("cause_of_action","[Cause]")]
        prayer = [s.strip() for s in (answers.get("reliefs","").split(",")) if s.strip()] or [
            "Appropriate reliefs as this Hon’ble Court deems fit."
        ]
        annexures = [s.strip() for s in (answers.get("annexures_list","").split(",")) if s.strip()] or ["[Annexures]"]
        return {
            "title": title, "parties": parties, "facts": facts,
            "grounds": grounds, "prayer": prayer, "annexures": annexures,
            "citations": ["[citation needed]"], "notes": f"Court/Forum: {answers.get('court','[Court]')}"
        }

    # Affidavit
    title = f"Affidavit of {answers.get('deponent_name','[Deponent]')}"
    parties = [f"Deponent: {answers.get('deponent_name','[Deponent]')}"]
    facts = [s.strip() for s in (answers.get("statements","").split(";")) if s.strip()] or ["[Statement]"]
    return {
        "title": title, "parties": parties, "facts": facts,
        "grounds": [], "prayer": [], "annexures": [],
        "citations": ["[citation needed]"],
        "notes": f"Verification at {answers.get('place','[Place]')} on {answers.get('date','[Date]')}"
    }

# ---------- Together ----------
async def _call_together(messages: list, model: Optional[str] = None) -> Optional[str]:
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        log.warning("Together disabled: TOGETHER_API_KEY not set")
        return None
    if Together is None:
        log.warning("Together SDK not available. Did you install `together`?")
        return None

    model_name = os.getenv("TOGETHER_MODEL") or model or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
    log.info("Calling Together model=%s", model_name)

    def _do():
        client = Together(api_key=api_key)
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
            # If your model supports JSON mode, uncomment the next line:
            # response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content if resp and resp.choices else None

    try:
        out = await asyncio.to_thread(_do)
        log.info("Together response length=%s", len(out) if out else 0)
        return out
    except Exception as e:
        log.exception("Together call failed: %s", e)
        return None

# ---------- main entry ----------
async def get_next_question_or_final(template: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    nxt = _next_required_field(template, answers)
    if nxt:
        return {"type": "question", "question": nxt}

    user_facts = json.dumps(answers, ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": (
            f"Template: {template}\nFacts:\n{user_facts}\n"
            "Requirements:\n"
            "- Output only the JSON object (no markdown code fences, no commentary).\n"
            "- Populate each array with complete, formal sentences suitable for a legal document.\n"
        )}
    ]

    text = await _call_together(messages)

    draft_json: Optional[Dict[str, Any]] = None
    if text:
        try:
            draft_json = json.loads(text)
        except Exception:
            draft_json = _extract_json(text)

    if not draft_json:
        log.info("Falling back to rule-based draft for template=%s", template)
        draft_json = _rule_based_final(template, answers)

    try:
        validate(instance=draft_json, schema=FINAL_SCHEMA)
    except ValidationError as e:
        log.warning("Draft failed schema validation; using fallback. Error: %s", e)
        draft_json = _rule_based_final(template, answers)

    return {"type": "final", "draft": draft_json}
