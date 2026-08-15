# The Polite Web Scraper

A small, polite scraping pipeline that downloads the first three catalogue pages of [Books to Scrape](https://books.toscrape.com), visits all 60 book pages, turns messy HTML into clean, validated JSON records, survives broken pages without crashing, and ends every run with an honest report.

## Target Classification

| Field | Value |
|-------|-------|
| **Target site** | [Books to Scrape](https://books.toscrape.com) |
| **What it is** | A public practice sandbox — "a fictional bookstore that desperately wants to be scraped" ([toscrape.com](https://toscrape.com)) |
| **Scope** | First 3 catalogue pages only (60 books) |
| **Data collected** | Title, price, availability, rating, description, product URL |
| **robots.txt** | Returned **404 Not Found** — no robots file exists. A missing file is not permission; it is just a missing file. |
| **Why appropriate** | The site explicitly states it is built for people to practise scraping on it. We collect only public, fictional data from a sandbox designed for this exact purpose. |

> **I will not reuse this code on another site without checking its rules and terms first.**
