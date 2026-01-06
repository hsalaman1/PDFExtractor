"""Vercel Serverless Function for PDF extraction."""

import base64
import hashlib
import json
import tempfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

import fitz  # PyMuPDF


def compute_file_hash(data: bytes) -> str:
    """Compute SHA256 hash of file data."""
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def extract_metadata(doc: fitz.Document, filename: str) -> dict:
    """Extract metadata from PDF document."""
    meta = doc.metadata or {}
    keywords = []
    if meta.get("keywords"):
        keywords = [k.strip() for k in meta["keywords"].split(",") if k.strip()]

    return {
        "title": meta.get("title") or Path(filename).stem,
        "author": meta.get("author") or None,
        "subject": meta.get("subject") or None,
        "keywords": keywords,
        "creator": meta.get("creator") or None,
        "creation_date": meta.get("creationDate") or None,
        "page_count": doc.page_count,
    }


def extract_toc(doc: fitz.Document) -> list:
    """Extract table of contents from PDF."""
    toc = doc.get_toc()
    return [
        {"level": level, "title": title, "page": page}
        for level, title, page in toc
    ]


def format_toc(toc: list, max_width: int = 60) -> str:
    """Format TOC for text output."""
    if not toc:
        return ""

    lines = []
    for entry in toc:
        indent = "  " * (entry["level"] - 1)
        title = entry["title"]
        page = entry["page"]
        prefix = f"{indent}{title}"
        suffix = f"Page {page}"
        dots_count = max_width - len(prefix) - len(suffix)
        dots = "." * max(3, dots_count)
        lines.append(f"{prefix}{dots}{suffix}")

    return "\n".join(lines)


def extract_text_by_page(doc: fitz.Document) -> list:
    """Extract text from each page."""
    pages = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        pages.append({
            "page": page_num + 1,
            "text": text.strip()
        })
    return pages


def extract_pdf(pdf_data: bytes, filename: str, output_format: str = "txt") -> dict:
    """Extract content from PDF data."""
    file_hash = compute_file_hash(pdf_data)

    # Write to temp file for fitz
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_data)
        tmp_path = tmp.name

    try:
        doc = fitz.open(tmp_path)

        metadata = extract_metadata(doc, filename)
        toc = extract_toc(doc)
        pages = extract_text_by_page(doc)

        doc.close()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    result = {
        "source_file": filename,
        "extraction_date": datetime.now().isoformat(),
        "file_hash": file_hash,
        "metadata": metadata,
        "toc": toc,
        "pages": pages,
    }

    # Generate text output
    if output_format in ("txt", "both"):
        lines = [
            f"# {metadata.get('title', filename)}",
        ]
        if metadata.get("author"):
            lines.append(f"# Author: {metadata['author']}")
        lines.append(f"# Source: {filename}")
        lines.append(f"# Pages: {metadata['page_count']}")
        lines.append("=" * 60)
        lines.append("")

        if toc:
            lines.append("TABLE OF CONTENTS")
            lines.append("-" * 40)
            lines.append(format_toc(toc))
            lines.append("")
            lines.append("=" * 60)
            lines.append("")

        for page_data in pages:
            lines.append(f"\n--- Page {page_data['page']} ---\n")
            lines.append(page_data["text"])

        result["text_output"] = "\n".join(lines)

    return result


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            content_type = self.headers.get("Content-Type", "")

            if content_length == 0:
                self.send_error(400, "No data received")
                return

            body = self.rfile.read(content_length)

            # Parse multipart form data or JSON
            if "application/json" in content_type:
                data = json.loads(body)
                # Expect base64 encoded PDF
                pdf_data = base64.b64decode(data.get("file", ""))
                filename = data.get("filename", "document.pdf")
                output_format = data.get("format", "txt")
            else:
                # Handle multipart form data
                self.send_error(400, "Please send JSON with base64 encoded file")
                return

            if not pdf_data:
                self.send_error(400, "No PDF data provided")
                return

            # Extract PDF
            result = extract_pdf(pdf_data, filename, output_format)

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
