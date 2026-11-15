"""
Statistical Analysis and Analytics Engine.
Computes comprehensive pricing metrics, IQR outlier detection, rating distributions,
and total inventory valuations for scraped book datasets.
"""

from __future__ import annotations

import math
from typing import Any


def calculate_price_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate extensive pricing statistics including mean, median, std dev,
    interquartile range (IQR), and statistical outliers.
    """
    if not records:
        return {
            "count": 0,
            "min_gbp": 0.0,
            "max_gbp": 0.0,
            "mean_gbp": 0.0,
            "median_gbp": 0.0,
            "std_dev_gbp": 0.0,
            "q1_gbp": 0.0,
            "q3_gbp": 0.0,
            "iqr_gbp": 0.0,
            "outliers": [],
            "price_histogram": {"0-20": 0, "20-40": 0, "40-60": 0, "60+": 0},
        }

    prices = sorted([float(r.get("price_gbp", 0.0)) for r in records])
    n = len(prices)

    min_p = min(prices)
    max_p = max(prices)
    mean_p = sum(prices) / n

    # Median
    if n % 2 == 1:
        median_p = prices[n // 2]
    else:
        median_p = (prices[n // 2 - 1] + prices[n // 2]) / 2.0

    # Sample standard deviation
    if n > 1:
        variance = sum((p - mean_p) ** 2 for p in prices) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    # Quartiles (Tukey method)
    def _median_of(slice_list: list[float]) -> float:
        m = len(slice_list)
        if not slice_list:
            return 0.0
        if m % 2 == 1:
            return slice_list[m // 2]
        return (slice_list[m // 2 - 1] + slice_list[m // 2]) / 2.0

    if n % 2 == 0:
        lower_half = prices[: n // 2]
        upper_half = prices[n // 2 :]
    else:
        lower_half = prices[: n // 2]
        upper_half = prices[n // 2 + 1 :]

    q1 = _median_of(lower_half) if lower_half else min_p
    q3 = _median_of(upper_half) if upper_half else max_p
    iqr = round(q3 - q1, 2)

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = [
        {"title": r.get("title", ""), "price_gbp": float(r.get("price_gbp", 0.0))}
        for r in records
        if float(r.get("price_gbp", 0.0)) < lower_bound or float(r.get("price_gbp", 0.0)) > upper_bound
    ]

    # Histogram buckets
    histogram = {"0-20": 0, "20-40": 0, "40-60": 0, "60+": 0}
    for p in prices:
        if p < 20.0:
            histogram["0-20"] += 1
        elif p < 40.0:
            histogram["20-40"] += 1
        elif p < 60.0:
            histogram["40-60"] += 1
        else:
            histogram["60+"] += 1

    return {
        "count": n,
        "min_gbp": round(min_p, 2),
        "max_gbp": round(max_p, 2),
        "mean_gbp": round(mean_p, 2),
        "median_gbp": round(median_p, 2),
        "std_dev_gbp": round(std_dev, 2),
        "q1_gbp": round(q1, 2),
        "q3_gbp": round(q3, 2),
        "iqr_gbp": iqr,
        "outliers": outliers,
        "price_histogram": histogram,
    }


def calculate_rating_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate star rating distribution breakdown (1-5 stars) and weighted average.
    """
    dist: dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total = len(records)

    for r in records:
        rating = int(r.get("rating", 0))
        if rating in dist:
            dist[rating] += 1

    weighted_sum = sum(star * count for star, count in dist.items())
    avg_rating = round(weighted_sum / total, 2) if total > 0 else 0.0

    percentages = {
        str(k): round((v / total) * 100, 1) if total > 0 else 0.0
        for k, v in dist.items()
    }

    return {
        "breakdown": dist,
        "percentages": percentages,
        "average_rating": avg_rating,
        "total_rated": total,
    }


def calculate_inventory_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate inventory units, stock valuation in GBP, and in-stock vs out-of-stock counts.
    """
    total_units = 0
    total_valuation = 0.0
    in_stock = 0
    out_of_stock = 0

    for r in records:
        stock = int(r.get("stock_count", 0))
        price = float(r.get("price_gbp", 0.0))
        total_units += stock
        total_valuation += stock * price
        if stock > 0:
            in_stock += 1
        else:
            out_of_stock += 1

    n = len(records)
    avg_stock = round(total_units / n, 1) if n > 0 else 0.0

    return {
        "total_units": total_units,
        "total_inventory_valuation_gbp": round(total_valuation, 2),
        "in_stock_titles": in_stock,
        "out_of_stock_titles": out_of_stock,
        "average_stock_per_title": avg_stock,
    }


def generate_full_analytics_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate consolidated analytics summary across price, ratings, and inventory."""
    return {
        "pricing": calculate_price_statistics(records),
        "ratings": calculate_rating_distribution(records),
        "inventory": calculate_inventory_metrics(records),
    }
