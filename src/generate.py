"""
The single entry point that turns a job description into a finished
resume PDF - wiring together every piece built so far: tailoring,
citation verification, HTML layout, and PDF rendering.
"""

import json
import os
import subprocess
import sys

from job_posting import fetch_job_description
from resume import tailor_resume, verify_citations
from template import build_resume_html

PROFILE_PATH = "data/profile.json"

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def generate_resume(job_url, output_path):
    """
    Produces a tailored resume PDF for one specific job posting.

    Parameters:
        job_url: the web address of the job posting to tailor toward.
        output_path: where to write the finished PDF file, e.g.
            "output/resume.pdf".

    Example: generate_resume("https://example.com/jobs/123", "out.pdf")
    writes out.pdf and returns nothing if everything checks out.

    Raises a clear error and does NOT write a PDF if the page cannot
    be downloaded, or if any citation fails verification - an
    unverified resume should never be silently produced.
    """
    with open(PROFILE_PATH) as f:
        profile = json.load(f)

    job_description = fetch_job_description(job_url)
    result = tailor_resume(job_description)

    problems = verify_citations(result, profile)
    if problems:
        problem_list = "\n".join(f"  - {p}" for p in problems)
        raise ValueError(
            "Citation check failed - refusing to produce a resume with "
            f"unverified claims:\n{problem_list}"
        )

    html_doc = build_resume_html(profile, result)
    html_path = output_path.rsplit(".", 1)[0] + ".html"
    with open(html_path, "w") as f:
        f.write(html_doc)

    _render_pdf(html_path, output_path)


def _render_pdf(html_path, pdf_path):
    """
    Converts an HTML file into a PDF using headless Chrome - the same
    approach used for the personal website resume, so the same font
    rendering and page rules apply here too.

    Parameters:
        html_path: path to the HTML file to render.
        pdf_path: where to write the resulting PDF.

    Raises a clear error if Chrome fails or does not produce a file,
    instead of silently leaving no PDF behind.
    """
    result = subprocess.run(
        [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            "--print-to-pdf-no-header",
            f"file://{os.path.abspath(html_path)}",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Chrome failed to render the PDF:\n{result.stderr}")


if __name__ == "__main__":
    # Usage: python3 src/generate.py <job posting URL> [output_path]
    if len(sys.argv) < 2:
        print("Usage: python3 src/generate.py <job posting URL> [output_path]")
        sys.exit(1)

    job_url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output/resume.pdf"

    try:
        generate_resume(job_url, output_path)
        print(f"Resume written to {output_path}")
    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}")
        sys.exit(1)
