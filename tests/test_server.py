"""
Unit tests for the Standalone HTTP Server and REST API (src/server.py).
"""

import json

from src.server import handle_api_route


def _setup_mock_dir(tmp_path):
    books_file = tmp_path / "books.json"
    report_file = tmp_path / "run-report.json"
    dash_file = tmp_path / "dashboard.html"
    csv_file = tmp_path / "books.csv"

    sample_books = [
        {
            "title": "Alpha Book",
            "price_gbp": 15.0,
            "rating": 5,
            "stock_count": 10,
            "availability_text": "In stock",
            "product_url": "https://books.toscrape.com/1",
            "description": "An alpha adventure.",
        },
        {
            "title": "Beta Book",
            "price_gbp": 45.0,
            "rating": 2,
            "stock_count": 0,
            "availability_text": "Out of stock",
            "product_url": "https://books.toscrape.com/2",
            "description": "A beta story.",
        },
    ]
    books_file.write_text(json.dumps(sample_books), encoding="utf-8")
    report_file.write_text(json.dumps({"duration_seconds": 2.5}), encoding="utf-8")
    dash_file.write_text("<!DOCTYPE html><html>Dashboard</html>", encoding="utf-8")
    csv_file.write_text("title,price_gbp\nAlpha Book,15.0", encoding="utf-8")
    return str(tmp_path)


def test_server_health_route(tmp_path):
    out_dir = _setup_mock_dir(tmp_path)
    status, headers, body = handle_api_route("/api/health", {}, output_dir=out_dir)

    assert status == 200
    assert "application/json" in headers["Content-Type"]
    data = json.loads(body.decode("utf-8"))
    assert data["status"] == "healthy"
    assert data["books_count"] == 2


def test_server_stats_route(tmp_path):
    out_dir = _setup_mock_dir(tmp_path)
    status, headers, body = handle_api_route("/api/stats", {}, output_dir=out_dir)

    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert "analytics" in data
    assert data["analytics"]["pricing"]["count"] == 2


def test_server_books_filtering_and_sorting(tmp_path):
    out_dir = _setup_mock_dir(tmp_path)

    # Search filter
    status, _, body = handle_api_route("/api/books", {"q": ["Alpha"]}, output_dir=out_dir)
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["total_items"] == 1
    assert data["books"][0]["title"] == "Alpha Book"

    # Rating filter
    status, _, body = handle_api_route("/api/books", {"rating": ["5"]}, output_dir=out_dir)
    data = json.loads(body.decode("utf-8"))
    assert data["total_items"] == 1
    assert data["books"][0]["rating"] == 5

    # Stock filter
    status, _, body = handle_api_route("/api/books", {"in_stock": ["true"]}, output_dir=out_dir)
    data = json.loads(body.decode("utf-8"))
    assert data["total_items"] == 1
    assert data["books"][0]["stock_count"] == 10

    # Sort descending by price
    status, _, body = handle_api_route("/api/books", {"sort": ["price_desc"]}, output_dir=out_dir)
    data = json.loads(body.decode("utf-8"))
    assert data["books"][0]["title"] == "Beta Book"


def test_server_export_and_dashboard_routes(tmp_path):
    out_dir = _setup_mock_dir(tmp_path)

    # CSV Export
    status, headers, body = handle_api_route("/api/export", {"format": ["csv"]}, output_dir=out_dir)
    assert status == 200
    assert "text/csv" in headers["Content-Type"]
    assert "Alpha Book" in body.decode("utf-8")

    # Dashboard HTML
    status, headers, body = handle_api_route("/dashboard", {}, output_dir=out_dir)
    assert status == 200
    assert "text/html" in headers["Content-Type"]
    assert "Dashboard" in body.decode("utf-8")

    # 404 Route
    status, _, _ = handle_api_route("/nonexistent", {}, output_dir=out_dir)
    assert status == 404
