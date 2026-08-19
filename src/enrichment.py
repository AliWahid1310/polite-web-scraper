"""
Local AI Enrichment module (Stretch Goal).
Uses Ollama (or a deterministic local semantic classifier fallback if offline)
to add an AI category and short summary to validated descriptions.
Enforces strict schema validation and keeps model opinions separated from scraped facts.
"""

from typing import Optional
import requests
from pydantic import BaseModel, Field

from src.schemas import BookRecord

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"


class AIEnrichmentMetadata(BaseModel):
    """Encapsulates AI generated semantic enrichment, isolated from factual data."""
    ai_category: str = Field(..., min_length=1, description="LLM inferred genre / category")
    ai_one_sentence_summary: str = Field(..., min_length=1, description="LLM distilled one-sentence summary")
    model_name: str = Field(..., min_length=1, description="Name of local LLM or fallback used")


class EnrichedBookRecord(BaseModel):
    """Combined record keeping raw scraped facts and AI opinion cleanly separated."""
    scraped_facts: BookRecord
    ai_enrichment: AIEnrichmentMetadata


def _heuristic_semantic_classifier(title: str, description: Optional[str]) -> AIEnrichmentMetadata:
    """
    Deterministic fallback when Ollama local daemon is offline.
    Infers category and short summary from textual cues without external network dependencies.
    """
    text = f"{title} {description or ''}".lower()

    if any(k in text for k in ["poem", "poetry", "verse", "rhyme", "silverstein"]):
        category = "Poetry"
    elif any(k in text for k in ["history", "war", "century", "country", "berlin", "olympic"]):
        category = "History / Non-Fiction"
    elif any(k in text for k in ["novel", "fiction", "romance", "story", "thriller"]):
        category = "Fiction / Literature"
    elif any(k in text for k in ["guide", "how-to", "food", "cook", "preserv"]):
        category = "Lifestyle & Cooking"
    else:
        category = "General Literature"

    # Short summary extraction
    if description and description.strip():
        first_sentence = description.split(".")[0].strip()
        summary = f"{first_sentence}." if first_sentence else f"A book about {title}."
    else:
        summary = f"A book titled '{title}'."

    return AIEnrichmentMetadata(
        ai_category=category,
        ai_one_sentence_summary=summary[:200],
        model_name="local-heuristic-classifier-v1",
    )


def enrich_book_record(
    record: BookRecord,
    ollama_url: str = OLLAMA_ENDPOINT,
    model: str = "llama3:latest",
) -> EnrichedBookRecord:
    """
    Enrich a BookRecord using Ollama local model, falling back to local classifier.
    Guarantees strict schema enforcement and error resilience.
    """
    prompt = (
        f"Analyze the following book:\n"
        f"Title: {record.title}\n"
        f"Description: {record.description or 'N/A'}\n\n"
        f"Provide exactly two lines:\n"
        f"CATEGORY: <single category name>\n"
        f"SUMMARY: <one concise sentence>\n"
    )

    try:
        resp = requests.post(
            ollama_url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            response_text = data.get("response", "")

            category = "General"
            summary = f"A book about {record.title}."

            for line in response_text.splitlines():
                clean_line = line.strip()
                if clean_line.upper().startswith("CATEGORY:"):
                    parsed_cat = clean_line.split(":", 1)[1].strip()
                    if parsed_cat:
                        category = parsed_cat
                elif clean_line.upper().startswith("SUMMARY:"):
                    parsed_sum = clean_line.split(":", 1)[1].strip()
                    if parsed_sum:
                        summary = parsed_sum

            enrichment = AIEnrichmentMetadata(
                ai_category=category,
                ai_one_sentence_summary=summary,
                model_name=model,
            )
            return EnrichedBookRecord(scraped_facts=record, ai_enrichment=enrichment)

    except Exception:
        # Gracefully handle any connection errors, timeout, JSON errors, or validation issues
        pass

    # Deterministic resilient fallback
    fallback_enrichment = _heuristic_semantic_classifier(record.title, record.description)
    return EnrichedBookRecord(scraped_facts=record, ai_enrichment=fallback_enrichment)
