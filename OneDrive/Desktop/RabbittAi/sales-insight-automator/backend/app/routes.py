import asyncio
from functools import partial

from fastapi import APIRouter, File, Form, UploadFile

from app.ai_service import generate_sales_summary
from app.email_service import send_email
from app.file_parser import parse_sales_file
from app.schemas import AnalyzeSalesResponse
from app.security import read_file_with_size_check, validate_file

router = APIRouter()


@router.post(
    "/analyze-sales",
    response_model=AnalyzeSalesResponse,
    summary="Analyze sales data and email executive summary",
    description=(
        "Upload a `.csv` or `.xlsx` sales file and provide a recipient email. "
        "The service parses the file, extracts key metrics, generates an "
        "AI-powered executive summary via Google Gemini, and emails it to the "
        "specified recipient."
    ),
)
async def analyze_sales(
    file: UploadFile = File(..., description="Sales data file (.csv or .xlsx)"),
    recipient_email: str = Form(..., description="Email address to receive the summary"),
):
    # 1. Validate file type and size header
    validate_file(file)

    # 2. Read contents with streaming size check
    contents = await read_file_with_size_check(file)

    # 3. Parse file and extract sales metrics
    loop = asyncio.get_event_loop()
    metrics = await loop.run_in_executor(
        None, parse_sales_file, contents, file.filename or "upload.csv"
    )

    # 4. Generate AI executive summary via Gemini (blocking I/O → thread pool)
    summary = await loop.run_in_executor(None, generate_sales_summary, metrics)

    # 5. Email the summary with revenue-by-region chart to the recipient
    await loop.run_in_executor(
        None, partial(send_email, recipient_email, summary, metrics.get("revenue_by_region"))
    )

    return AnalyzeSalesResponse(
        status="success",
        message="Sales summary generated and sent.",
    )
