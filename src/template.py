"""
Lays out a tailored resume selection into a formatted HTML document.

No AI is involved anywhere in this file - it is plain, deterministic
code that mechanically fills a fixed template, which is exactly what
guarantees the format rules in docs/resume-rules.md (single column,
correct fonts, standard section order) can never be broken, no matter
what the AI wrote in resume.py.
"""

import html


def build_resume_html(profile, result):
    """
    Combines your profile (for contact info and education, which never
    change per job) with a tailored selection (for everything else)
    into one complete, formatted HTML resume.

    Parameters:
        profile: the full profile dict, same shape as profile.json.
        result: the dict returned by resume.tailor_resume() - the
            AI's selection of summary/experience/projects/skills/
            achievements for one specific job.

    Returns a complete HTML document as a string, ready to be rendered
    to PDF.
    """
    personal = profile["personal"]
    exp_by_company = {e["company"]: e for e in profile["experience"]}
    proj_by_name = {p["name"]: p for p in profile["projects"]}

    sections = [
        _build_header(personal),
        _build_summary(result.get("summary")),
        _build_skills(result.get("skills", []), profile["skills"]),
        _build_experience(result.get("experience", []), exp_by_company),
        _build_education(profile["education"]),
        _build_projects(result.get("projects", []), proj_by_name),
        _build_achievements(result.get("achievements", [])),
    ]

    return _PAGE_TEMPLATE.format(
        name=_esc(personal["name"]),
        body="\n".join(s for s in sections if s),
    )


def _build_header(personal):
    """
    Builds the name + contact line at the top of the resume, from the
    profile's "personal" section - never touched by the AI.
    """
    links = personal.get("links", {})
    parts = [f'<a href="mailto:{_esc(personal["email"])}">{_esc(personal["email"])}</a>']
    if personal.get("phone"):
        parts.append(_esc(personal["phone"]))
    if links.get("github"):
        parts.append(f'<a href="{_esc(links["github"])}">GitHub</a>')
    if links.get("linkedin"):
        parts.append(f'<a href="{_esc(links["linkedin"])}">LinkedIn</a>')
    if links.get("website"):
        parts.append(f'<a href="{_esc(links["website"])}">Portfolio</a>')

    contact_line = f' <span class="sep">|</span> '.join(parts)
    return f'<h1>{_esc(personal["name"])}</h1>\n<div class="contact">{contact_line}</div>'


def _build_summary(summary):
    """
    Builds the optional Summary section - skipped entirely if the AI
    did not provide one, since resume-rules.md marks it optional.
    """
    if not summary or not summary.get("text"):
        return ""
    return f'<h2>Summary</h2>\n<p class="summary">{_esc(summary["text"])}</p>'


def _build_skills(skills, profile_skills):
    """
    Builds the Skills section, grouped under the same category labels
    (Languages/Systems/Tools) as the profile - rather than one flat,
    undifferentiated line, which is harder to scan quickly.

    Parameters:
        skills: the AI's already-selected flat list of skill names.
        profile_skills: the profile's "skills" dict (with "languages",
            "systems", "tools" lists), used to look up which category
            each selected skill belongs to.
    """
    if not skills:
        return ""

    categories = [("languages", "Languages"), ("systems", "Systems"), ("tools", "Tools")]
    skill_to_category = {
        name: key for key, _ in categories for name in profile_skills.get(key, [])
    }

    grouped = {key: [] for key, _ in categories}
    other = []
    for skill in skills:
        category = skill_to_category.get(skill)
        (grouped[category] if category else other).append(skill)

    rows = []
    for key, label in categories:
        if grouped[key]:
            rows.append(f'<div class="skills-row"><b>{label}:</b> {_esc(", ".join(grouped[key]))}</div>')
    if other:
        rows.append(f'<div class="skills-row"><b>Other:</b> {_esc(", ".join(other))}</div>')

    return "<h2>Skills</h2>\n" + "\n".join(rows)


def _build_experience(experience, exp_by_company):
    """
    Builds the Experience section. Looks up each entry's location and
    dates from the profile by company name, since the AI's output
    only carries company/title/highlights, not those fixed details.
    """
    if not experience:
        return ""

    entries = []
    for entry in experience:
        source = exp_by_company.get(entry["company"], {})
        dates = _format_date_range(source.get("start_date"), source.get("end_date"))
        role_line = entry["title"]
        if source.get("location"):
            role_line += f', {source["location"]}'

        items = "\n".join(
            f"      <li>{_esc(h['text'])}</li>" for h in entry.get("highlights", [])
        )

        entries.append(
            f"""  <div class="entry">
    <div class="row">
      <div class="left">{_esc(entry['company'])}</div>
      <div class="right">{_esc(dates)}</div>
    </div>
    <div class="row">
      <div class="role">{_esc(role_line)}</div>
      <div class="right"></div>
    </div>
    <ul>
{items}
    </ul>
  </div>"""
        )

    return "<h2>Experience</h2>\n" + "\n".join(entries)


