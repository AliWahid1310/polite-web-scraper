"""
Unit tests for AI enrichment module (Stretch Goal).
"""

from src.enrichment import enrich_book_record, EnrichedBookRecord
from src.schemas import BookRecord


def test_ai_enrichment_schema_isolation():
    """Test that factual data and AI opinion remain strictly separated in the schema."""
    book = BookRecord(
        title="A Light in the Attic",
        product_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        price_text="£51.77",
        price_gbp=51.77,
        availability_text="In stock (22 available)",
        stock_count=22,
        rating_text="Three",
        rating=3,
        description="A celebrated poetry collection from Shel Silverstein.",
        source_page="https://books.toscrape.com/catalogue/page-1.html",
        fetched_at="2026-08-18T12:00:00Z",
    )

    enriched = enrich_book_record(book)
    assert isinstance(enriched, EnrichedBookRecord)
    
    # Verify scraped facts are unaltered
    assert enriched.scraped_facts.title == "A Light in the Attic"
    assert enriched.scraped_facts.price_gbp == 51.77
    
    # Verify AI opinion is isolated
    assert enriched.ai_enrichment.ai_category == "Poetry"
    assert "celebrated poetry" in enriched.ai_enrichment.ai_one_sentence_summary.lower()
    assert enriched.ai_enrichment.model_name is not None
