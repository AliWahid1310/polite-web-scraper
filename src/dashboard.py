"""
Local Observability Dashboard Generator.
Generates an interactive, modern, standalone glassmorphic HTML dashboard
featuring real-time Chart.js visualizations, multi-column search,
faceted filtering, interactive book detail modals, and client-side data exports.
"""

from __future__ import annotations

import json
import os
from typing import Any


def generate_dashboard_html(
    books_json_path: str = "output/books.json",
    report_json_path: str = "output/run-report.json",
    output_html_path: str = "output/dashboard.html",
) -> str:
    """
    Generate a high-performance observability dashboard from books.json and run-report.json.
    Includes Chart.js analytics, instant search, star-rating chips, book detail modal,
    and client-side CSV/JSON export.
    """
    books: list[dict[str, Any]] = []
    if os.path.exists(books_json_path):
        with open(books_json_path, "r", encoding="utf-8") as f:
            books = json.load(f)

    report: dict[str, Any] = {}
    if os.path.exists(report_json_path):
        with open(report_json_path, "r", encoding="utf-8") as f:
            report = json.load(f)

    # Compute high-level KPI metrics
    prices = [float(b.get("price_gbp", 0.0)) for b in books]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0

    ratings_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for b in books:
        r = int(b.get("rating", 0))
        if r in ratings_dist:
            ratings_dist[r] += 1

    total_stock = sum(int(b.get("stock_count", 0)) for b in books)
    total_valuation = sum(float(b.get("price_gbp", 0.0)) * int(b.get("stock_count", 0)) for b in books)
    in_stock_count = sum(1 for b in books if int(b.get("stock_count", 0)) > 0)
    out_of_stock_count = len(books) - in_stock_count

    # Price histogram distribution bins with formatted labels
    price_bins = {"Under £20": 0, "£20 to £40": 0, "£40 to £60": 0, "Over £60": 0}
    for p in prices:
        if p < 20.0:
            price_bins["Under £20"] += 1
        elif p < 40.0:
            price_bins["£20 to £40"] += 1
        elif p < 60.0:
            price_bins["£40 to £60"] += 1
        else:
            price_bins["Over £60"] += 1

    books_json_embedded = json.dumps(books, ensure_ascii=False)
    price_bins_embedded = json.dumps(price_bins)
    ratings_dist_embedded = json.dumps(ratings_dist)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Polite Scraper — Enterprise Observability Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <!-- Chart.js CDN for interactive visual analytics -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: rgba(17, 24, 39, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover-border: rgba(56, 189, 248, 0.4);
      --text: #f3f4f6;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.25);
      --accent: #818cf8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --modal-overlay: rgba(0, 0, 0, 0.8);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 10% 10%, #0d1527 0%, var(--bg) 100%);
      color: var(--text);
      min-height: 100vh;
      padding: 32px 24px;
      line-height: 1.5;
    }}
    .container {{ max-width: 1400px; margin: 0 auto; }}

    /* Header */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
      flex-wrap: wrap;
      gap: 16px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}
    .brand-icon {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 20px;
      color: #0b0f19;
      box-shadow: 0 0 20px var(--primary-glow);
    }}
    h1 {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.02em;
      background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .header-actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 9999px;
      font-size: 13px;
      color: var(--primary);
      font-family: 'JetBrains Mono', monospace;
    }}
    .pulse-dot {{
      width: 8px;
      height: 8px;
      background: var(--success);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--success);
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.3); opacity: 0.6; }}
    }}

    /* Export buttons */
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.2s ease;
      text-decoration: none;
    }}
    .btn-primary {{
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #fff;
    }}
    .btn-primary:hover {{
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3);
    }}
    .btn-secondary {{
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border-color: var(--card-border);
    }}
    .btn-secondary:hover {{
      background: rgba(255, 255, 255, 0.1);
      border-color: var(--primary);
    }}

    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 22px;
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card:hover {{
      border-color: var(--card-hover-border);
      transform: translateY(-2px);
    }}
    .kpi-title {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 600;
      margin-bottom: 8px;
    }}
    .kpi-value {{
      font-size: 32px;
      font-weight: 800;
      color: #fff;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    .kpi-sub {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 6px;
    }}

    /* Charts Section */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 20px;
      margin-bottom: 32px;
    }}
    .chart-card {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
      position: relative;
    }}
    .chart-title {{
      font-size: 15px;
      font-weight: 700;
      margin-bottom: 16px;
      color: var(--text);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .chart-container {{
      position: relative;
      height: 240px;
      width: 100%;
    }}

    /* Control Bar & Filter Chips */
    .filter-panel {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 18px;
      padding: 20px;
      margin-bottom: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    .search-row {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .search-box {{
      flex: 1;
      min-width: 260px;
      position: relative;
    }}
    .search-box input {{
      width: 100%;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 12px 18px;
      color: #fff;
      font-size: 14px;
      outline: none;
      transition: all 0.2s ease;
    }}
    .search-box input:focus {{
      border-color: var(--primary);
      box-shadow: 0 0 12px var(--primary-glow);
    }}
    .filter-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .filter-label {{
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
    }}
    .chip {{
      padding: 6px 14px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      color: var(--text-muted);
    }}
    .chip:hover, .chip.active {{
      background: rgba(56, 189, 248, 0.15);
      border-color: var(--primary);
      color: var(--primary);
    }}
    select.sort-select {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #fff;
      padding: 10px 14px;
      border-radius: 10px;
      font-size: 13px;
      outline: none;
      cursor: pointer;
    }}

    /* Table */
    .table-wrapper {{
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      overflow: hidden;
      margin-bottom: 40px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 14px;
    }}
    th {{
      background: rgba(15, 23, 42, 0.9);
      padding: 16px 20px;
      font-weight: 700;
      color: var(--text-muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border-bottom: 1px solid var(--card-border);
    }}
    td {{
      padding: 16px 20px;
      border-top: 1px solid var(--card-border);
      vertical-align: middle;
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
      cursor: pointer;
    }}
    .book-title-cell {{
      font-weight: 600;
      color: #fff;
      max-width: 320px;
    }}
    .price-pill {{
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: var(--success);
      background: rgba(16, 185, 129, 0.1);
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid rgba(16, 185, 129, 0.2);
      display: inline-block;
    }}
    .rating-badge {{
      color: var(--warning);
      font-size: 14px;
      letter-spacing: 2px;
    }}
    .stock-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
    }}
    .in-stock {{
      background: rgba(56, 189, 248, 0.1);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.25);
    }}
    .out-stock {{
      background: rgba(239, 68, 68, 0.1);
      color: var(--danger);
      border: 1px solid rgba(239, 68, 68, 0.25);
    }}

    /* Modal */
    .modal-overlay {{
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: var(--modal-overlay);
      backdrop-filter: blur(8px);
      z-index: 999;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }}
    .modal-content {{
      background: #0f172a;
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 20px;
      width: 100%;
      max-width: 650px;
      padding: 32px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
      position: relative;
    }}
    .modal-close {{
      position: absolute;
      top: 20px;
      right: 20px;
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 24px;
      cursor: pointer;
    }}
    .modal-close:hover {{ color: #fff; }}
    .modal-title {{
      font-size: 20px;
      font-weight: 800;
      margin-bottom: 12px;
      color: #fff;
    }}
    .modal-meta {{
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }}
    .modal-desc {{
      font-size: 14px;
      color: #cbd5e1;
      line-height: 1.6;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      padding: 16px;
      border-radius: 12px;
      margin-bottom: 24px;
      max-height: 200px;
      overflow-y: auto;
    }}
    .modal-provenance {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      gap: 6px;
      border-top: 1px solid var(--card-border);
      padding-top: 16px;
    }}
    .modal-actions {{
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-icon">P</div>
        <div>
          <h1>The Polite Scraper</h1>
          <p style="color: var(--text-muted); font-size: 13px;">Enterprise Observability & Analytics Dashboard &bull; Books to Scrape</p>
        </div>
      </div>
      <div class="header-actions">
        <div class="badge">
          <div class="pulse-dot"></div>
          <span>Run: {report.get('end_time', 'N/A')[:19].replace('T', ' ')} UTC</span>
        </div>
        <button class="btn btn-secondary" onclick="exportData('csv')">Export CSV</button>
        <button class="btn btn-primary" onclick="exportData('json')">Export JSON</button>
      </div>
    </header>

    <!-- KPI Grid -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Total Books Scraped</div>
        <div class="kpi-value">{len(books)}</div>
        <div class="kpi-sub">{report.get('catalogue_pages_fetched', 3)} Catalogue Pages Discovered</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Average Price</div>
        <div class="kpi-value">£{avg_price}</div>
        <div class="kpi-sub">Spread: £{min_price} &ndash; £{max_price}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Total Inventory Valuation</div>
        <div class="kpi-value">£{total_valuation:,.2f}</div>
        <div class="kpi-sub">{total_stock:,} total units in stock</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Stock Availability</div>
        <div class="kpi-value">{in_stock_count} <span style="font-size: 14px; font-weight: 500; color: var(--text-muted);">/ {len(books)}</span></div>
        <div class="kpi-sub">{out_of_stock_count} titles out of stock</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Execution Politeness</div>
        <div class="kpi-value">{report.get('duration_seconds', 0.0)}s</div>
        <div class="kpi-sub">Cache Hits: {report.get('cache_hits', 0)} &bull; Failures: {report.get('failed_pages', 0)}</div>
      </div>
    </div>

    <!-- Interactive Visual Charts -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">
          <span>Price Distribution (GBP)</span>
          <span style="font-size: 12px; color: var(--primary);">4 Bins</span>
        </div>
        <div class="chart-container">
          <canvas id="priceChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-title">
          <span>Star Rating Breakdown</span>
          <span style="font-size: 12px; color: var(--accent);">1 to 5 Stars</span>
        </div>
        <div class="chart-container">
          <canvas id="ratingChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Filter Control Panel -->
    <div class="filter-panel">
      <div class="search-row">
        <div class="search-box">
          <input type="text" id="searchInput" placeholder="Search by title, description, or keyword..." oninput="applyFilters()">
        </div>
        <select class="sort-select" id="sortSelect" onchange="applyFilters()">
          <option value="default">Sort by: Default Crawl Order</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="rating_desc">Highest Rated (5★ → 1★)</option>
          <option value="stock_desc">Highest Stock Available</option>
          <option value="title_asc">Title (A &rarr; Z)</option>
        </select>
      </div>
      <div class="filter-row">
        <span class="filter-label">Filter by Rating:</span>
        <div class="chip active" onclick="setRatingFilter(0, this)">All</div>
        <div class="chip" onclick="setRatingFilter(5, this)">5 Stars</div>
        <div class="chip" onclick="setRatingFilter(4, this)">4 Stars</div>
        <div class="chip" onclick="setRatingFilter(3, this)">3 Stars</div>
        <div class="chip" onclick="setRatingFilter(2, this)">2 Stars</div>
        <div class="chip" onclick="setRatingFilter(1, this)">1 Star</div>

        <span class="filter-label" style="margin-left: 12px;">Stock:</span>
        <div class="chip active" onclick="setStockFilter('all', this)">All</div>
        <div class="chip" onclick="setStockFilter('instock', this)">In Stock Only</div>
        <div class="chip" onclick="setStockFilter('outofstock', this)">Out of Stock</div>
        <span id="resultCountBadge" style="margin-left: auto; font-size: 13px; color: var(--primary); font-family: 'JetBrains Mono', monospace; font-weight: 600;"></span>
      </div>
    </div>

    <!-- Data Table -->
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Book Title</th>
            <th>Price (GBP)</th>
            <th>Rating</th>
            <th>Availability</th>
            <th>Total Value</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>

  <!-- Book Detail Modal -->
  <div class="modal-overlay" id="bookModal" onclick="closeModalOnOverlay(event)">
    <div class="modal-content">
      <button class="modal-close" onclick="closeModal()">&times;</button>
      <div class="modal-title" id="mTitle">Book Title</div>
      <div class="modal-meta" id="mMeta"></div>
      <div class="modal-desc" id="mDesc">Description text...</div>
      <div class="modal-provenance" id="mProvenance"></div>
      <div class="modal-actions">
        <button class="btn btn-secondary" onclick="copyModalJson()">Copy JSON</button>
        <a id="mProductLink" class="btn btn-primary" href="#" target="_blank" rel="noopener">Open Product Page &rarr;</a>
      </div>
    </div>
  </div>

  <script>
    const books = {books_json_embedded};
    const priceBins = {price_bins_embedded};
    const ratingsDist = {ratings_dist_embedded};

    let selectedRating = 0;
    let selectedStock = 'all';
    let filteredBooks = [...books];

    // Render Chart.js visual charts
    function initCharts() {{
      // Price Histogram Chart
      const priceCtx = document.getElementById('priceChart').getContext('2d');
      new Chart(priceCtx, {{
        type: 'bar',
        data: {{
          labels: Object.keys(priceBins),
          datasets: [{{
            label: 'Books in Range',
            data: Object.values(priceBins),
            backgroundColor: 'rgba(56, 189, 248, 0.65)',
            borderColor: '#38bdf8',
            borderWidth: 1.5,
            borderRadius: 8,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            y: {{ grid: {{ color: 'rgba(255, 255, 255, 0.05)' }}, ticks: {{ color: '#94a3b8' }} }},
            x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }}
          }}
        }}
      }});

      // Rating Donut Chart
      const ratingCtx = document.getElementById('ratingChart').getContext('2d');
      new Chart(ratingCtx, {{
        type: 'doughnut',
        data: {{
          labels: ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
          datasets: [{{
            data: [ratingsDist[1], ratingsDist[2], ratingsDist[3], ratingsDist[4], ratingsDist[5]],
            backgroundColor: ['#ef4444', '#f97316', '#f59e0b', '#38bdf8', '#10b981'],
            borderWidth: 0,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 12 }} }} }}
          }}
        }}
      }});
    }}

    function renderTable(data) {{
      const tbody = document.getElementById("tableBody");
      tbody.innerHTML = "";

      if (data.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No matching books found.</td></tr>';
        return;
      }}

      data.forEach((b, idx) => {{
        const row = document.createElement("tr");
        row.onclick = () => openModal(b);
        const stars = "★".repeat(b.rating) + "☆".repeat(5 - b.rating);
        const inStock = b.stock_count > 0;
        const totalVal = (b.price_gbp * b.stock_count).toFixed(2);

        row.innerHTML = `
          <td style="color: var(--text-muted); font-size: 12px;">${{idx + 1}}</td>
          <td class="book-title-cell">${{b.title}}</td>
          <td><span class="price-pill">£${{b.price_gbp.toFixed(2)}}</span></td>
          <td><span class="rating-badge">${{stars}}</span> <span style="font-size: 11px; color: var(--text-muted);">(${{b.rating}})</span></td>
          <td><span class="stock-badge ${{inStock ? 'in-stock' : 'out-stock'}}">${{inStock ? '● ' + b.stock_count + ' in stock' : '○ Out of stock'}}</span></td>
          <td style="font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #cbd5e1;">£${{totalVal}}</td>
        `;
        tbody.appendChild(row);
      }});
    }}

    function applyFilters() {{
      const query = document.getElementById("searchInput").value.toLowerCase();
      const sortVal = document.getElementById("sortSelect").value;

      filteredBooks = books.filter(b => {{
        const matchesQuery = b.title.toLowerCase().includes(query) ||
          (b.description && b.description.toLowerCase().includes(query)) ||
          b.availability_text.toLowerCase().includes(query);

        const matchesRating = selectedRating === 0 || b.rating === selectedRating;
        const matchesStock = selectedStock === 'all' ||
          (selectedStock === 'instock' && b.stock_count > 0) ||
          (selectedStock === 'outofstock' && b.stock_count === 0);

        return matchesQuery && matchesRating && matchesStock;
      }});

      // Sorting
      if (sortVal === "price_asc") filteredBooks.sort((a, b) => a.price_gbp - b.price_gbp);
      else if (sortVal === "price_desc") filteredBooks.sort((a, b) => b.price_gbp - a.price_gbp);
      else if (sortVal === "rating_desc") filteredBooks.sort((a, b) => b.rating - a.rating);
      else if (sortVal === "stock_desc") filteredBooks.sort((a, b) => b.stock_count - a.stock_count);
      else if (sortVal === "title_asc") filteredBooks.sort((a, b) => a.title.localeCompare(b.title));

      const countBadge = document.getElementById("resultCountBadge");
      if (countBadge) countBadge.innerText = `Showing ${{filteredBooks.length}} of ${{books.length}} titles`;

      renderTable(filteredBooks);
    }}

    function setRatingFilter(rating, el) {{
      selectedRating = rating;
      el.parentElement.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
      applyFilters();
    }}

    function setStockFilter(stock, el) {{
      selectedStock = stock;
      el.parentElement.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
      applyFilters();
    }}

    let currentModalBook = null;

    // Modal
    function openModal(b) {{
      currentModalBook = b;
      document.getElementById("mTitle").innerText = b.title;
      const stars = "★".repeat(b.rating) + "☆".repeat(5 - b.rating);
      document.getElementById("mMeta").innerHTML = `
        <span class="price-pill">£${{b.price_gbp.toFixed(2)}}</span>
        <span class="rating-badge" style="margin-left: 8px;">${{stars}} (${{b.rating_text}})</span>
        <span class="stock-badge ${{b.stock_count > 0 ? 'in-stock' : 'out-stock'}}">${{b.availability_text}}</span>
      `;
      document.getElementById("mDesc").innerText = b.description || "No product description available.";
      document.getElementById("mProvenance").innerHTML = `
        <div><strong>Product URL:</strong> ${{b.product_url}}</div>
        <div><strong>Source Page:</strong> ${{b.source_page}}</div>
        <div><strong>Fetched At:</strong> ${{b.fetched_at}}</div>
      `;
      document.getElementById("mProductLink").href = b.product_url;
      document.getElementById("bookModal").style.display = "flex";
    }}

    function copyModalJson() {{
      if (currentModalBook) {{
        navigator.clipboard.writeText(JSON.stringify(currentModalBook, null, 2));
        alert("Book record copied to clipboard as formatted JSON!");
      }}
    }}

    function closeModal() {{
      document.getElementById("bookModal").style.display = "none";
    }}

    function closeModalOnOverlay(e) {{
      if (e.target.id === "bookModal") closeModal();
    }}

    // Client-side instant export
    function exportData(format) {{
      if (format === 'json') {{
        const blob = new Blob([JSON.stringify(filteredBooks, null, 2)], {{ type: 'application/json' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'books_filtered.json';
        a.click();
      }} else if (format === 'csv') {{
        const header = ["title", "price_gbp", "rating", "stock_count", "availability_text", "product_url", "source_page"];
        const rows = filteredBooks.map(b => [
          `"${{(b.title || '').replace(/"/g, '""')}}"`,
          b.price_gbp,
          b.rating,
          b.stock_count,
          `"${{(b.availability_text || '').replace(/"/g, '""')}}"`,
          `"${{(b.product_url || '')}}"`,
          `"${{(b.source_page || '')}}"`
        ]);
        const csvContent = [header.join(','), ...rows.map(r => r.join(','))].join('\\n');
        const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'books_filtered.csv';
        a.click();
      }}
    }}

    // Init
    initCharts();
    renderTable(books);
  </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(os.path.abspath(output_html_path)), exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_html_path