def _build_education(education):
    """Builds the Education section directly from the profile - not tailored."""
    if not education:
        return ""

    entries = []
    for entry in education:
        dates = f'{entry.get("start_date", "")} – {entry.get("end_date", "")}'
        role_line = entry["degree"]
        if entry.get("gpa"):
            role_line += f' — CGPA: {entry["gpa"]}'
        entries.append(
            f"""  <div class="row">
    <div class="left">{_esc(entry['institution'])}</div>
    <div class="right">{_esc(dates)}</div>
  </div>
  <div class="row">
    <div class="role">{_esc(role_line)}</div>
    <div class="right"></div>
  </div>"""
        )

    return "<h2>Education</h2>\n" + "\n".join(entries)


def _build_projects(projects, proj_by_name):
    """
    Builds the Projects section. Looks up each entry's GitHub link
    from the profile by project name - left blank for the projects
    that genuinely do not have one, rather than guessing.
    """
    if not projects:
        return ""

    entries = []
    for project in projects:
        source = proj_by_name.get(project["name"], {})
        link = source.get("link", "")
        link_display = link.replace("https://github.com/", "github.com/") if link else ""
        tech = ", ".join(project.get("tech", []))
        description = project.get("description", {})
        text = description.get("text", "") if isinstance(description, dict) else ""

        entries.append(
            f"""  <div class="entry">
    <div class="row">
      <div class="left">{_esc(project['name'])} <span class="proj-links">({_esc(tech)})</span></div>
      <div class="right">{_esc(link_display)}</div>
    </div>
    <ul>
      <li>{_esc(text)}</li>
    </ul>
  </div>"""
        )

    return "<h2>Projects</h2>\n" + "\n".join(entries)


def _build_achievements(achievements):
    """
    Builds the Achievements section - always copied verbatim, never
    reworded. Rendered as bold, bullet-free lines (one credential per
    line) rather than a plain bulleted list, since a row of bullet
    dots reads as more "job description," while bold standalone lines
    read more clearly as a list of credentials.
    """
    if not achievements:
        return ""
    items = "\n".join(f"    <p>{_esc(a)}</p>" for a in achievements)
    return f'<h2>Achievements</h2>\n<div class="achievements">\n{items}\n</div>'


def _format_date_range(start, end):
    """Formats a start/end date pair for display, e.g. "Jul 2025 - Present"."""
    if not start:
        return ""
    return f"{start} – {end or 'Present'}"


def _esc(text):
    """Escapes text for safe use inside HTML, e.g. turning & into &amp;."""
    return html.escape(str(text))


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{name} — Resume</title>
<style>
  @page {{
    size: Letter;
    /* margin-top applies to every printed page, unlike body padding
       (which only applies once, at the very start of the content) -
       this is what gives page 2+ the same top breathing room as
       page 1, instead of starting flush against the edge. */
    margin: 0.35in 0 0 0;
  }}

  * {{
    box-sizing: border-box;
  }}

  body {{
    margin: 0;
    padding: 0 0.65in 0.35in 0.65in;

    font-family: "Times New Roman", Georgia, serif;
    font-size: 9.6pt;
    line-height: 1.2;
    color: #111;

    font-variant-ligatures: none;
    -webkit-font-variant-ligatures: none;
    font-feature-settings: "liga" 0, "clig" 0, "dlig" 0;
  }}

  h1 {{
    margin: 0 0 3px;
    text-align: center;
    font-size: 20pt;
    letter-spacing: 0.5px;
  }}

  .contact {{
    text-align: center;
    font-size: 9.3pt;
    margin-bottom: 10px;
  }}

  .contact a {{
    color: #111;
    text-decoration: none;
  }}

  .contact span.sep {{
    margin: 0 6px;
    color: #888;
  }}

  h2 {{
    font-size: 10.5pt;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 1px solid #111;
    margin: 8px 0 3px;
    padding-bottom: 1px;

    /* Never leave a section heading stranded alone at the bottom of a
       page with its content pushed to the next one. */
    page-break-after: avoid;
    break-after: avoid;
  }}

  .row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
  }}

  .row .left {{
    font-weight: bold;
  }}

  .row .role {{
    font-style: italic;
    font-weight: normal;
  }}

  .row .right {{
    white-space: nowrap;
    font-style: italic;
    font-size: 9.7pt;
  }}

  ul {{
    margin: 2px 0 5px;
    padding-left: 16px;
  }}

  li {{
    margin: 0.5px 0;
  }}

  .entry {{
    margin-bottom: 1px;

    /* Keep a whole job/project entry (title, dates, bullets) together -
       if it doesn't fit in the space left on a page, the entire entry
       moves to the next page rather than splitting mid-way. */
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .entry:last-child ul {{
    margin-bottom: 0;
  }}

  .proj-links {{
    font-weight: normal;
    font-style: normal;
    font-size: 9pt;
    color: #444;
  }}

  .skills-row {{
    margin: 3px 0;
  }}

  .summary {{
    margin: 0 0 6px;
  }}

  .achievements {{
    /* Keep the whole achievements list together, same reasoning as
       .entry above - it has no .entry wrapper of its own. */
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .achievements p {{
    margin: 2.5px 0;
    font-weight: bold;
  }}
</style>
</head>
<body>

{body}

</body>
</html>
"""
