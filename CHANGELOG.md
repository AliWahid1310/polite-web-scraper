# Changelog

All notable changes to The Polite Web Scraper are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-11-23

### Added
- **Centralized Configuration Manager** (`src/config.py`): Dataclass-based config with environment variable overrides (`PSC_*` prefix), runtime validation, and global singleton access pattern.
- **Advanced Cache Manager** (`src/cache_manager.py`): TTL-based expiration, LRU eviction on max entry limits, cache performance statistics (hit rate, bytes read/written), and comprehensive cache summary reports.
- **Custom Validators & Sanitizers** (`src/validators.py`): `URLValidator` for URL scheme/domain validation, `TextSanitizer` for HTML tag removal and whitespace normalization, `RecordValidator` for field-level data quality checks with dataset-wide quality scoring.
- **Pipeline Notification System** (`src/notifications.py`): Publisher-subscriber event bus with typed pipeline events (`EventType`, `EventLevel`), global and per-type handlers, event logging with configurable max size, and built-in console/file/counter handler factories.
- **Multi-Run Dataset Comparator** (`src/comparator.py`): Diff engine comparing two scrape runs by `product_url` key, detecting additions, removals, and field-level changes with numeric deltas and percentage calculations. Includes `get_price_changes()`, `get_stock_changes()`, and `summarize()` for human-readable reports.
- **CONTRIBUTING.md**: Comprehensive contributor guide with setup instructions, project structure, testing guidelines, code style rules, and PR process.
- **CHANGELOG.md**: This file — structured changelog following Keep a Changelog format.
- 30+ new unit tests across `test_config.py`, `test_cache_manager.py`, `test_validators.py`, `test_notifications.py`, and `test_comparator.py`.

### Changed
- **Version bumped to 2.1.0** in `pyproject.toml` and `src/__init__.py`.
- **`src/__init__.py`**: Added exports for `ScraperConfig`, `CacheManager`, `URLValidator`, `TextSanitizer`, `RecordValidator`, `NotificationManager`, `DatasetComparator`.
- **`README.md`**: Updated test badge to 100+ tests, added sections for configuration system, notifications, dataset comparison, and contributing guide reference.
- **CI pipeline** (`.github/workflows/ci.yml`): Added Python 3.14 to test matrix, added `--tb=short` flag for cleaner CI output.

---

## [2.0.0] - 2026-11-21

### Added
- **Interactive Glassmorphic Dashboard** (`src/dashboard.py`): Complete rewrite with Chart.js visualizations, faceted filtering, search, sorting, book detail modal, and client-side CSV/JSON export.
- **REST API Server** (`src/server.py`): Zero-dependency HTTP server with `/api/health`, `/api/stats`, `/api/books` (paginated, filtered), and `/api/export` endpoints.
- **SQLite Relational Storage** (`src/sqlite_storage.py`): Indexed database with upsert, full-text search, and query helpers.
- **Statistical Analytics Engine** (`src/analytics.py`): Mean, median, standard deviation, IQR outlier detection, rating distributions, and inventory valuations.
- **Cryptographic Audit Module** (`src/audit.py`): SHA-256 dataset integrity manifests and anomaly detection.
- **Token-Bucket Rate Limiter** (`src/rate_limiter.py`): Thread-safe rate limiting with configurable RPS and burst.
- **Circuit Breaker** (`src/circuit_breaker.py`): State-machine pattern (CLOSED → OPEN → HALF_OPEN) for cascading failure protection.
- **Respectful Header Manager** (`src/headers.py`): User-Agent rotation with honest identification.
- **Multi-Format Exporters** (`src/exporters.py`): CSV, Markdown, NDJSON, and XML export from validated records.
- **Terminal UI** (`src/terminal_ui.py`): Colorized banners, stage headers, and ASCII summary tables.
- **Batch Manager** (`src/batch.py`): Keyword filtering and custom target list loading.
- **Pipeline Benchmark** (`src/benchmark.py`): Parser throughput and function execution measurement.
- 69 unit tests covering all modules.

### Changed
- **`src/schemas.py`**: Added `currency`, `is_in_stock`, `total_inventory_value_gbp`, `category` fields.
- **`src/normalizer.py`**: Updated to compute new derived fields.
- **`src/main.py`**: Full pipeline overhaul with multi-stage orchestration, audit manifest, and multi-format exports.
- **`src/cli.py`**: Added `--serve`, `--port`, `--export-format`, `--query` flags.
- **CI pipeline**: Expanded with lint check and artifact verification.
- **`README.md`**: Complete rewrite with v2.0 architecture documentation.

---

## [1.0.0] - 2026-08-16

### Added
- Initial release with basic scraping pipeline.
- HTML extraction with BeautifulSoup and lxml.
- Pydantic schema validation for book records.
- JSON and CSV export.
- Basic HTML dashboard.
- pytest test suite.
- GitHub Actions CI pipeline.
