"""
Generates a short interview prep guide - a self-introduction pitch and
a handful of key talking points tailored to a specific job. Same
citation-grounded trust pattern as resume.py and cover_letter.py.
"""

import json

from llm import call_llm
from resume import PROFILE_PATH, _parse_json_reply, _resolve_path

NUM_TALKING_POINTS = 4

SYSTEM_PROMPT = f"""
You are helping someone prepare for a job interview by drafting a
short self-introduction and a list of key talking points.

RULES YOU MUST FOLLOW EXACTLY:

1. Write in FIRST PERSON, as the candidate speaking for themselves -
   "I built...", "I am a...", never "Raja built..." or "The candidate...".

2. You may only reference facts that already exist in the profile JSON
   given to you. Never invent a new number, company, project, skill, or
   achievement.

3. For the intro and every talking point, include a "sources" field: a
   list of exact paths to where the facts came from in the profile, e.g.
   "experience[0].highlights[2]" or "projects[3].description". Use [N]
   only for items inside a list, and .fieldname (no brackets) for a
   named field inside an object.

4. Write a self-introduction of about 100-150 words: a "tell me about
   yourself" style spoken pitch specifically relevant to this job
   description - not a resume summary, something that sounds natural
   said out loud.

5. Select exactly {NUM_TALKING_POINTS} talking points - the strongest,
   most relevant real experiences or projects for this specific job,
   using each project's "priority" field in the profile as a tiebreaker
   when relevance is close. For each, write a "title" (the project or
   experience name, copied exactly) and a one to two sentence "text"
   explaining why it is worth bringing up for this specific role.

Respond with ONLY valid JSON matching this exact shape - no explanation,
no markdown code fences, nothing before or after the JSON:

{{
  "intro": {{"text": "...", "sources": ["path.to.field", "..."]}},
  "talking_points": [
    {{"title": "...", "text": "...", "sources": ["path.to.field", "..."]}}
  ]
}}"""


def generate_prep_guide(job_description):
    """
    Given a job description, drafts a short interview prep guide: a
    self-introduction pitch and a handful of key talking points, both
    grounded in and cited against your real profile.

    Parameters:
        job_description: the plain-text job posting to tailor toward.

    Returns a dict like:
        {"intro": {"text": "...", "sources": [...]},
         "talking_points": [{"title": "...", "text": "...", "sources": [...]}]}

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

    reply = call_llm(messages, max_tokens=2500)
    return _parse_json_reply(reply)


def verify_prep_guide_citations(result, profile):
    """
    Checks every citation in a prep guide result against the real
    profile, confirming each one points to a field that actually
    exists - same safety net as resume.verify_citations().

    Parameters:
        result: the dict returned by generate_prep_guide().
        profile: the full profile dict the guide should be grounded in.

    Returns a list of problem descriptions - empty if every citation
    checked out.
    """
    problems = []

    def check(sources, context):
        if not sources:
            problems.append(f"{context}: missing source citations")
            return
        for source in sources:
            try:
                _resolve_path(profile, source)
            except (KeyError, IndexError, ValueError, TypeError):
                problems.append(f"{context}: source '{source}' does not exist in the profile")

    intro = result.get("intro") or {}
    check(intro.get("sources", []), "intro")

    for i, point in enumerate(result.get("talking_points", [])):
        check(point.get("sources", []), f"talking_points[{i}]")

    return problems


if __name__ == "__main__":
    # Manual sanity check: `python3 src/prep_guide.py`
    sample_jd = (
        "Backend Software Engineer - we build high-throughput distributed "
        "systems in Python and C++, with a focus on database internals "
        "and low-latency performance. Strong CS fundamentals required."
    )
    result = generate_prep_guide(sample_jd)
    print(json.dumps(result, indent=2))
