"""
Generates the kind of free-text questions a job application form is
likely to ask for a specific posting, plus a grounded, citation-backed
draft answer for each one where the profile actually has a real
answer - same trust pattern as resume.py and cover_letter.py.
"""

import json

from llm import call_llm
from resume import PROFILE_PATH, _parse_json_reply, _resolve_path

NUM_QUESTIONS = 8

SYSTEM_PROMPT = f"""You are helping someone prepare to fill out a job
application form by predicting what it is likely to ask, and drafting
answers they can review and paste in.

Generate exactly {NUM_QUESTIONS} realistic, open-ended questions that
this SPECIFIC application form is likely to include - the kind of
free-text questions application forms commonly ask, such as:
- Why do you want to work at this company / in this role?
- Describe relevant experience for this specific position.
- Role- or technology-specific screening questions implied by the job
  description (only if genuinely relevant to this posting).
- Logistics questions (notice period, visa/work authorization, salary
  expectations, willingness to relocate) only if plausible for this
  type of role.

For each question, decide whether it is answerable from the profile:

- If it is about background, experience, projects, skills, or fit
  (something the profile can genuinely answer), write a draft answer
  using ONLY facts that exist in the profile JSON given to you - never
  invent a number, company, project, or achievement. Include a
  "sources" field: a list of exact paths to where the facts came from,
  e.g. "experience[0].highlights[2]" or "projects[3].description".
  Use [N] only for items inside a list, and .fieldname (no brackets)
  for a named field inside an object.

- If it is a personal/logistics question the profile cannot answer
  (notice period, salary expectations, visa status, availability date,
  and similar), do NOT guess or invent an answer. Set "answer" to null
  and "needs_personal_input" to true instead.

Respond with ONLY valid JSON matching this exact shape - no explanation,
no markdown code fences, nothing before or after the JSON:

{{
  "items": [
    {{
      "question": "...",
      "answer": {{"text": "...", "sources": ["path.to.field", "..."]}},
      "needs_personal_input": false
    }},
    {{
      "question": "What is your notice period?",
      "answer": null,
      "needs_personal_input": true
    }}
  ]
}}"""


def generate_qa(job_description):
    """
    Given a job description, predicts the free-text questions its
    application form is likely to ask, and drafts an answer for each
    one that the profile can genuinely answer - so you have a strong
    starting draft to review and paste in, instead of writing cold.

    Parameters:
        job_description: the plain-text job posting to tailor toward.

    Returns a dict like:
        {"items": [{"question": "...", "answer": {"text": "...",
        "sources": [...]} or None, "needs_personal_input": bool}]}

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

    reply = call_llm(messages, max_tokens=3000)
    return _parse_json_reply(reply)


def verify_qa_citations(result, profile):
    """
    Checks every citation in a Q&A result against the real profile,
    confirming each one points to a field that actually exists - same
    safety net as resume.verify_citations(), applied to Q&A answers.

    Parameters:
        result: the dict returned by generate_qa().
        profile: the full profile dict the answers should be grounded in.

    Returns a list of problem descriptions - empty if every citation
    checked out.
    """
    problems = []

    for i, item in enumerate(result.get("items", [])):
        answer = item.get("answer")
        if not answer:
            continue

        sources = answer.get("sources", [])
        if not sources:
            problems.append(f"items[{i}]: answer is missing source citations")
            continue

        for source in sources:
            try:
                _resolve_path(profile, source)
            except (KeyError, IndexError, ValueError, TypeError):
                problems.append(f"items[{i}]: source '{source}' does not exist in the profile")

    return problems


if __name__ == "__main__":
    # Manual sanity check: `python3 src/qa.py`
    sample_jd = (
        "Backend Software Engineer - we build high-throughput distributed "
        "systems in Python and C++, with a focus on database internals "
        "and low-latency performance. Strong CS fundamentals required."
    )
    result = generate_qa(sample_jd)
    print(json.dumps(result, indent=2))
