import os
from typing import Any

from google import genai
from fastapi import HTTPException


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def generate_sales_summary(metrics: dict[str, Any]) -> str:
    """Send extracted sales metrics to Google Gemini and return an executive summary."""
    client = _get_client()

    prompt = (
        "You are a business analyst AI. Generate a concise executive summary of the "
        "following sales data. The summary should be in a professional tone suitable "
        "for leadership. Format the summary as numbered points (1. 2. 3. etc.). "
        "All monetary values must be in Indian Rupees (₹). "
        "Do NOT use asterisks (*) or markdown formatting.\n\n"
        f"Total Revenue: \u20b9{metrics['total_revenue']:,.2f}\n"
        f"Top Product Category: {metrics['top_category']}\n"
        f"Region with Highest Sales: {metrics['top_region']}\n"
        f"Total Units Sold: {metrics['total_units']:,}\n"
        f"Cancelled Orders: {metrics['cancelled_orders']}\n"
        f"Completed Orders: {metrics['completed_orders']}\n"
        f"Cancelled vs Completed Ratio: {metrics['cancelled_ratio']:.2%}\n"
    )

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Gemini API error: {exc}"
        ) from exc
