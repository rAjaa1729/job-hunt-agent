# job-hunt-agent

A personal AI agent that tailors a resume to a specific job description, using a single structured profile as its only source of truth — and (eventually) tracks applications end to end.

## How it's meant to work

1. **Profile** — all real background facts (experience, projects, skills, links) live in one structured file, `data/profile.json`. This is the only thing the agent is ever allowed to draw facts from.
2. **Tailoring** — given a job description, the agent picks the subset of the profile most relevant to that specific role and writes a resume from it. See [`docs/resume-rules.md`](docs/resume-rules.md) for the exact rules every generated resume must follow, and the checks used to verify it.
3. **Tracking** *(planned)* — logging applications and their status over time.
4. **Autofill** *(planned, later)* — filling out application forms, once the safer pieces above are solid.

## Getting started

These steps set up the parts that exist right now — the profile and the AI connection. There's no resume-generation command yet (see Project status below).

### 1. Install the dependencies

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

A virtual environment (`venv`) keeps this project's packages separate from anything else on your machine.

### 2. Add your own profile

```
cp data/profile.example.json data/profile.json
```

Open `data/profile.json` and replace the placeholder values with your real details. This file is private by design — it's listed in `.gitignore`, so it never gets committed or pushed, no matter what.

### 3. Set up an AI provider

```
cp .env.example .env
```

Open `.env` and pick one:

- **Cloudflare** (cloud-hosted, free tier with a daily limit) — set `LLM_PROVIDER=cloudflare`, then fill in `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`. Find the account ID under Workers & Pages in your Cloudflare dashboard; create a token under My Profile → API Tokens with "Workers AI" permission.
- **Ollama** (runs on your own computer, no daily limit, slower) — set `LLM_PROVIDER=ollama`, install [Ollama](https://ollama.com), make sure it's running, and pull a model first (e.g. `ollama pull qwen3.5:9b`).

### 4. Confirm it's working

```
python3 src/llm.py
```

A working setup prints something like `LLM (ollama) replied: works`. If something's misconfigured, the error message explains exactly what to check.

## Project status

- [x] Profile schema + real data (kept private — see below)
- [x] Resume tailoring rules defined ([`docs/resume-rules.md`](docs/resume-rules.md))
- [ ] Resume-tailoring tool (in progress)
- [ ] Application tracking
- [ ] Form autofill

## Privacy

`data/profile.json` contains real personal information and is `.gitignore`'d — it never enters git history and is never pushed. `data/profile.example.json` shows the same structure with placeholder data, for reference.

## Why this exists

Built as a learning project — to understand how an AI agent (brain + memory + tools) actually works end to end, one small, reviewed piece at a time, rather than using an off-the-shelf tool.
