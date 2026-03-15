import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qcwind/qwen3-8b-instruct-Q4-K-M"


def _clean(text: str) -> str:
    """
    Strip all markdown formatting from LLM output so the UI receives clean prose.
    Removes: bold (**text**), italic (*text*), headers (#), bullets (- / * / 1.),
    inline code (`text`), horizontal rules, and excess blank lines.
    """
    # Remove bold / italic markers
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    # Remove inline code
    text = re.sub(r"`+([^`]*)`+", r"\1", text)
    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r"^[-_*]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Convert bullet / numbered list lines into plain sentences
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_ai_recommendation(context: str) -> str:
    """
    Accepts a plain-text competitive context string and returns a clean,
    professional advisory paragraph — no markdown, no bullet points.
    Used by the alerts AI-strategy endpoint.
    """

    prompt = (
        "You are a senior e-commerce business consultant advising a seller on an Indian marketplace.\n\n"
        "Based on the competitive data below, write a focused advisory of exactly 4 to 5 sentences.\n\n"
        "Strict output rules — any violation makes the response unusable:\n"
        "  - Plain sentences only. Zero bullet points. Zero numbered lists. Zero asterisks.\n"
        "  - Every sentence must name a specific number from the data (price, discount %, delivery days, rating).\n"
        "  - Open with the single most urgent action the seller must take right now.\n"
        "  - End with one sentence on how to turn any existing advantage into visible marketing.\n"
        "  - Do not introduce yourself, do not add a heading, do not summarise at the end.\n\n"
        f"Competitive data:\n{context}\n\n"
        "Advisory (plain sentences, no formatting):"
    )

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=120,
        )
        if resp.status_code != 200:
            return "LLM service is unavailable. Please ensure Ollama is running and the model is loaded."
        raw = resp.json().get("response", "")
        return _clean(raw) or "No recommendation could be generated for this product."
    except requests.exceptions.ConnectionError:
        return "Unable to reach Ollama. Run 'ollama serve' and ensure the model is loaded."
    except requests.exceptions.Timeout:
        return "The model took too long to respond. Try a lighter model or increase the timeout."
    except Exception as exc:
        return f"Unexpected error while calling LLM: {exc}"