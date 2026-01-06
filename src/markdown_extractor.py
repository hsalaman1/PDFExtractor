"""Markdown file extraction module."""

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"


def compute_data_hash(data: bytes) -> str:
    """Compute SHA256 hash of data."""
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}
    body = content

    # Check for YAML frontmatter (--- at start)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            except yaml.YAMLError:
                pass

    return frontmatter, body


def extract_headings(content: str) -> list:
    """Extract headings from markdown to build TOC."""
    toc = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        # ATX-style headings (# Heading)
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            # Remove trailing # if present
            title = re.sub(r"\s*#+\s*$", "", title)
            toc.append({
                "level": level,
                "title": title,
                "line": i + 1
            })

    return toc


def estimate_pages(content: str, chars_per_page: int = 3000) -> int:
    """Estimate page count based on character count."""
    return max(1, len(content) // chars_per_page + 1)


def split_into_sections(content: str, toc: list) -> list:
    """Split content into sections based on headings."""
    if not toc:
        return [{"section": 1, "title": "Content", "text": content.strip()}]

    lines = content.split("\n")
    sections = []

    for i, entry in enumerate(toc):
        start_line = entry["line"] - 1
        if i + 1 < len(toc):
            end_line = toc[i + 1]["line"] - 1
        else:
            end_line = len(lines)

        section_text = "\n".join(lines[start_line:end_line]).strip()
        sections.append({
            "section": i + 1,
            "title": entry["title"],
            "level": entry["level"],
            "text": section_text
        })

    return sections


def extract_metadata_from_frontmatter(frontmatter: dict, filename: str) -> dict:
    """Extract standard metadata fields from frontmatter."""
    return {
        "title": frontmatter.get("title") or Path(filename).stem,
        "author": frontmatter.get("author") or frontmatter.get("authors"),
        "subject": frontmatter.get("subject") or frontmatter.get("description"),
        "keywords": frontmatter.get("keywords") or frontmatter.get("tags") or [],
        "date": frontmatter.get("date"),
        "category": frontmatter.get("category"),
    }


def extract_markdown(
    md_path: str | Path,
    output_dir: Optional[str | Path] = None,
    output_format: str = "txt",
) -> dict:
    """
    Extract content from a Markdown file.

    Args:
        md_path: Path to the Markdown file
        output_dir: Directory to save extracted content
        output_format: Output format - 'txt', 'json', or 'both'

    Returns:
        Dictionary with extraction results
    """
    md_path = Path(md_path)
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    if output_dir is None:
        output_dir = md_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_name = md_path.stem

    # Read file
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    file_hash = compute_file_hash(md_path)

    # Extract frontmatter and body
    frontmatter, body = extract_frontmatter(content)
    metadata = extract_metadata_from_frontmatter(frontmatter, md_path.name)

    # Extract TOC from headings
    toc = extract_headings(body)

    # Estimate pages
    estimated_pages = estimate_pages(body)
    metadata["page_count"] = estimated_pages
    metadata["word_count"] = len(body.split())
    metadata["char_count"] = len(body)

    # Split into sections
    sections = split_into_sections(body, toc)

    result = {
        "source_file": str(md_path.name),
        "source_path": str(md_path.absolute()),
        "file_type": "markdown",
        "extraction_date": datetime.now().isoformat(),
        "file_hash": file_hash,
        "metadata": metadata,
        "frontmatter": frontmatter,
        "toc": toc,
        "sections": sections,
        "output_files": []
    }

    # Generate text output
    if output_format in ("txt", "both"):
        txt_path = output_dir / f"{base_name}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"# {metadata.get('title', base_name)}\n")
            if metadata.get("author"):
                author = metadata["author"]
                if isinstance(author, list):
                    author = ", ".join(author)
                f.write(f"# Author: {author}\n")
            f.write(f"# Source: {md_path.name}\n")
            f.write(f"# Words: {metadata['word_count']}\n")
            f.write("=" * 60 + "\n\n")

            for section in sections:
                f.write(f"\n--- Section {section['section']}: {section['title']} ---\n\n")
                f.write(section["text"])
                f.write("\n")

        result["output_files"].append(str(txt_path))
        result["text_output"] = open(txt_path, "r", encoding="utf-8").read()

    # Save JSON output
    if output_format in ("json", "both"):
        import json
        json_path = output_dir / f"{base_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        result["output_files"].append(str(json_path))

    return result


def extract_markdown_from_data(
    data: bytes,
    filename: str,
    output_format: str = "txt"
) -> dict:
    """Extract content from Markdown data (for API use)."""
    content = data.decode("utf-8")
    file_hash = compute_data_hash(data)

    # Extract frontmatter and body
    frontmatter, body = extract_frontmatter(content)
    metadata = extract_metadata_from_frontmatter(frontmatter, filename)

    # Extract TOC from headings
    toc = extract_headings(body)

    # Estimate pages
    estimated_pages = estimate_pages(body)
    metadata["page_count"] = estimated_pages
    metadata["word_count"] = len(body.split())
    metadata["char_count"] = len(body)

    # Split into sections
    sections = split_into_sections(body, toc)

    result = {
        "source_file": filename,
        "file_type": "markdown",
        "extraction_date": datetime.now().isoformat(),
        "file_hash": file_hash,
        "metadata": metadata,
        "frontmatter": frontmatter,
        "toc": toc,
        "sections": sections,
    }

    # Generate text output
    if output_format in ("txt", "both"):
        lines = [
            f"# {metadata.get('title', filename)}",
        ]
        if metadata.get("author"):
            author = metadata["author"]
            if isinstance(author, list):
                author = ", ".join(author)
            lines.append(f"# Author: {author}")
        lines.append(f"# Source: {filename}")
        lines.append(f"# Words: {metadata['word_count']}")
        lines.append("=" * 60)
        lines.append("")

        for section in sections:
            lines.append(f"\n--- Section {section['section']}: {section['title']} ---\n")
            lines.append(section["text"])

        result["text_output"] = "\n".join(lines)

    return result
