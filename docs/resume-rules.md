# Resume Tailoring Rules

This document is the contract the resume-generation tool in this repo follows. Every resume it produces must satisfy every rule below, and every rule below has a corresponding automated check (see [Verification and Testing](#verification-and-testing)) that runs before a resume is considered finished.

The source of truth for all facts is [`data/profile.json`](../data/profile.json) (a real copy stays local-only and untracked — see `data/profile.example.json` for the shape). Nothing in a generated resume may exist outside that file.

## 1. Format rules

These exist because ATS (Applicant Tracking System) parsers are simple, literal text extractors — not humans. A resume that looks fine to a person can still get mangled or silently rejected by one.

- **Single column only.** A two-column layout makes ATS parsers read the left and right columns in the wrong order, interleaving unrelated text into nonsense.
- **Standard section order:** Contact → Summary (optional) → Skills → Experience → Education → Projects → Achievements.
- **Real, selectable text.** Never an image or a screenshot of text.
- **Safe fonts only:** Times New Roman, Arial, Calibri, Georgia, or Helvetica.
- **1 page** by default. 2 pages only if explicitly justified — never as a default.
- **Standard section headers** (`Experience`, `Education`, `Skills`, `Projects`) — not creative alternatives like "My Journey."

## 2. Content rules

- Each bullet: **action verb + what was done + measurable result**, ~20-25 words max.
- **Quantify wherever the fact is real.** A number is only used if it is true and traceable to `profile.json` — never invented to sound more impressive.
- **Match the job description's exact keywords** where honestly applicable — ATS keyword matching is often literal, so close synonyms can fail to register.
- **Achievements (competitions, ratings, honors) are copied verbatim, never reworded** — these are precise factual claims where rewording risks distorting them.

## 3. Tailoring rule

For each specific job, the tool reads the job description and selects the subset of `profile.json` most relevant to it — not everything, not padding. Different roles should surface different experience bullets, different projects (out of the full pool in the profile), and a different skills emphasis. There is no single fixed "target resume" — every output is generated per job description.

## 4. Anti-fabrication rule (the most important one)

**The tool may only select and rephrase facts already present in `data/profile.json`. It may never invent a new number, company, scope of responsibility, or achievement.**

This matters more than any formatting rule: a false claim on a resume can surface as a follow-up question in an interview that has no honest answer. If a bullet needs a fact that isn't in the profile, the fix is to add that fact to the profile first — not to write around it.

## Verification and Testing

Every generated resume is run through three kinds of checks before being handed back as finished. Failing any of these means the resume is not done — it's flagged with what specifically failed, the same way a failing test names the broken assertion.

### A. Format checks (mechanical)
- Page count is exactly 1 (or 2, only if explicitly allowed for this run)
- The PDF's extracted text (via `pdftotext`, the same tool used to verify the personal-website resume earlier) reads cleanly, in the correct order, nothing garbled or dropped
- No leftover placeholder text (`TODO`, `{{...}}`, etc.)
- All required sections present, using standard header names

### B. Honesty check (the most important check)
- A second, independent pass compares every specific claim in the generated resume against `data/profile.json` and flags anything not traceable to a real entry — a second reviewer fact-checking the first, specifically for fabrication.

### C. Tailoring-quality check
- Key terms are extracted from the job description; the tool measures how many appear in the generated resume and flags a low-overlap result as under-tailored.
- The fraction of experience bullets that are quantified is measured (target: majority of bullets, based on general resume research showing quantified bullets perform meaningfully better).

## Change history

- 2026-09-15: Initial rules drafted and agreed on with Raja.
