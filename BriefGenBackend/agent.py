import os, json, uuid, httpx, re
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
from together import Together
import asyncio

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
    "You are a legal drafting assistant for India-focused documents. "
    "First ensure essential facts are gathered. When drafting, return STRICT JSON "
    "matching the schema (no commentary). Do not invent real case citations; if not provided, "
    "write '[citation needed]'. Tone must be formal and clear."
)

def _next_required_field(template: str, answers: Dict[str, Any]) -> Optional[Dict[str,str]]:
    fields = TEMPLATES[template]["fields"]
    for key, text, hint in fields:
        if not answers.get(key):
            return {"id": uuid.uuid4().hex, "field": key, "text": text, "hint": hint or ""}
    return None

def _rule_based_final(template: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    if template == "Legal Notice":
        title = f"Legal Notice for Non-payment against {answers.get('recipient_name','[Recipient]')}"
        parties = [f"Sender: {answers.get('sender_name','[Sender]')}", f"Recipient: {answers.get('recipient_name','[Recipient]')}"]
        facts = [
            f"The sender is {answers.get('sender_name','[Sender]')} located at {answers.get('sender_address','[Address]')}.",
            f"The recipient is {answers.get('recipient_name','[Recipient]')} located at {answers.get('recipient_address','[Address]')}.",
            f"Amount due is INR {answers.get('amount_due','[Amount]')} with last payment on {answers.get('last_payment_date','[Date]')}.",
            f"Invoices: {answers.get('invoice_refs','[Refs]')}.",
            f"Summary: {answers.get('facts_summary','[Summary]')}."
        ]
        grounds = ["Failure to make payments due despite invoices raised and reminders."]
        prayer = [
            f"Pay INR {answers.get('amount_due','[Amount]')} within {answers.get('deadline_days','[X]')} days.",
            "Failing which, legal proceedings will be initiated without further notice."
        ]
        annexures = ["Invoice copies", "Account statement", "Proof of delivery"]
        return {
            "title": title, "parties": parties, "facts": facts,
            "grounds": grounds, "prayer": prayer, "annexures": annexures,
            "citations": ["[citation needed]"], "notes": f"Jurisdiction: {answers.get('jurisdiction','[Jurisdiction]')}"
        }
    elif template == "Petition":
        title = f"Petition by {answers.get('petitioner','[Petitioner]')} against {answers.get('respondent','[Respondent]')}"
        parties = [f"Petitioner: {answers.get('petitioner','[Petitioner]')}", f"Respondent: {answers.get('respondent','[Respondent]')}"]
        facts = [answers.get("facts_summary","[Facts]")]
        grounds = [answers.get("cause_of_action","[Cause]")]
        prayer = [s.strip() for s in (answers.get("reliefs","").split(",")) if s.strip()] or ["Appropriate reliefs as this Hon'ble Court deems fit."]
        annexures = [s.strip() for s in (answers.get("annexures_list","").split(",")) if s.strip()] or ["[Annexures]"]
        return {
            "title": title, "parties": parties, "facts": facts,
            "grounds": grounds, "prayer": prayer, "annexures": annexures,
            "citations": ["[citation needed]"], "notes": f"Court/Forum: {answers.get('court','[Court]')}"
        }
    else:
        title = f"Affidavit of {answers.get('deponent_name','[Deponent]')}"
        parties = [f"Deponent: {answers.get('deponent_name','[Deponent]')}"]
        facts = [s.strip() for s in (answers.get("statements","").split(";")) if s.strip()] or ["[Statement]"]
        return {
            "title": title, "parties": parties, "facts": facts,
            "grounds": [], "prayer": [], "annexures": [],
            "citations": ["[citation needed]"], "notes": f"Verification at {answers.get('place','[Place]')} on {answers.get('date','[Date]')}"
        }

async def _call_together(messages: list, model: str | None = None) -> Optional[str]:
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        return None

    model_name = os.getenv("TOGETHER_MODEL") or model or "google/gemma-3n-E4B-it"

    def _do():
        client = Together()  # uses TOGETHER_API_KEY from env
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
        )
        return resp.choices[0].message.content if resp and resp.choices else None

    try:
        return await asyncio.to_thread(_do)
    except Exception:
        return None

async def get_next_question_or_final(template: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    nxt = _next_required_field(template, answers)
    if nxt: return {"type": "question", "question": nxt}

    user_facts = json.dumps(answers, ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
        {"role": "user", "content": f"Template: {template}\nFacts:\n{user_facts}\n"
                                    "Produce the final draft as STRICT JSON with keys: title, parties, facts, grounds, prayer, annexures, citations, notes. No prose outside JSON."}
    ]

    text = await _call_together(messages)

    draft_json: Optional[Dict[str, Any]] = None

    if text:
        try:
            draft_json = json.loads(text)
        except Exception:
            # Try to salvage a JSON object if the model wrapped it in prose/markdown
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    draft_json = json.loads(m.group(0))
                except Exception:
                    draft_json = None

    if not draft_json:
        draft_json = _rule_based_final(template, answers)

    try:
        validate(instance=draft_json, schema=FINAL_SCHEMA)
    except ValidationError:
        draft_json = _rule_based_final(template, answers)

    return {"type": "final", "draft": draft_json}