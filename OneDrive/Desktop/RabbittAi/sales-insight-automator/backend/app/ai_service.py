import os
import time
from typing import Any

from groq import Groq
from fastapi import HTTPException

_MAX_RETRIES = 3


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")
    return Groq(api_key=api_key)


def generate_sales_summary(metrics: dict[str, Any]) -> str:
    """Send extracted sales metrics to Groq and return an executive summary."""
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

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as exc:
            last_exc = exc
            # Retry on 429 rate-limit errors
            if "429" in str(exc) or "rate_limit" in str(exc).lower():
                time.sleep(2 ** attempt * 10)  # 10s, 20s, 40s
                continue
            raise HTTPException(
                status_code=502, detail=f"Groq API error: {exc}"
            ) from exc

    raise HTTPException(
        status_code=429,
        detail=f"Groq API rate limit exceeded after {_MAX_RETRIES} retries: {last_exc}",
    ) from last_exc
