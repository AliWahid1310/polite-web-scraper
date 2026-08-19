"""
Unit tests for AI enrichment module (Stretch Goal).
Tests schema isolation, fallback classifier, and mock network response handling.
"""

from unittest.mock import MagicMock, patch
from pydantic import HttpUrl
from datetime import datetime, timezone
from src.enrichment import enrich_book_record, EnrichedBookRecord, _heuristic_semantic_classifier
from src.schemas import BookRecord


def _create_sample_book(title: str = "A Light in the Attic", description: str = "A poetry book.") -> BookRecord:
    return BookRecord(
        title=title,
        product_url=HttpUrl("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"),
        price_text="£51.77",
        price_gbp=51.77,
        availability_text="In stock (22 available)",
        stock_count=22,
        rating_text="Three",
        rating=3,
        description=description,
        source_page=HttpUrl("https://books.toscrape.com/catalogue/page-1.html"),
        fetched_at=datetime.now(timezone.utc),
    )


def test_ai_enrichment_schema_isolation():
    """Test that factual data and AI opinion remain strictly separated in the schema."""
    book = _create_sample_book(title="A Light in the Attic", description="A celebrated poetry collection from Shel Silverstein.")
    enriched = enrich_book_record(book)

    assert isinstance(enriched, EnrichedBookRecord)
    assert enriched.scraped_facts.title == "A Light in the Attic"
    assert enriched.scraped_facts.price_gbp == 51.77
    assert enriched.ai_enrichment.ai_category == "Poetry"
    assert "celebrated poetry" in enriched.ai_enrichment.ai_one_sentence_summary.lower()
    assert enriched.ai_enrichment.model_name == "local-heuristic-classifier-v1"


def test_heuristic_categories():
    """Test heuristic categorization across diverse topics."""
    c1 = _heuristic_semantic_classifier("World War II in Europe", "A detailed history of the 20th century conflict.")
    assert c1.ai_category == "History / Non-Fiction"

    c2 = _heuristic_semantic_classifier("The Gourmet Cook", "A complete guide to food and preserving.")
    assert c2.ai_category == "Lifestyle & Cooking"

    c3 = _heuristic_semantic_classifier("Love and Mystery", "A gripping romance thriller novel.")
    assert c3.ai_category == "Fiction / Literature"


@patch("src.enrichment.requests.post")
def test_enrich_with_mocked_ollama_success(mock_post):
    """Test successful Ollama API response parsing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": "CATEGORY: Science Fiction\nSUMMARY: An adventurous sci-fi novel exploring distant galaxies."
    }
    mock_post.return_value = mock_resp

    book = _create_sample_book(title="Dune", description="A desert planet epic.")
    enriched = enrich_book_record(book)

    assert enriched.ai_enrichment.ai_category == "Science Fiction"
    assert "adventurous sci-fi" in enriched.ai_enrichment.ai_one_sentence_summary
    assert enriched.ai_enrichment.model_name == "llama3:latest"


@patch("src.enrichment.requests.post")
def test_enrich_with_mocked_ollama_failure_fallback(mock_post):
    """Test fallback when Ollama raises connection error or returns 500."""
    mock_post.side_effect = Exception("Connection refused")

    book = _create_sample_book(title="History of Rome", description="The rise and fall of the empire.")
    enriched = enrich_book_record(book)

    assert enriched.ai_enrichment.ai_category == "History / Non-Fiction"
    assert enriched.ai_enrichment.model_name == "local-heuristic-classifier-v1"
