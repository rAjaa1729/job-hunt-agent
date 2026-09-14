# job-hunt-agent

A personal AI agent that tailors a resume to a specific job description, using a single structured profile as its only source of truth — and (eventually) tracks applications end to end.

## How it's meant to work

1. **Profile** — all real background facts (experience, projects, skills, links) live in one structured file, `data/profile.json`. This is the only thing the agent is ever allowed to draw facts from.
2. **Tailoring** — given a job description, the agent picks the subset of the profile most relevant to that specific role and writes a resume from it. See [`docs/resume-rules.md`](docs/resume-rules.md) for the exact rules every generated resume must follow, and the checks used to verify it.
3. **Tracking** *(planned)* — logging applications and their status over time.
4. **Autofill** *(planned, later)* — filling out application forms, once the safer pieces above are solid.

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
