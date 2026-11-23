"""
Standalone HTTP Server & REST API for Polite Web Scraper.
Provides a local web server hosting the interactive dashboard
and exposing RESTful endpoints for books querying, metrics, and downloads.
Requires zero external web framework dependencies (built on Python stdlib http.server).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from src.analytics import generate_full_analytics_summary


def load_books_from_dir(output_dir: str) -> list[dict[str, Any]]:
    """Load books.json from output directory."""
    books_file = os.path.join(output_dir, "books.json")
    if os.path.exists(books_file):
        with open(books_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_report_from_dir(output_dir: str) -> dict[str, Any]:
    """Load run-report.json from output directory."""
    report_file = os.path.join(output_dir, "run-report.json")
    if os.path.exists(report_file):
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def handle_api_route(
    path: str,
    query_params: dict[str, list[str]],
    output_dir: str = "output",
) -> tuple[int, dict[str, str], bytes]:
    """
    Core route handler separating business logic from socket I/O.
    Returns: (status_code, headers_dict, body_bytes)
    """
    # 1. Health check
    if path == "/api/health":
        books = load_books_from_dir(output_dir)
        payload = {
            "status": "healthy",
            "service": "Polite Web Scraper Dashboard API",
            "version": "2.0.0",
            "books_count": len(books),
        }
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        return 200, {"Content-Type": "application/json; charset=utf-8"}, body

    # 2. Stats endpoint
    if path == "/api/stats":
        books = load_books_from_dir(output_dir)
        report = load_report_from_dir(output_dir)
        analytics = generate_full_analytics_summary(books)
        payload = {
            "report": report,
            "analytics": analytics,
        }
        body = json.dumps(payload, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        return 200, {"Content-Type": "application/json; charset=utf-8"}, body

    # 3. Books query and filtering
    if path == "/api/books":
        books = load_books_from_dir(output_dir)

        search_query = query_params.get("q", [None])[0] or query_params.get("search", [None])[0]
        rating_filter = query_params.get("rating", [None])[0]
        in_stock_filter = query_params.get("in_stock", [None])[0]
        min_price = query_params.get("min_price", [None])[0]
        max_price = query_params.get("max_price", [None])[0]

        filtered = books
        if search_query:
            sq = search_query.lower()
            filtered = [
                b for b in filtered
                if sq in b.get("title", "").lower() or sq in (b.get("description") or "").lower()
            ]

        if rating_filter is not None:
            try:
                r_val = int(rating_filter)
                filtered = [b for b in filtered if int(b.get("rating", 0)) == r_val]
            except ValueError:
                pass

        if in_stock_filter is not None:
            want_in_stock = in_stock_filter.lower() in ("true", "1", "yes")
            filtered = [b for b in filtered if (int(b.get("stock_count", 0)) > 0) == want_in_stock]

        if min_price is not None:
            try:
                p_min = float(min_price)
                filtered = [b for b in filtered if float(b.get("price_gbp", 0.0)) >= p_min]
            except ValueError:
                pass

        if max_price is not None:
            try:
                p_max = float(max_price)
                filtered = [b for b in filtered if float(b.get("price_gbp", 0.0)) <= p_max]
            except ValueError:
                pass

        # Sorting
        sort_param = query_params.get("sort", [None])[0]
        if sort_param == "price_asc":
            filtered.sort(key=lambda b: float(b.get("price_gbp", 0.0)))
        elif sort_param == "price_desc":
            filtered.sort(key=lambda b: float(b.get("price_gbp", 0.0)), reverse=True)
        elif sort_param == "rating_desc":
            filtered.sort(key=lambda b: int(b.get("rating", 0)), reverse=True)
        elif sort_param == "title_asc":
            filtered.sort(key=lambda b: b.get("title", "").lower())

        # Pagination
        try:
            page = max(1, int(query_params.get("page", [1])[0]))
        except ValueError:
            page = 1

        try:
            limit = max(1, min(100, int(query_params.get("limit", [50])[0])))
        except ValueError:
            limit = 50

        total_items = len(filtered)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_items = filtered[start_idx:end_idx]

        payload = {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": (total_items + limit - 1) // limit if total_items > 0 else 0,
            "books": page_items,
        }
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        return 200, {"Content-Type": "application/json; charset=utf-8"}, body

    # 4. Exports
    if path == "/api/export":
        fmt = query_params.get("format", ["csv"])[0].lower()
        allowed = {
            "csv": ("books.csv", "text/csv"),
            "json": ("books.json", "application/json"),
            "markdown": ("books.md", "text/markdown"),
            "md": ("books.md", "text/markdown"),
            "ndjson": ("books.ndjson", "application/x-ndjson"),
            "xml": ("books.xml", "application/xml"),
        }
        if fmt in allowed:
            fname, ctype = allowed[fmt]
            target_path = os.path.join(output_dir, fname)
            if not os.path.exists(target_path):
                return 404, {"Content-Type": "text/plain"}, b"Export file not found."
            with open(target_path, "rb") as f:
                content = f.read()
            headers = {
                "Content-Type": ctype,
                "Content-Disposition": f'attachment; filename="{fname}"',
            }
            return 200, headers, content
        return 400, {"Content-Type": "text/plain"}, f"Unsupported export format: {fmt}".encode()

    # 5. Dashboard HTML
    if path in ("/", "/dashboard", "/index.html"):
        dashboard_file = os.path.join(output_dir, "dashboard.html")
        if not os.path.exists(dashboard_file):
            return 404, {"Content-Type": "text/plain"}, b"Dashboard HTML file not found."
        with open(dashboard_file, "rb") as f:
            content = f.read()
        return 200, {"Content-Type": "text/html; charset=utf-8"}, content

    return 404, {"Content-Type": "text/plain"}, f"Endpoint not found: {path}".encode()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler routing requests through handle_api_route."""
    server_version = "PoliteScraperServer/2.0"

    def __init__(self, *args, output_dir: str = "output", **kwargs):
        self.output_dir = output_dir
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            sys.stderr.write(f"[HTTP] {self.address_string()} - {format % args}\n")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        status, headers, body = handle_api_route(path, query_params, output_dir=self.output_dir)

        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = "127.0.0.1", port: int = 8080, output_dir: str = "output") -> HTTPServer:
    """Instantiate and configure the HTTP server."""
    def handler(*args: Any, **kwargs: Any) -> DashboardRequestHandler:
        return DashboardRequestHandler(*args, output_dir=output_dir, **kwargs)

    return HTTPServer((host, port), handler)


def run_server(host: str = "127.0.0.1", port: int = 8080, output_dir: str = "output") -> None:
    """Run the server until interrupted."""
    server = create_server(host, port, output_dir)
    print(f"\n[SERVER] Polite Web Scraper Dashboard running at: http://{host}:{port}/")
    print(f"[SERVER] REST API Books endpoint: http://{host}:{port}/api/books")
    print(f"[SERVER] REST API Stats endpoint: http://{host}:{port}/api/stats")
    print("[SERVER] Press Ctrl+C to terminate.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down gracefully...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
