"""
The "brain" of job-hunt-agent - the one place in this whole project that
knows how to talk to an AI model.

Every other part of the project asks this file to talk to the AI,
rather than talking to a provider directly.

To switch to a different AI provider later (e.g. Anthropic's Claude),
edit only this file: replace the request-building code inside
call_llm() with a call to the new provider's API, while keeping the
same function signature (takes messages in, returns plain text out).
Nothing else in the project needs to change.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
CLOUDFLARE_API_TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
MODEL = "@cf/qwen/qwen3.8-27b"


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

    Raises a clear error if the call fails, instead of returning
    something broken silently.
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"messages": messages, "max_tokens": max_tokens}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    data = response.json()

    if not data.get("success"):
        error_message = data.get("errors", [{}])[0].get("message", "Unknown error")
        raise RuntimeError(f"LLM call failed: {error_message}")

    result = data["result"]
    # Different AI models on this platform shape their reply
    # differently: some return {"response": "..."}, others return the
    # more common {"choices": [{"message": {"content": "..."}}]} format.
    # Checking for both means this function keeps working even if the
    # model gets swapped for a different one later.
    if "response" in result:
        return result["response"]
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # Manual sanity check: `python3 src/llm.py` - confirms the
    # connection works without needing the full resume tool built yet.
    reply = call_llm([{"role": "user", "content": "Reply with exactly the word: works"}])
    print("LLM replied:", reply)
