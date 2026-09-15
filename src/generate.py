"""
The single entry point that turns a job posting into a complete
application package - wiring together every piece built so far:
fetching, tailoring, citation verification, HTML layout, and PDF
rendering, for the resume, cover letter, Q&A, and prep guide.
"""

import json
import os
import subprocess
import sys
from urllib.parse import urlparse

from cover_letter import tailor_cover_letter, verify_cover_letter_citations
from cover_letter_template import build_cover_letter_html
from job_posting import fetch_job_description
from prep_guide import generate_prep_guide, verify_prep_guide_citations
from prep_guide_template import build_prep_guide_html
from qa import generate_qa, verify_qa_citations
from qa_template import build_qa_html
from resume import tailor_resume, verify_citations
from template import build_resume_html

PROFILE_PATH = "data/profile.json"

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def generate_application(job_url, output_dir=None):
    """
    Produces a complete application package for one job posting: a
    tailored resume, cover letter, application form Q&A, and interview
    prep guide, all grounded in and verified against your real profile.

    Parameters:
        job_url: the web address of the job posting to tailor toward.
        output_dir: the folder to write into, e.g. "output/google".
            Defaults to a folder named after the job's company,
            derived from the URL.

    Example: generate_application("https://example.com/jobs/123")
    writes output/example/resume.pdf, cover_letter.pdf, qa.pdf, and
    prep_guide.pdf (each with a matching .html), and returns the
    folder path used.

    Raises a clear error and does NOT write a document if the page
    cannot be downloaded, or if any citation fails verification - an
    unverified document should never be silently produced.
    """
    output_dir = output_dir or _company_folder(job_url)
    os.makedirs(output_dir, exist_ok=True)
    company_name = _display_name(output_dir)

    with open(PROFILE_PATH) as f:
        profile = json.load(f)

    # Fetched once and reused for both documents, rather than hitting
    # the job posting URL twice.
    job_description = fetch_job_description(job_url)

    _generate_resume(profile, job_description, output_dir)
    _generate_cover_letter(profile, job_description, output_dir, company_name)
    _generate_qa(profile, job_description, output_dir, company_name)
    _generate_prep_guide(profile, job_description, output_dir, company_name)

    return output_dir


def _generate_resume(profile, job_description, output_dir):
    """Tailors, verifies, and renders the resume into output_dir/resume.pdf."""
    result = tailor_resume(job_description)

    problems = verify_citations(result, profile)
    if problems:
        problem_list = "\n".join(f"  - {p}" for p in problems)
        raise ValueError(
            "Resume citation check failed - refusing to produce a resume "
            f"with unverified claims:\n{problem_list}"
        )

    html_doc = build_resume_html(profile, result)
    html_path = os.path.join(output_dir, "resume.html")
    pdf_path = os.path.join(output_dir, "resume.pdf")
    with open(html_path, "w") as f:
        f.write(html_doc)

    _render_pdf(html_path, pdf_path)


def _generate_cover_letter(profile, job_description, output_dir, company_name):
    """Tailors, verifies, and renders the cover letter into output_dir/cover_letter.pdf."""
    result = tailor_cover_letter(job_description)

    problems = verify_cover_letter_citations(result, profile)
    if problems:
        problem_list = "\n".join(f"  - {p}" for p in problems)
        raise ValueError(
            "Cover letter citation check failed - refusing to produce a "
            f"letter with unverified claims:\n{problem_list}"
        )

    html_doc = build_cover_letter_html(profile, result, company_name)
    html_path = os.path.join(output_dir, "cover_letter.html")
    pdf_path = os.path.join(output_dir, "cover_letter.pdf")
    with open(html_path, "w") as f:
        f.write(html_doc)

    _render_pdf(html_path, pdf_path)


def _generate_qa(profile, job_description, output_dir, company_name):
    """Generates, verifies, and renders the application Q&A into output_dir/qa.pdf."""
    result = generate_qa(job_description)

    problems = verify_qa_citations(result, profile)
    if problems:
        problem_list = "\n".join(f"  - {p}" for p in problems)
        raise ValueError(
            "Q&A citation check failed - refusing to produce answers "
            f"with unverified claims:\n{problem_list}"
        )

    html_doc = build_qa_html(profile, result, company_name)
    html_path = os.path.join(output_dir, "qa.html")
    pdf_path = os.path.join(output_dir, "qa.pdf")
    with open(html_path, "w") as f:
        f.write(html_doc)

    _render_pdf(html_path, pdf_path)


def _generate_prep_guide(profile, job_description, output_dir, company_name):
    """Generates, verifies, and renders the interview prep guide into output_dir/prep_guide.pdf."""
    result = generate_prep_guide(job_description)

    problems = verify_prep_guide_citations(result, profile)
    if problems:
        problem_list = "\n".join(f"  - {p}" for p in problems)
        raise ValueError(
            "Prep guide citation check failed - refusing to produce a "
            f"guide with unverified claims:\n{problem_list}"
        )

    html_doc = build_prep_guide_html(profile, result, company_name)
    html_path = os.path.join(output_dir, "prep_guide.html")
    pdf_path = os.path.join(output_dir, "prep_guide.pdf")
    with open(html_path, "w") as f:
        f.write(html_doc)

    _render_pdf(html_path, pdf_path)


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


def _company_folder(job_url):
    """
    Builds a per-company output folder path from a job URL's domain,
    so every document generated for one application (resume, cover
    letter, form Q&A, prep guide) lands in the same place, and
    different companies never overwrite each other.

    Parameters:
        job_url: the web address of the job posting.

    Example: _company_folder("https://www.google.com/about/careers/...")
    returns "output/google".

    Note: this is a simple heuristic based on the domain name, so it
    works well for a company's own site (google.com -> "google") but
    less well for a shared job board (e.g. job-boards.greenhouse.io),
    where the company name is in the URL path, not the domain.
    """
    domain = urlparse(job_url).netloc
    if domain.startswith("www."):
        domain = domain[len("www.") :]
    name = domain.split(".")[0] or "company"
    return f"output/{name}"


def _display_name(output_dir):
    """
    Turns a folder name like "google" or "job-boards" into a
    presentable name like "Google" or "Job Boards", for use in the
    cover letter's greeting line.
    """
    folder_name = os.path.basename(output_dir.rstrip("/"))
    return folder_name.replace("-", " ").replace("_", " ").title()


if __name__ == "__main__":
    # Usage: python3 src/generate.py <job posting URL> [output_dir]
    if len(sys.argv) < 2:
        print("Usage: python3 src/generate.py <job posting URL> [output_dir]")
        sys.exit(1)

    job_url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        final_dir = generate_application(job_url, output_dir)
        print(f"Application documents written to {final_dir}/")
    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}")
        sys.exit(1)
