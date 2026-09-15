"""
Lays out generated application Q&A into a formatted HTML document.

No AI involved here - plain, deterministic code that fills a fixed
template, same split as template.py and cover_letter_template.py.
"""

import html

PLACEHOLDER_TEXT = "— fill in yourself (not something your profile can answer) —"


def build_qa_html(profile, result, company_name=""):
    """
    Combines the generated question/answer pairs into one complete,
    formatted document - draft answers ready to review and copy into
    the real application form, with personal/logistics questions
    clearly marked for you to answer yourself.

    Parameters:
        profile: the full profile dict, same shape as profile.json.
        result: the dict returned by qa.generate_qa() -
            {"items": [{"question": "...", "answer": {...} or None,
            "needs_personal_input": bool}, ...]}.
        company_name: optional company name for the document title.

    Returns a complete HTML document as a string, ready to render to PDF.
    """
    title = f"Application Q&A — {company_name}" if company_name else "Application Q&A"

    items_html = "\n".join(_build_item(item) for item in result.get("items", []))

    return _PAGE_TEMPLATE.format(
        page_title=_esc(title),
        heading=_esc(title),
        items=items_html,
    )


def _build_item(item):
    """Builds one question block: the question, then its draft answer or a fill-in-yourself note."""
    if item.get("needs_personal_input") or not item.get("answer"):
        answer_text = PLACEHOLDER_TEXT
        answer_class = "placeholder"
    else:
        answer_text = item["answer"].get("text", "")
        answer_class = "answer"

    return f"""  <div class="item">
    <p class="question">{_esc(item['question'])}</p>
    <p class="{answer_class}">{_esc(answer_text)}</p>
  </div>"""


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
    font-size: 10.5pt;
    line-height: 1.4;
    color: #111;

    font-variant-ligatures: none;
    -webkit-font-variant-ligatures: none;
    font-feature-settings: "liga" 0, "clig" 0, "dlig" 0;
  }}

  h1 {{
    margin: 0 0 18px;
    text-align: center;
    font-size: 16pt;
    letter-spacing: 0.3px;
  }}

  .item {{
    margin-bottom: 14px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  .question {{
    margin: 0 0 4px;
    font-weight: bold;
  }}

  .answer {{
    margin: 0;
    color: #222;
  }}

  .placeholder {{
    margin: 0;
    font-style: italic;
    color: #888;
  }}
</style>
</head>
<body>

<h1>{heading}</h1>

{items}

</body>
</html>
"""
