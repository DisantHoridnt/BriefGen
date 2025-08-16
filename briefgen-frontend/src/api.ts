const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

export async function api(path: string, init: RequestInit = {}) {
  const resp = await fetch(`${BASE}${path}`, {
    credentials: "include", // send/receive cookies
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    ...init,
  });
  if (!resp.ok) {
    const msg = await resp.text().catch(() => `${resp.status} ${resp.statusText}`);
    throw new Error(msg || `${resp.status} ${resp.statusText}`);
  }
  const ct = resp.headers.get("content-type") || "";
  return ct.includes("application/json") ? resp.json() : resp.text();
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

export async function login(password: string): Promise<void> {
  // First try JSON login
  let res = await fetch(`${API_BASE}/api/auth`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ password }),
  });
  if (res.status === 404) {
    // Fallback to form /auth
    const form = new URLSearchParams();
    form.set('password', password);
    res = await fetch(`${API_BASE}/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      credentials: 'include',
      body: form.toString(),
      redirect: 'follow',
    });
    if (!(res.status === 200 || res.status === 302)) {
      throw new Error('Login failed');
    }
  } else if (!res.ok) {
    throw new Error('Login failed');
  }
}

export type TemplatesResp = { templates: string[] };

export async function getTemplates(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/templates`, { credentials: 'include' });
    if (res.status === 404) {
      // fallback if your backend didn't add /api/templates yet
      return ['Legal Notice','Petition','Affidavit'];
    }
    const data = await json<TemplatesResp>(res);
    return data.templates ?? ['Legal Notice','Petition','Affidavit'];
  } catch {
    return ['Legal Notice','Petition','Affidavit'];
  }
}

export async function createDraft(template: string): Promise<string> {
  // Preferred JSON endpoint
  let res = await fetch(`${API_BASE}/api/drafts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ template }),
  });
  if (res.status === 404) {
    throw new Error('The backend needs /api/drafts (JSON) to create a draft. Please add the minimal endpoint as documented.');
  }
  const data = await json<{ draft_id: string }>(res);
  return data.draft_id;
}

export type AgentQuestion = {
  id: string; field: string; text: string; hint?: string; required?: boolean
}
export type AgentResponse = 
  | { type: 'question'; question: AgentQuestion }
  | { type: 'final'; draft: any };

export async function agentNext(draft_id: string, last?: { field: string; text: any }): Promise<AgentResponse> {
  const res = await fetch(`${API_BASE}/agent/next`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ draft_id, last_answer: last }),
  });
  return json<AgentResponse>(res);
}

export function exportDocx(draft_id: string) {
  window.open(`${API_BASE}/export/${draft_id}.docx`, '_blank');
}