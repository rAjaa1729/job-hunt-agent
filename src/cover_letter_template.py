"""
Lays out a tailored cover letter into a formatted HTML document.

Same split as template.py/resume.py: no AI involved here at all. The
AI only wrote two body paragraphs (cover_letter.py); everything else
- greeting, closing, sign-off, layout - is fixed, deterministic code.
"""

import html

CLOSING_SENTENCE = (
    "I would welcome the opportunity to discuss how my background could "
    "contribute to your team."
)


def build_cover_letter_html(profile, result, company_name=""):
    """
    Combines your profile (for name, contact info, and the sign-off)
    with the AI's two tailored paragraphs into one complete, formatted
    cover letter document.

    Parameters:
        profile: the full profile dict, same shape as profile.json.
        result: the dict returned by cover_letter.tailor_cover_letter()
            - {"paragraphs": [{"text": "...", "sources": [...]}, ...]}.
        company_name: optional company name to address the letter to,
            e.g. "Google" - falls back to "Hiring Manager" if not given.

    Returns a complete HTML document as a string, ready to render to PDF.
    """
    personal = profile["personal"]
    ai_paragraphs = [p["text"] for p in result.get("paragraphs", [])]

    body_paragraphs = ai_paragraphs + [CLOSING_SENTENCE]
    paragraphs_html = "\n".join(f"  <p>{_esc(text)}</p>" for text in body_paragraphs)

    greeting = f"Dear {_esc(company_name)} Hiring Team," if company_name else "Dear Hiring Manager,"

    return _PAGE_TEMPLATE.format(
        name=_esc(personal["name"]),
        header=_build_header(personal),
        greeting=greeting,
        paragraphs=paragraphs_html,
        signature=_esc(personal["name"]),
    )


def _build_header(personal):
    """Builds the name + contact line at the top of the letter, same style as the resume."""
    links = personal.get("links", {})
    parts = [f'<a href="mailto:{_esc(personal["email"])}">{_esc(personal["email"])}</a>']
    if personal.get("phone"):
        parts.append(_esc(personal["phone"]))
    if links.get("github"):
        parts.append(f'<a href="{_esc(links["github"])}">GitHub</a>')
    if links.get("linkedin"):
        parts.append(f'<a href="{_esc(links["linkedin"])}">LinkedIn</a>')

    contact_line = ' <span class="sep">|</span> '.join(parts)
    return f'<h1>{_esc(personal["name"])}</h1>\n<div class="contact">{contact_line}</div>'


def _esc(text):
    """Escapes text for safe use inside HTML, e.g. turning & into &amp;."""
    return html.escape(str(text))


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{name} — Cover Letter</title>
<style>
  @page {{
    size: Letter;
    margin: 0.4in 0 0 0;
  }}

  * {{
    box-sizing: border-box;
  }}

  body {{
    margin: 0;
    padding: 0 0.75in 0.4in 0.75in;

    font-family: "Times New Roman", Georgia, serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #111;

    font-variant-ligatures: none;
    -webkit-font-variant-ligatures: none;
    font-feature-settings: "liga" 0, "clig" 0, "dlig" 0;
  }}

  h1 {{
    margin: 0 0 4px;
    text-align: center;
    font-size: 18pt;
    letter-spacing: 0.5px;
  }}

  .contact {{
    text-align: center;
    font-size: 10pt;
    margin-bottom: 28px;
  }}

  .contact a {{
    color: #111;
    text-decoration: none;
  }}

  .contact span.sep {{
    margin: 0 6px;
    color: #888;
  }}

  .greeting {{
    margin: 0 0 14px;
  }}

  p {{
    margin: 0 0 14px;
    text-align: justify;
  }}
</style>
</head>
<body>

{header}

<p class="greeting">{greeting}</p>

{paragraphs}

<p>Sincerely,<br />{signature}</p>

</body>
</html>
"""
