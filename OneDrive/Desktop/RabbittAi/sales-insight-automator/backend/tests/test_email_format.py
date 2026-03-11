"""Tests for the email_service module (formatting only, no SMTP)."""

from app.email_service import _format_summary_as_html


def test_numbered_points_to_ol():
    text = "1. Revenue is strong.\n2. North leads sales.\n3. Low cancellation rate."
    html = _format_summary_as_html(text)
    assert "<ol>" in html
    assert "<li>Revenue is strong.</li>" in html
    assert "<li>North leads sales.</li>" in html
    assert "<li>Low cancellation rate.</li>" in html


def test_mixed_text_and_points():
    text = "Executive Summary\n1. Revenue up.\n2. Growth steady."
    html = _format_summary_as_html(text)
    assert "<p>Executive Summary</p>" in html
    assert "<ol>" in html
    assert html.index("<p>") < html.index("<ol>")


def test_no_numbered_lines_fallback():
    text = "Just a plain paragraph.\nAnother line."
    html = _format_summary_as_html(text)
    assert "<br>" in html
    assert "<ol>" not in html


def test_parenthesis_numbering():
    text = "1) First point.\n2) Second point."
    html = _format_summary_as_html(text)
    assert "<ol>" in html
    assert "<li>First point.</li>" in html
