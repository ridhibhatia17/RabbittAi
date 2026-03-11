import io
import os
import re
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fastapi import HTTPException


def _generate_revenue_chart(revenue_by_region: dict[str, float]) -> bytes:
    """Create a bar chart of revenue by region and return PNG bytes."""
    regions = list(revenue_by_region.keys())
    revenues = [v / 1000 for v in revenue_by_region.values()]  # in thousands

    colors = ["#6C3CE1", "#34a853", "#ea4335", "#fbbc04", "#1a73e8"]
    bar_colors = [colors[i % len(colors)] for i in range(len(regions))]

    fig, ax = plt.subplots(figsize=(6, 3.2), dpi=150)
    bars = ax.bar(regions, revenues, color=bar_colors, width=0.55, edgecolor="white")

    for bar, val in zip(bars, revenues):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(revenues) * 0.02,
            f"\u20b9{val:,.1f}K",
            ha="center", va="bottom", fontsize=9, fontweight="bold", color="#333",
        )

    ax.set_ylabel("Revenue (\u20b9 thousands)", fontsize=10)
    ax.set_title("Revenue by Region", fontsize=13, fontweight="bold", pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _format_summary_as_html(summary: str) -> str:
    """Convert numbered-point plain text into an HTML ordered list."""
    lines = summary.strip().splitlines()
    items: list[str] = []
    non_list: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Match lines starting with a number followed by . or )
        m = re.match(r"^\d+[\.\)]\s*", stripped)
        if m:
            items.append(stripped[m.end():])
        elif stripped:
            non_list.append(stripped)

    if items:
        ol = "<ol>" + "".join(f"<li>{item}</li>" for item in items) + "</ol>"
        # Prepend any non-list text (e.g. a title line) as paragraphs
        prefix = "".join(f"<p>{p}</p>" for p in non_list)
        return prefix + ol

    # Fallback: no numbered lines detected, return as paragraphs
    return "<br>".join(lines)


def send_email(
    recipient: str,
    summary: str,
    revenue_by_region: dict[str, float] | None = None,
) -> None:
    """Send an HTML-formatted sales summary email with an optional chart."""
    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_email = os.getenv("SMTP_EMAIL", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    if not all([smtp_server, smtp_email, smtp_password]):
        raise HTTPException(
            status_code=500, detail="SMTP configuration is incomplete."
        )

    # Build the chart section if data is available
    chart_html = ""
    chart_bytes: bytes | None = None
    if revenue_by_region:
        chart_bytes = _generate_revenue_chart(revenue_by_region)
        chart_html = (
            '<h2 style="color:#6C3CE1;font-size:18px;margin-top:24px;">'
            'Revenue by Region</h2>'
            '<img src="cid:revenue_chart" alt="Revenue by Region Chart" '
            'style="max-width:100%;height:auto;border-radius:8px;" />'
        )

    # Convert numbered lines (e.g. "1. ...") into an HTML ordered list
    summary_html = _format_summary_as_html(summary)

    html_body = f"""\
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; background: #f4f2ff; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 32px; background: #ffffff; border-radius: 12px; }}
            .brand {{ color: #6C3CE1; font-size: 13px; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px; }}
            h1 {{ color: #1a1a2e; font-size: 22px; margin-top: 0; }}
            .divider {{ height: 3px; background: linear-gradient(90deg, #6C3CE1, #a78bfa); border: none; margin: 16px 0; border-radius: 2px; }}
            .summary {{ background: #f9f8ff; border-left: 4px solid #6C3CE1;
                        padding: 16px 20px; margin: 16px 0; line-height: 1.7; border-radius: 0 8px 8px 0; }}
            .summary ol {{ margin: 0; padding-left: 20px; }}
            .summary ol li {{ margin-bottom: 8px; }}
            .footer {{ font-size: 12px; color: #999; margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="https://rabbitt.ai/rabbits/rabbit1.svg" alt="RabbittAi" width="40" style="margin-bottom:8px;" />
            <p class="brand">RabbittAi</p>
            <h1>Sales Insight Report</h1>
            <hr class="divider" />
            <div class="summary">{summary_html}</div>
            {chart_html}
            <p class="footer">
                Generated by <strong>RabbittAi</strong> &middot; Sales Insight Automator
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("related")
    msg["Subject"] = "Sales Insight Report \u2014 Executive Summary"
    msg["From"] = smtp_email
    msg["To"] = recipient

    # Wrap text alternatives inside a multipart/alternative part
    msg_alt = MIMEMultipart("alternative")
    msg_alt.attach(MIMEText(summary, "plain"))
    msg_alt.attach(MIMEText(html_body, "html"))
    msg.attach(msg_alt)

    # Attach chart image as inline CID
    if chart_bytes:
        img_part = MIMEBase("image", "png")
        img_part.set_payload(chart_bytes)
        from email import encoders
        encoders.encode_base64(img_part)
        img_part.add_header("Content-ID", "<revenue_chart>")
        img_part.add_header(
            "Content-Disposition", "inline", filename="revenue_chart.png"
        )
        msg.attach(img_part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [recipient], msg.as_string())
    except smtplib.SMTPException as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to send email: {exc}"
        ) from exc
