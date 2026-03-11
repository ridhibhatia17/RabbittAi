"""Tests for the file_parser module."""

import pytest

from app.file_parser import parse_sales_file


VALID_CSV = (
    "Revenue,Product_Category,Region,Units_Sold,Status\n"
    "10000,Electronics,North,50,Delivered\n"
    "5000,Home Appliances,South,30,Shipped\n"
    "2000,Electronics,East,10,Cancelled\n"
)


def test_parse_csv_total_revenue():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    assert metrics["total_revenue"] == 17000.0


def test_parse_csv_top_category():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    assert metrics["top_category"] == "Electronics"


def test_parse_csv_top_region():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    assert metrics["top_region"] == "North"


def test_parse_csv_units():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    assert metrics["total_units"] == 90


def test_parse_csv_order_counts():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    assert metrics["cancelled_orders"] == 1
    assert metrics["completed_orders"] == 2


def test_parse_csv_cancelled_ratio():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    expected = round(1 / 3, 4)
    assert metrics["cancelled_ratio"] == expected


def test_parse_csv_revenue_by_region():
    metrics = parse_sales_file(VALID_CSV.encode(), "sales.csv")
    rbr = metrics["revenue_by_region"]
    assert rbr["North"] == 10000.0
    assert rbr["South"] == 5000.0
    assert rbr["East"] == 2000.0


def test_missing_columns():
    bad_csv = "Revenue,Region\n100,North\n"
    with pytest.raises(Exception) as exc_info:
        parse_sales_file(bad_csv.encode(), "bad.csv")
    assert "Missing required columns" in str(exc_info.value.detail)


def test_unsupported_format():
    with pytest.raises(Exception) as exc_info:
        parse_sales_file(b"data", "file.txt")
    assert "Unsupported" in str(exc_info.value.detail)
