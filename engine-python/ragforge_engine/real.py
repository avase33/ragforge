"""Optional real LLM synthesizer (used only when RAGFORGE_LLM=openai)."""

from __future__ import annotations

import os
from typing import List


def synthesize_openai(question: str, contexts: List) -> str:
    from openai import OpenAI  # lazy import

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    joined = "\n\n".join(c.text for c in contexts)
    prompt = (
        "Answer the question using only the context. If the answer is not in the "
        f"context, say so.\n\nContext:\n{joined}\n\nQuestion: {question}\nAnswer:"
    )
    resp = client.chat.completions.create(
        model=os.getenv("RAGFORGE_LLM_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()
