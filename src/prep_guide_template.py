"""
Lays out a generated interview prep guide into a formatted HTML
document. No AI involved here - plain, deterministic code, same split
as every other *_template.py file in this project.
"""

import html


def build_prep_guide_html(profile, result, company_name=""):
    """
    Combines your generated introduction and talking points into one
    complete, formatted prep guide document.

    Parameters:
        profile: the full profile dict, same shape as profile.json.
        result: the dict returned by prep_guide.generate_prep_guide() -
            {"intro": {"text": "...", "sources": [...]},
            "talking_points": [{"title": "...", "text": "...", "sources": [...]}]}.
        company_name: optional company name for the document title.

    Returns a complete HTML document as a string, ready to render to PDF.
    """
    title = f"Interview Prep — {company_name}" if company_name else "Interview Prep"
    intro_text = (result.get("intro") or {}).get("text", "")

    points_html = "\n".join(
        f"""  <div class="point">
    <p class="point-title">{_esc(point.get('title', ''))}</p>
    <p class="point-text">{_esc(point.get('text', ''))}</p>
  </div>"""
        for point in result.get("talking_points", [])
    )

    return _PAGE_TEMPLATE.format(
        page_title=_esc(title),
        heading=_esc(title),
        intro=_esc(intro_text),
        points=points_html,
    )


def _esc(text):
    """Escapes text for safe use inside HTML, e.g. turning & into &amp;."""
    return html.escape(str(text))


_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>{page_title}</title>
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
    padding: 0 0.65in 0.4in 0.65in;

    font-family: "Times New Roman", Georgia, serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #111;

    font-variant-ligatures: none;
    -webkit-font-variant-ligatures: none;
    font-feature-settings: "liga" 0, "clig" 0, "dlig" 0;
  }}

  h1 {{
    margin: 0 0 20px;
    text-align: center;
    font-size: 16pt;
    letter-spacing: 0.3px;
  }}

  h2 {{
    font-size: 11pt;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    border-bottom: 1px solid #111;
    margin: 20px 0 8px;
    padding-bottom: 2px;
  }}

  .intro {{
    margin: 0;
    text-align: justify;
  }}

  .point {{
    margin-bottom: 10px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .point-title {{
    margin: 0 0 2px;
    font-weight: bold;
  }}

  .point-text {{
    margin: 0;
    color: #222;
  }}
</style>
</head>
<body>

<h1>{heading}</h1>

<h2>Your Introduction</h2>
<p class="intro">{intro}</p>

<h2>Key Talking Points</h2>
{points}

</body>
</html>
"""
