# Bonus Stage: The AI Rematch — Engineering Diff & Analysis

## 1. Overview
We challenged an AI to generate the entire scraping pipeline from a concise specification prompt, quarantined inside `ai-version/`. We then evaluated both implementations against the 7 checkpoint criteria.

---

## 2. Checkpoint Comparison

| Metric / Checkpoint | Hand-Crafted Pipeline (`src/`) | AI Quarantined Version (`ai-version/`) |
|---------------------|--------------------------------|-----------------------------------------|
| **Catalogue Scope** | Exactly 3 pages discovered via pagination | Exactly 3 pages discovered via pagination |
| **Unique Books** | 60 unique canonical URLs | 60 unique URLs |
| **Raw Field Provenance** | 8 keys with ISO 8601 UTC timestamp | 8 keys with ISO 8601 timestamp |
| **Schema Validation** | Strict Pydantic v2 + custom validators (`gt=0`, `le=5`, non-empty title) | Standard Pydantic model |
| **Encoding Resilience** | Cleans `Â£` / `\xa3` encoding artifacts | Uses standard regex; misses some character artifacts |
| **Transient Retries** | Exponential backoff + jitter + `Retry-After` compliance (`src/backoff.py`) | Single retry or catch-all exception |
| **Observability** | JSON report + CSV export + interactive visual HTML dashboard | Basic JSON summary only |
| **Test Suite** | 19 unit tests with HTML fixtures (`tests/`) | No test suite |

---

## 3. What Did the AI Do Better?
1. **Conciseness**: The AI combined extraction, normalization, and model validation into a single linear loop (~130 lines), which is easy to read at a glance for small scripts.
2. **Compact Cache Key Generation**: Used MD5 hashes directly on URLs to produce clean filenames without needing regex sanitization.

---

## 4. What Did It Get Wrong or Silently Skip?
1. **Encoding Noise in Prices**: Did not account for `requests` defaulting to `ISO-8859-1` on certain HTML responses, which produces `Â£` characters. Our hand-crafted pipeline explicitly checks `response.apparent_encoding`.
2. **Distinguishing Error Types for Retries**: The AI caught `Exception` generically without checking if the HTTP status was a `404` (never retry) vs a `500` / `503` (retry with backoff). Asking again on a 404 is impolite robot behavior.
3. **Modular Separation of Concerns**: Putting network fetching, parsing, validation, and serialization in one file makes unit testing with mock fixtures difficult without hitting the network.

---

## 5. What Did My Prompt Forget to Say?
1. The prompt did not specify how character encodings (like GBP `£` signs) should be cleaned from the HTTP response headers.
2. The prompt did not mandate separate test fixtures for parser unit testing.
3. The prompt did not specify generating a visual HTML dashboard or CSV format conversion.

---

## 6. Rematch: Improved Prompt Specification
```text
Build a modular Python scraping pipeline for Books to Scrape (3 pages, 60 books).
Enforce:
1. ISO-8859-1 -> UTF-8 decoding fallback for pound symbols.
2. Modular architecture (extract.py, normalizer.py, storage.py, retry.py, reporter.py).
3. Exponential backoff with jitter for 5xx/timeouts; strictly NO retry for 404/403.
4. Separate error routing to output/errors.json and export to output/books.csv.
5. Standalone pytest suite with saved HTML fixtures.
```
