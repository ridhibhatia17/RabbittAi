import io
from typing import Any

import pandas as pd
from fastapi import HTTPException


def parse_sales_file(contents: bytes, filename: str) -> dict[str, Any]:
    """Parse a CSV or XLSX file and extract key sales metrics."""
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()

    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(contents))
        elif ext == ".xlsx":
            df = pd.read_excel(io.BytesIO(contents), engine="openpyxl")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse file: {exc}"
        ) from exc

    required_columns = {"Revenue", "Product_Category", "Region", "Units_Sold", "Status"}
    missing = required_columns - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )

    total_revenue = float(df["Revenue"].sum())
    top_category = str(df.groupby("Product_Category")["Revenue"].sum().idxmax())
    top_region = str(df.groupby("Region")["Revenue"].sum().idxmax())
    total_units = int(df["Units_Sold"].sum())

    status_counts = df["Status"].str.strip().str.lower().value_counts()
    cancelled_orders = int(status_counts.get("cancelled", 0))
    completed_orders = int(
        status_counts.get("delivered", 0) + status_counts.get("shipped", 0)
    )
    total_orders = cancelled_orders + completed_orders
    cancelled_ratio = round(cancelled_orders / total_orders, 4) if total_orders else 0.0

    revenue_by_region = (
        df.groupby("Region")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    return {
        "total_revenue": total_revenue,
        "top_category": top_category,
        "top_region": top_region,
        "total_units": total_units,
        "cancelled_orders": cancelled_orders,
        "completed_orders": completed_orders,
        "revenue_by_region": revenue_by_region,
        "cancelled_ratio": cancelled_ratio,
    }
