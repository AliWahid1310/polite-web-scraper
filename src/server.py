"""
Standalone HTTP Server & REST API for Polite Web Scraper.
Provides a local web server hosting the interactive dashboard
and exposing RESTful endpoints for books querying, metrics, and downloads.
Requires zero external web framework dependencies (built on Python stdlib http.server).
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from src.analytics import generate_full_analytics_summary
from src.exporters import export_to_csv, export_to_markdown_table


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler routing dashboard pages, REST endpoints, and export downloads.
    """
    server_version = "PoliteScraperServer/2.0"

    def __init__(self, *args, output_dir: str = "output", **kwargs):
        self.output_dir = output_dir
        super().__init__(*args, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Custom clean logging format for server requests."""
        # Suppress spammy log outputs during automated testing
        if not os.environ.get("PYTEST_CURRENT_TEST"):
            sys.stderr.write(f"[HTTP] {self.address_string()} - {format % args}\n")

    def _send_json_response(self, data: Any, status: int = 200) -> None:
        """Send formatted JSON response."""
        payload = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _send_file_response(self, file_path: str, content_type: str | None = None, as_attachment: bool = False) -> None:
        """Send static file or attachment."""
        if not os.path.exists(file_path):
            self.send_error(HTTPStatus.NOT_FOUND, f"File not found: {os.path.basename(file_path)}")
            return

        with open(file_path, "rb") as f:
            content = f.read()

        ct = content_type or mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(content)))
        if as_attachment:
            filename = os.path.basename(file_path)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(content)

    def _load_books(self) -> list[dict[str, Any]]:
        """Load books.json from output directory."""
        books_file = os.path.join(self.output_dir, "books.json")
        if os.path.exists(books_file):
            with open(books_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _load_report(self) -> dict[str, Any]:
        """Load run-report.json from output directory."""
        report_file = os.path.join(self.output_dir, "run-report.json")
        if os.path.exists(report_file):
            with open(report_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def do_GET(self) -> None:
        """Route GET requests to HTML dashboard or REST API endpoints."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # 1. Dashboard UI
        if path in ("/", "/dashboard", "/index.html"):
            dashboard_file = os.path.join(self.output_dir, "dashboard.html")
            self._send_file_response(dashboard_file, content_type="text/html; charset=utf-8")
            return

        # 2. REST API: Health Check
        if path == "/api/health":
            self._send_json_response({
                "status": "healthy",
                "service": "Polite Web Scraper Dashboard API",
                "version": "2.0.0",
                "books_count": len(self._load_books()),
            })
            return

        # 3. REST API: Statistics
        if path == "/api/stats":
            books = self._load_books()
            report = self._load_report()
            analytics = generate_full_analytics_summary(books)
            self._send_json_response({
                "report": report,
                "analytics": analytics,
            })
            return

        # 4. REST API: Books Query & Filtering
        if path == "/api/books":
            books = self._load_books()

            # Filters
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

            self._send_json_response({
                "page": page,
                "limit": limit,
                "total_items": total_items,
                "total_pages": (total_items + limit - 1) // limit if total_items > 0 else 0,
                "books": page_items,
            })
            return

        # 5. REST API: Export Downloads
        if path == "/api/export":
            fmt = query_params.get("format", ["csv"])[0].lower()
            if fmt == "csv":
                p = os.path.join(self.output_dir, "books.csv")
                self._send_file_response(p, content_type="text/csv", as_attachment=True)
                return
            elif fmt == "json":
                p = os.path.join(self.output_dir, "books.json")
                self._send_file_response(p, content_type="application/json", as_attachment=True)
                return
            elif fmt == "markdown" or fmt == "md":
                p = os.path.join(self.output_dir, "books.md")
                self._send_file_response(p, content_type="text/markdown", as_attachment=True)
                return
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, f"Unsupported export format: {fmt}")
                return

        # Not found fallback
        self.send_error(HTTPStatus.NOT_FOUND, f"Endpoint not found: {path}")


def create_server(host: str = "127.0.0.1", port: int = 8080, output_dir: str = "output") -> HTTPServer:
    """Instantiate and configure the HTTP server."""
    handler = lambda *args, **kwargs: DashboardRequestHandler(*args, output_dir=output_dir, **kwargs)
    return HTTPServer((host, port), handler)


def run_server(host: str = "127.0.0.1", port: int = 8080, output_dir: str = "output") -> None:
    """Run the server until interrupted."""
    server = create_server(host, port, output_dir)
    print(f"\n[SERVER] Polite Web Scraper Dashboard running at: http://{host}:{port}/")
    print(f"[SERVER] REST API Books endpoint: http://{host}:{port}/api/books")
    print(f"[SERVER] REST API Stats endpoint: http://{host}:{port}/api/stats")
    print(f"[SERVER] Press Ctrl+C to terminate.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down gracefully...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
