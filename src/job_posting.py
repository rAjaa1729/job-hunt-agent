"""
Downloads a job posting from a URL and pulls out just the actual job
description text, ignoring navigation menus, ads, and other page
clutter around it.
"""

import subprocess

from bs4 import BeautifulSoup

from llm import call_llm

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Reasonable ceiling on how much raw page text gets sent to the AI -
# keeps the request fast and leaves room in the context window for
# the profile and everything else that goes into later prompts.
MAX_RAW_TEXT_CHARS = 10000

EXTRACTION_PROMPT = """You are given the raw text of a job posting webpage,
which includes unrelated clutter (navigation menus, cookie notices,
unrelated links, footers, etc.) mixed in with the actual job posting.

Extract and return ONLY the real job posting content - title, company,
responsibilities, requirements, and similar - with the clutter removed.
Do not summarize or add commentary, just return the cleaned-up text."""


def fetch_job_description(url):
    """
    Downloads a job posting webpage and returns just the job
    description text, with page clutter removed.

    Parameters:
        url: the web address of the job posting.

    Example: fetch_job_description("https://example.com/jobs/123")
    returns a plain-text job description, ready to pass to
    resume.tailor_resume().

    Uses a real, headless copy of Chrome to load the page (not a
    plain HTTP request), so pages that load their content via
    JavaScript after the initial load - which turned out to be most
    major tech company career sites - are captured correctly too.

    Raises a clear error if the page cannot be downloaded.
    """
    html = _render_page(url)
    raw_text = _extract_readable_text(html)
    raw_text = raw_text[:MAX_RAW_TEXT_CHARS]

    messages = [
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": raw_text},
    ]
    return call_llm(messages, max_tokens=2000)


def _render_page(url):
    """
    Loads a webpage in headless Chrome, waits for its JavaScript to
    finish running, and returns the fully rendered page as HTML.

    Parameters:
        url: the web address to load.

    Example: _render_page("https://example.com") returns that page's
    complete HTML, including content that only appeared after
    JavaScript ran - unlike a plain HTTP request, which only sees the
    page's initial, unrendered state.
    """
    result = subprocess.run(
        [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--dump-dom",
            "--virtual-time-budget=8000",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0 or not result.stdout:
        raise RuntimeError(f"Could not download the job posting page:\n{result.stderr}")

    return result.stdout


def _extract_readable_text(html):
    """
    Strips HTML markup down to plain readable text, discarding script
    and style tags entirely since they are never real page content.

    Parameters:
        html: the raw HTML of a webpage, as a string.

    Example: _extract_readable_text("<script>...</script><p>Hello</p>")
    returns "Hello" - the script tag's content is dropped completely.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


if __name__ == "__main__":
    # Manual sanity check: `python3 src/job_posting.py <url>`
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 src/job_posting.py <job posting URL>")
        sys.exit(1)

    description = fetch_job_description(sys.argv[1])
    print(description)
