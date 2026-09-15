"""
Turns a job description into a tailored, citation-grounded cover
letter body - the same trust pattern as resume.py, applied to flowing
paragraphs instead of bullet points.
"""

import json
import re

from llm import call_llm
from resume import PROFILE_PATH, _parse_json_reply, _resolve_path

SYSTEM_PROMPT = """
You are helping write the body paragraphs of a cover letter for a
specific job description.

RULES YOU MUST FOLLOW EXACTLY:

1. Write in FIRST PERSON, as the candidate speaking for themselves -
   "I designed...", "I am writing...", never "Raja designed..." or
   "The candidate...". The profile data is written in third person;
   translate it into first person as you write.

2. You may only reference facts that already exist in the profile JSON
   given to you. Never invent a new number, company, project, skill, or
   achievement. If a fact is not in the profile, it cannot appear in your
   output.

3. For every paragraph, include a "sources" field: a list of exact paths
   to where the facts in that paragraph came from in the profile, e.g.
   "experience[0].highlights[2]" or "projects[3].description". Use [N]
   only for items inside a list, and .fieldname (no brackets) for a named
   field inside an object, e.g. "personal.links.github".

4. Write exactly 2 paragraphs:
   - Paragraph 1 (Opening): what role and company this is for, and a
     one-line hook connecting the candidate to it.
   - Paragraph 2 (Body): the strongest 1-2 pieces of real experience or
     projects that match this specific job description, briefly explained.

5. Do NOT include a greeting ("Dear...") or a sign-off ("Sincerely...")
   - those are added separately, outside your output. Do NOT write a
   closing paragraph either - that is also added separately.

6. Keep the whole letter short enough to fit on one page - roughly
   180-250 words total across both paragraphs.

Respond with ONLY valid JSON matching this exact shape - no explanation,
no markdown code fences, nothing before or after the JSON:

{
  "paragraphs": [
    {"text": "...", "sources": ["path.to.field", "..."]}
  ]
}"""


def tailor_cover_letter(job_description):
    """
    Given a job description, writes a grounded, citation-backed cover
    letter body - three paragraphs, each referencing only real facts
    from your profile.

    Parameters:
        job_description: the plain-text job posting to tailor toward.

    Returns a dict like {"paragraphs": [{"text": "...", "sources": [...]}]}
    - the raw paragraph data, not a formatted letter yet (a separate,
    later step lays this out into an actual document).

    Raises a clear error if the AI's response cannot be parsed as
    valid JSON, instead of silently returning something broken.
    """
    with open(PROFILE_PATH) as f:
        profile = json.load(f)

    user_message = (
        "PROFILE:\n"
        + json.dumps(profile, indent=2)
        + "\n\nJOB DESCRIPTION:\n"
        + job_description.strip()
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    reply = call_llm(messages, max_tokens=4000)
    return _parse_json_reply(reply)


def verify_cover_letter_citations(result, profile):
    """
    Checks every citation in a cover letter result against the real
    profile, confirming each one points to a field that actually
    exists - same safety net as resume.verify_citations(), applied to
    paragraphs instead of resume sections.

    Parameters:
        result: the dict returned by tailor_cover_letter().
        profile: the full profile dict the letter should be grounded in.

    Returns a list of problem descriptions - empty if every citation
    checked out.
    """
    problems = []

    for i, paragraph in enumerate(result.get("paragraphs", [])):
        sources = paragraph.get("sources", [])
        if not sources:
            problems.append(f"paragraph[{i}]: missing source citations")
            continue
        for source in sources:
            try:
                _resolve_path(profile, source)
            except (KeyError, IndexError, ValueError, TypeError):
                problems.append(f"paragraph[{i}]: source '{source}' does not exist in the profile")

    return problems


if __name__ == "__main__":
    # Manual sanity check: `python3 src/cover_letter.py`
    sample_jd = (
        "Backend Software Engineer - we build high-throughput distributed "
        "systems in Python and C++, with a focus on database internals "
        "and low-latency performance. Strong CS fundamentals required."
    )
    result = tailor_cover_letter(sample_jd)
    print(json.dumps(result, indent=2))
