"""
Local Observability Dashboard Generator.
Generates an interactive, standalone HTML dashboard for viewing scraping results.
"""

import json
import os


def generate_dashboard_html(
    books_json_path: str = "output/books.json",
    report_json_path: str = "output/run-report.json",
    output_html_path: str = "output/dashboard.html",
) -> str:
    """
    Generate an HTML observability dashboard from books.json and run-report.json.
    """
    books = []
    if os.path.exists(books_json_path):
        with open(books_json_path, "r", encoding="utf-8") as f:
            books = json.load(f)

    report = {}
    if os.path.exists(report_json_path):
        with open(report_json_path, "r", encoding="utf-8") as f:
            report = json.load(f)

    prices = [b.get("price_gbp", 0.0) for b in books]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0

    ratings_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for b in books:
        r = b.get("rating", 0)
        if r in ratings_dist:
            ratings_dist[r] += 1

    total_stock = sum(b.get("stock_count", 0) for b in books)

    books_json_embedded = json.dumps(books, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Polite Scraper — Observability Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #111827;
      --card-border: #1f2937;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #38bdf8;
      --accent: #818cf8;
      --success: #34d399;
      --warning: #fbbf24;
      --danger: #f87171;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 32px 24px;
      line-height: 1.5;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      flex-wrap: wrap;
      gap: 16px;
    }}
    h1 {{
      font-size: 28px;
      font-weight: 800;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 9999px;
      font-size: 13px;
      color: var(--primary);
      font-family: 'JetBrains Mono', monospace;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
    }}
    .card-title {{
      font-size: 13px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }}
    .card-value {{
      font-size: 32px;
      font-weight: 700;
      color: #fff;
    }}
    .card-sub {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }}
    .table-container {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      overflow: hidden;
      margin-top: 24px;
    }}
    .search-bar {{
      padding: 16px 20px;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      gap: 12px;
    }}
    input[type="text"] {{
      flex: 1;
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 8px;
      padding: 10px 16px;
      color: #fff;
      font-size: 14px;
      outline: none;
    }}
    input[type="text"]:focus {{
      border-color: var(--primary);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      text-align: left;
    }}
    th {{
      background: #172033;
      padding: 14px 20px;
      font-weight: 600;
      color: var(--text-muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    td {{
      padding: 14px 20px;
      border-top: 1px solid var(--card-border);
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}
    .price-tag {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      color: var(--success);
    }}
    .rating-stars {{
      color: var(--warning);
      letter-spacing: 2px;
    }}
    a.book-link {{
      color: var(--primary);
      text-decoration: none;
      font-weight: 500;
    }}
    a.book-link:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>The Polite Scraper</h1>
        <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">Books to Scrape &bull; Observability Dashboard</p>
      </div>
      <div class="badge">
        <span>&#9679;</span> Last Fresh: {report.get('end_time', 'N/A')[:19].replace('T', ' ')} UTC
      </div>
    </header>

    <div class="grid">
      <div class="card">
        <div class="card-title">Total Books Scraped</div>
        <div class="card-value">{len(books)}</div>
        <div class="card-sub">{report.get('catalogue_pages_fetched', 3)} Catalogue Pages</div>
      </div>
      <div class="card">
        <div class="card-title">Average Price</div>
        <div class="card-value">£{avg_price}</div>
        <div class="card-sub">Range: £{min_price} &ndash; £{max_price}</div>
      </div>
      <div class="card">
        <div class="card-title">Total Inventory Stock</div>
        <div class="card-value">{total_stock:,}</div>
        <div class="card-sub">Units available in catalog</div>
      </div>
      <div class="card">
        <div class="card-title">Run Duration</div>
        <div class="card-value">{report.get('duration_seconds', 0.0)}s</div>
        <div class="card-sub">Cache hits: {report.get('cache_hits', 0)} / Failed: {report.get('failed_pages', 0)}</div>
      </div>
    </div>

    <div class="table-container">
      <div class="search-bar">
        <input type="text" id="searchInput" placeholder="Search by title, price, rating or availability..." onkeyup="filterTable()">
      </div>
      <table id="booksTable">
        <thead>
          <tr>
            <th>Title</th>
            <th>Price (GBP)</th>
            <th>Rating</th>
            <th>Availability</th>
          </tr>
        </thead>
        <tbody id="tableBody">
        </tbody>
      </table>
    </div>
  </div>

  <script>
    const books = {books_json_embedded};
    const tbody = document.getElementById("tableBody");

    function renderTable(data) {{
      tbody.innerHTML = "";
      data.forEach(b => {{
        const row = document.createElement("tr");
        const stars = "★".repeat(b.rating) + "☆".repeat(5 - b.rating);
        row.innerHTML = `
          <td><a class="book-link" href="${{b.product_url}}" target="_blank">${{b.title}}</a></td>
          <td class="price-tag">£${{b.price_gbp.toFixed(2)}}</td>
          <td class="rating-stars">${{stars}} <span style="font-size: 11px; color: var(--text-muted);">(${{b.rating_text}})</span></td>
          <td>${{b.availability_text}}</td>
        `;
        tbody.appendChild(row);
      }});
    }}

    function filterTable() {{
      const query = document.getElementById("searchInput").value.toLowerCase();
      const filtered = books.filter(b =>
        b.title.toLowerCase().includes(query) ||
        b.availability_text.toLowerCase().includes(query) ||
        b.price_text.toLowerCase().includes(query) ||
        b.rating_text.toLowerCase().includes(query)
      );
      renderTable(filtered);
    }}

    renderTable(books);
  </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_html_path
