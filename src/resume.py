"""
Turns a job description into a tailored, structured resume selection.

This is where the rules from docs/resume-rules.md actually get enforced
in a prompt: the AI is only allowed to pick and lightly reword content
that already exists in data/profile.json, and must cite exactly which
part of the profile each rewritten line came from.
"""

import json
import re

from llm import call_llm

PROFILE_PATH = "data/profile.json"

MIN_PROJECTS = 3
MAX_PROJECTS = 6

SYSTEM_PROMPT = f"""
You are helping tailor a resume to a specific job description.

RULES YOU MUST FOLLOW EXACTLY:

1. You may only select and lightly reword facts that already exist in the
   profile JSON given to you. Never invent a new number, company, project,
   skill, or achievement. If a fact is not in the profile, it cannot appear
   in your output.

2. For every rewritten sentence (in "summary", experience "highlights", and
   project "description" fields), you must include a "source" field: the
   exact path to where that fact came from in the profile.

   Path notation rules:
   - Use [N] (a number) only for items inside a LIST, e.g. "experience[0]"
     is the first experience entry, "experience[0].highlights[2]" is its
     third highlight.
   - Use .fieldname (no brackets) for a NAMED field inside an object, e.g.
     "personal.links.github" (never "personal[0].links[0]" - personal and
     links are named objects, not lists).
   - Correct examples: "experience[1].highlights[0]", "projects[3].description",
     "personal.links.github", "skills.languages[2]".

   Every path must point to a real field that actually exists in the given
   profile - do not guess at a path's shape.

3. Fields like company, title, project name, tech, skills, and achievements
   must be copied exactly as written in the profile - never reworded.

4. Select between {MIN_PROJECTS} and {MAX_PROJECTS} projects - the most
   relevant ones for this specific job description, using each project's
   "priority" field in the profile as a tiebreaker when relevance is close.

5. Achievements are copied verbatim, never reworded.

Respond with ONLY valid JSON matching this exact shape - no explanation,
no markdown code fences, nothing before or after the JSON:

{{
  "summary": {{"text": "...", "sources": ["path.to.field", "..."]}},
  "experience": [
    {{"company": "...", "title": "...", "highlights": [
      {{"text": "...", "source": "experience[0].highlights[0]"}}
    ]}}
  ],
  "projects": [
    {{"name": "...", "tech": ["..."], "description": {{"text": "...", "source": "projects[0].description"}}}}
  ],
  "skills": ["..."],
  "achievements": ["..."]
}}"""


def tailor_resume(job_description):
    """
    Given a job description, decides which parts of your profile to
    include and how to phrase them, following the rules above.

    Parameters:
        job_description: the plain-text job posting to tailor toward.

    Returns a dict matching the schema in SYSTEM_PROMPT - the raw
    selection data, not a formatted resume document yet (that is a
    separate, later step that mechanically lays this out into HTML).

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

    reply = call_llm(messages, max_tokens=8000)
    return _parse_json_reply(reply)


def _parse_json_reply(reply):
    """
    Pulls a JSON object out of the AI's reply text, even if it added
    stray text or markdown code fences around it despite being told
    not to - a small safety net, not something to rely on instead of
    clear instructions.

    Parameters:
        reply: the raw text returned by the AI.

    Raises a clear error, including the raw reply, if no valid JSON
    object can be found - so a broken response is obvious to debug
    instead of failing somewhere else in a confusing way.
    """
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in AI reply:\n{reply}")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as error:
        raise ValueError(f"AI reply was not valid JSON ({error}):\n{reply}") from None


def _resolve_path(profile, path):
    """
    Walks through the profile dict to find the value at an exact
    location described by a path string, and returns it.

    Parameters:
        profile: the full profile dict (same shape as profile.json).
        path: a location string like "experience[0].highlights[2]" or
            "projects[3].description" or "skills.systems[0]".

    Example: _resolve_path(profile, "projects[0].description") returns
    the description text of the first project in the profile.

    Raises a clear error if any part of the path does not exist -
    this is what makes a fabricated or wrong citation detectable.
    """
    tokens = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    current = profile
    for token in tokens:
        if token.startswith("["):
            current = current[int(token[1:-1])]
        else:
            current = current[token]
    return current


def verify_citations(result, profile):
    """
    Checks every citation in a tailored-resume result against the
    real profile, confirming each one points to a field that actually
    exists - the same check we did by hand to confirm the AI wasn't
    making things up, now automated.

    Parameters:
        result: the dict returned by tailor_resume().
        profile: the full profile dict the result should be grounded in.

    Returns a list of problem descriptions - empty if every citation
    checked out. Does not raise, so all problems can be reported at
    once instead of stopping at the first one found.
    """
    problems = []

    def check(source, context):
        if not source:
            problems.append(f"{context}: missing a source citation")
            return
        try:
            _resolve_path(profile, source)
        except (KeyError, IndexError, ValueError, TypeError):
            problems.append(f"{context}: source '{source}' does not exist in the profile")

    summary = result.get("summary") or {}
    for source in summary.get("sources", []):
        check(source, "summary")

    for i, entry in enumerate(result.get("experience", [])):
        for j, highlight in enumerate(entry.get("highlights", [])):
            check(highlight.get("source"), f"experience[{i}].highlights[{j}]")

    projects = result.get("projects", [])
    if not (MIN_PROJECTS <= len(projects) <= MAX_PROJECTS):
        problems.append(
            f"project count is {len(projects)}, expected between "
            f"{MIN_PROJECTS} and {MAX_PROJECTS}"
        )

    for i, project in enumerate(projects):
        description = project.get("description")
        if isinstance(description, dict):
            check(description.get("source"), f"projects[{i}].description")

    return problems


if __name__ == "__main__":
    # Manual sanity check: `python3 src/resume.py` with a short,
    # made-up job description, confirming the whole pipeline (prompt
    # -> AI -> parsing -> citation verification) runs cleanly.
    sample_jd = (
        "Backend Software Engineer - we build high-throughput distributed "
        "systems in Python and C++, with a focus on database internals "
        "and low-latency performance. Strong CS fundamentals required."
    )

    with open(PROFILE_PATH) as f:
        profile = json.load(f)

    result = tailor_resume(sample_jd)
    print(json.dumps(result, indent=2))

    problems = verify_citations(result, profile)
    print("\n--- Citation check ---")
    if problems:
        for p in problems:
            print("PROBLEM:", p)
    else:
        print("All citations verified against the profile.")
