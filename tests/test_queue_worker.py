"""
Unit tests for PoliteWorkerPool concurrency and queue execution.
"""

from src.queue_worker import PoliteWorkerPool


def test_worker_pool_execution():
    """Test concurrent job processing with mock fetcher."""
    pool = PoliteWorkerPool(max_concurrency=2)

    dummy_html = """
    <div class="product_main">
      <h1>Concurrent Book</h1>
      <p class="price_color">£19.99</p>
      <p class="instock availability">In stock (5 available)</p>
    </div>
    <p class="star-rating Three"></p>
    """

    entries = [
        {"url": f"https://books.toscrape.com/catalogue/book-{i}/index.html", "source_page": "https://books.toscrape.com/page-1.html"}
        for i in range(1, 6)
    ]

    def mock_fetch(url: str) -> str:
        return dummy_html

    results = pool.process_jobs(entries, mock_fetch)
    assert len(results) == 5
    for r in results:
        assert r["title"] == "Concurrent Book"
        assert r["price_text"] == "£19.99"
