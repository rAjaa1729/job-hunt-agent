"""
The "brain" of job-hunt-agent - the one place in this whole project that
knows how to talk to an AI model.

Every other part of the project asks this file to talk to the AI,
rather than talking to a provider directly.

Which AI actually answers is controlled by one setting, LLM_PROVIDER,
in .env - set it to "cloudflare" (a cloud service, needs an API token,
has a daily free limit) or "ollama" (runs locally on this laptop, no
token needed, no daily limit, but slower). To add a new provider
later, add one more small function below and one more branch inside
call_llm() - nothing outside this file needs to change either way.
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "cloudflare")

CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_MODEL = "@cf/qwen/qwen3.8-27b"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:9b")


def call_llm(messages, max_tokens=500):
    """
    Asks the AI a question or gives it a task, and returns its answer
    as plain text. This is the one function every other part of this
    project uses whenever it needs the AI to think or write something.

    Parameters:
        messages: the conversation so far, oldest turn first, e.g.
            [{"role": "user", "content": "Say hello"}]
        max_tokens: roughly how long the reply is allowed to be -
            a bigger number allows a longer answer but can cost more
            and take longer to arrive.

    Example: call_llm([{"role": "user", "content": "Say hello"}])
    returns something like "Hello! How can I help?"

    Which AI actually answers depends on the LLM_PROVIDER setting in
    .env - this function just routes the request to the matching
    provider and raises a clear error if that call fails, instead of
    returning something broken silently.
    """
    if LLM_PROVIDER == "cloudflare":
        return _call_cloudflare(messages, max_tokens)
    if LLM_PROVIDER == "ollama":
        return _call_ollama(messages, max_tokens)
    raise ValueError(
        f"Unknown LLM_PROVIDER: '{LLM_PROVIDER}' - expected 'cloudflare' or 'ollama'"
    )


def _call_cloudflare(messages, max_tokens):
    """
    Sends a conversation to Cloudflare's hosted AI service over the
    internet and returns its reply as plain text.

    Parameters:
        messages: the conversation so far, same shape as call_llm().
        max_tokens: the reply length limit, same meaning as call_llm().

    Needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN set in .env.
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_MODEL}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"messages": messages, "max_tokens": max_tokens}

    response = requests.post(url, headers=headers, json=payload, timeout=300)
    data = response.json()

    if not data.get("success"):
        error_message = data.get("errors", [{}])[0].get("message", "Unknown error")
        raise RuntimeError(f"Cloudflare LLM call failed: {error_message}")

    result = data["result"]
    # Different AI models on this platform shape their reply
    # differently: some return {"response": "..."}, others return the
    # more common {"choices": [{"message": {"content": "..."}}]} format.
    # Checking for both means this function keeps working even if the
    # model gets swapped for a different one later.
    if "response" in result:
        return result["response"]
    return result["choices"][0]["message"]["content"]


def _call_ollama(messages, max_tokens):
    """
    Sends a conversation to an AI model running locally on this
    laptop (via Ollama) and returns its reply as plain text.

    Parameters:
        messages: the conversation so far, same shape as call_llm().
        max_tokens: the reply length limit, same meaning as call_llm().

    Needs Ollama installed and running, with the model already
    downloaded ahead of time (e.g. `ollama pull qwen3.5:9b`).
    """
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"num_predict": max_tokens, "num_ctx": 16384},
    }

    try:
        response = requests.post(url, json=payload, timeout=300)
    except requests.exceptions.ConnectionError:
        # "from None" hides the low-level connection error underneath -
        # it's just internal plumbing detail, not something a reader
        # needs to see to fix the actual problem.
        raise RuntimeError(
            "Could not reach the local AI (Ollama). To fix this:\n"
            "  1. Open the Ollama app, or run `ollama serve` in a terminal\n"
            "  2. Wait a few seconds for it to fully start\n"
            "  3. Run this again\n"
            "Still not working? Check the model is downloaded with: ollama list"
        ) from None

    data = response.json()

    if "error" in data:
        raise RuntimeError(f"Ollama LLM call failed: {data['error']}")

    # Some local models (reasoning models especially) include their
    # internal "thinking" text alongside the real answer - we only
    # want the final answer, which Ollama always puts in "content".
    return data["message"]["content"]


if __name__ == "__main__":
    # Manual sanity check: `python3 src/llm.py` - confirms the
    # connection works without needing the full resume tool built yet.
    #
    # Known, expected problems (like Ollama not running) print just
    # their clear guidance message here - not a wall of Python
    # internals, which would bury the actual instructions.
    try:
        reply = call_llm([{"role": "user", "content": "Reply with exactly the word: works"}])
        print(f"LLM ({LLM_PROVIDER}) replied:", reply)
    except RuntimeError as error:
        print(f"Error: {error}")
        sys.exit(1)
