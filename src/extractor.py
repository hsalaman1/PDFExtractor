"""PDF text and metadata extraction module."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"


def extract_metadata(doc: fitz.Document, file_path: Path) -> dict:
    """Extract metadata from PDF document."""
    meta = doc.metadata or {}

    # Try to extract ISBN from metadata or text
    isbn = None
    keywords = []

    if meta.get("keywords"):
        keywords = [k.strip() for k in meta["keywords"].split(",") if k.strip()]

    return {
        "title": meta.get("title") or file_path.stem,
        "author": meta.get("author") or None,
        "subject": meta.get("subject") or None,
        "keywords": keywords,
        "isbn": isbn,
        "publisher": meta.get("producer") or None,
        "creator": meta.get("creator") or None,
        "creation_date": meta.get("creationDate") or None,
        "modification_date": meta.get("modDate") or None,
        "page_count": doc.page_count,
    }


def extract_toc(doc: fitz.Document) -> list:
    """Extract table of contents / bookmarks from PDF."""
    toc = doc.get_toc()  # Returns list of [level, title, page_number]
    return [
        {"level": level, "title": title, "page": page}
        for level, title, page in toc
    ]


def format_toc(toc: list, max_width: int = 60) -> str:
    """Format TOC for text output."""
    if not toc:
        return "No table of contents found in document.\n"

    lines = []
    for entry in toc:
        indent = "  " * (entry["level"] - 1)
        title = entry["title"]
        page = entry["page"]

        # Calculate dots
        prefix = f"{indent}{title}"
        suffix = f"Page {page}"
        dots_count = max_width - len(prefix) - len(suffix)
        dots = "." * max(3, dots_count)

        lines.append(f"{prefix}{dots}{suffix}")

    return "\n".join(lines)


def extract_text_by_page(doc: fitz.Document) -> list:
    """Extract text from each page with page markers."""
    pages = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        pages.append({
            "page": page_num + 1,
            "text": text.strip()
        })
    return pages


def extract_pdf(
    pdf_path: str | Path,
    output_dir: Optional[str | Path] = None,
    output_format: str = "txt",
    include_metadata: bool = True,
    include_toc: bool = True,
) -> dict:
    """
    Extract content from a PDF file.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted content (default: same as PDF)
        output_format: Output format - 'txt', 'json', or 'both'
        include_metadata: Whether to extract and save metadata
        include_toc: Whether to extract and save table of contents

    Returns:
        Dictionary with extraction results
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if output_dir is None:
        output_dir = pdf_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = pdf_path.stem

    # Open PDF
    doc = fitz.open(pdf_path)

    try:
        # Extract content
        file_hash = compute_file_hash(pdf_path)
        metadata = extract_metadata(doc, pdf_path)
        toc = extract_toc(doc)
        pages = extract_text_by_page(doc)

        # Build result
        result = {
            "source_file": str(pdf_path.name),
            "source_path": str(pdf_path.absolute()),
            "extraction_date": datetime.now().isoformat(),
            "file_hash": file_hash,
            "metadata": metadata,
            "toc": toc,
            "pages": pages,
            "output_files": []
        }

        # Save text output
        if output_format in ("txt", "both"):
            txt_path = output_dir / f"{base_name}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"# {metadata.get('title', base_name)}\n")
                if metadata.get("author"):
                    f.write(f"# Author: {metadata['author']}\n")
                f.write(f"# Source: {pdf_path.name}\n")
                f.write(f"# Pages: {metadata['page_count']}\n")
                f.write("=" * 60 + "\n\n")

                for page_data in pages:
                    f.write(f"\n--- Page {page_data['page']} ---\n\n")
                    f.write(page_data["text"])
                    f.write("\n")

            result["output_files"].append(str(txt_path))

        # Save JSON output
        if output_format in ("json", "both"):
            json_path = output_dir / f"{base_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            result["output_files"].append(str(json_path))

        # Save TOC
        if include_toc and toc:
            toc_path = output_dir / f"{base_name}_toc.txt"
            with open(toc_path, "w", encoding="utf-8") as f:
                f.write(f"Table of Contents: {metadata.get('title', base_name)}\n")
                f.write("=" * 60 + "\n\n")
                f.write(format_toc(toc))
            result["output_files"].append(str(toc_path))

        # Save metadata
        if include_metadata:
            meta_path = output_dir / f"{base_name}_metadata.json"
            meta_output = {
                "source_file": result["source_file"],
                "extraction_date": result["extraction_date"],
                "file_hash": result["file_hash"],
                "metadata": result["metadata"],
                "toc": result["toc"]
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_output, f, indent=2, ensure_ascii=False)
            result["output_files"].append(str(meta_path))

        return result

    finally:
        doc.close()
