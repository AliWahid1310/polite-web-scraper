"""
Unit tests for Statistical Analysis & Analytics Engine (src/analytics.py).
"""

from src.analytics import (
    calculate_inventory_metrics,
    calculate_price_statistics,
    calculate_rating_distribution,
    generate_full_analytics_summary,
)


def test_calculate_price_statistics_empty():
    stats = calculate_price_statistics([])
    assert stats["count"] == 0
    assert stats["mean_gbp"] == 0.0
    assert stats["median_gbp"] == 0.0
    assert stats["outliers"] == []


def test_calculate_price_statistics_single_item():
    records = [{"title": "Book 1", "price_gbp": 25.50}]
    stats = calculate_price_statistics(records)
    assert stats["count"] == 1
    assert stats["mean_gbp"] == 25.50
    assert stats["median_gbp"] == 25.50
    assert stats["std_dev_gbp"] == 0.0
    assert stats["outliers"] == []


def test_calculate_price_statistics_normal_and_outliers():
    # 10 records with typical prices around 20-30, and one outlier at 150.00
    records = [
        {"title": f"Book {i}", "price_gbp": float(20 + i)}
        for i in range(10)
    ]
    records.append({"title": "Expensive Rare Book", "price_gbp": 150.00})

    stats = calculate_price_statistics(records)
    assert stats["count"] == 11
    assert stats["min_gbp"] == 20.0
    assert stats["max_gbp"] == 150.0
    assert stats["iqr_gbp"] > 0
    assert len(stats["outliers"]) == 1
    assert stats["outliers"][0]["title"] == "Expensive Rare Book"
    assert stats["price_histogram"]["20-40"] >= 10
    assert stats["price_histogram"]["60+"] == 1


def test_calculate_rating_distribution():
    records = [
        {"rating": 1},
        {"rating": 1},
        {"rating": 3},
        {"rating": 5},
        {"rating": 5},
    ]
    dist = calculate_rating_distribution(records)
    assert dist["total_rated"] == 5
    assert dist["breakdown"][1] == 2
    assert dist["breakdown"][3] == 1
    assert dist["breakdown"][5] == 2
    assert dist["breakdown"][2] == 0
    assert dist["average_rating"] == 3.0
    assert dist["percentages"]["1"] == 40.0
    assert dist["percentages"]["5"] == 40.0


def test_calculate_inventory_metrics():
    records = [
        {"stock_count": 10, "price_gbp": 15.00},
        {"stock_count": 5, "price_gbp": 20.00},
        {"stock_count": 0, "price_gbp": 50.00},
    ]
    inv = calculate_inventory_metrics(records)
    assert inv["total_units"] == 15
    # (10 * 15) + (5 * 20) + (0 * 50) = 150 + 100 = 250.00
    assert inv["total_inventory_valuation_gbp"] == 250.00
    assert inv["in_stock_titles"] == 2
    assert inv["out_of_stock_titles"] == 1
    assert inv["average_stock_per_title"] == 5.0


def test_generate_full_analytics_summary():
    records = [
        {"title": "Sample", "price_gbp": 10.0, "rating": 4, "stock_count": 2}
    ]
    summary = generate_full_analytics_summary(records)
    assert "pricing" in summary
    assert "ratings" in summary
    assert "inventory" in summary
    assert summary["pricing"]["count"] == 1
    assert summary["ratings"]["breakdown"][4] == 1
    assert summary["inventory"]["total_units"] == 2
