"""Library indexing module for PDF documents."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .extractor import extract_pdf, compute_file_hash


def build_index(
    library_path: str | Path,
    index_path: Optional[str | Path] = None,
    force_reindex: bool = False,
) -> dict:
    """
    Build a searchable index of all PDFs in a library.

    Args:
        library_path: Path to directory containing PDFs or extracted files
        index_path: Path to save the index file (default: library_path/index.json)
        force_reindex: Re-extract and index even if already indexed

    Returns:
        Dictionary containing the library index
    """
    library_path = Path(library_path)
    if not library_path.exists():
        raise FileNotFoundError(f"Library path not found: {library_path}")

    if index_path is None:
        index_path = library_path / "library_index.json"
    index_path = Path(index_path)

    # Load existing index if available
    existing_index = {}
    if index_path.exists() and not force_reindex:
        with open(index_path, "r", encoding="utf-8") as f:
            existing_index = json.load(f)

    # Find all PDF and JSON files
    pdf_files = list(library_path.rglob("*.pdf"))
    json_files = list(library_path.rglob("*.json"))

    # Build document entries
    documents = existing_index.get("documents", {})

    for pdf_path in pdf_files:
        file_key = str(pdf_path.relative_to(library_path))
        file_hash = compute_file_hash(pdf_path)

        # Skip if already indexed with same hash
        if file_key in documents and documents[file_key].get("file_hash") == file_hash:
            if not force_reindex:
                continue

        # Check for existing extracted JSON
        json_path = pdf_path.with_suffix(".json")
        meta_path = pdf_path.parent / f"{pdf_path.stem}_metadata.json"

        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            documents[file_key] = {
                "file_path": str(pdf_path.absolute()),
                "file_hash": file_hash,
                "metadata": meta.get("metadata", {}),
                "toc": meta.get("toc", []),
                "extracted": True,
                "text_file": str(pdf_path.with_suffix(".txt")),
                "indexed_date": datetime.now().isoformat(),
            }
        elif json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            documents[file_key] = {
                "file_path": str(pdf_path.absolute()),
                "file_hash": file_hash,
                "metadata": data.get("metadata", {}),
                "toc": data.get("toc", []),
                "extracted": True,
                "text_file": str(pdf_path.with_suffix(".txt")),
                "indexed_date": datetime.now().isoformat(),
            }
        else:
            # PDF exists but not extracted yet
            documents[file_key] = {
                "file_path": str(pdf_path.absolute()),
                "file_hash": file_hash,
                "metadata": {"title": pdf_path.stem},
                "toc": [],
                "extracted": False,
                "text_file": None,
                "indexed_date": datetime.now().isoformat(),
            }

    # Build the index
    index = {
        "library_path": str(library_path.absolute()),
        "created_date": existing_index.get("created_date", datetime.now().isoformat()),
        "updated_date": datetime.now().isoformat(),
        "total_documents": len(documents),
        "extracted_count": sum(1 for d in documents.values() if d.get("extracted")),
        "documents": documents,
    }

    # Save index
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return index


def get_catalog(index_path: str | Path) -> str:
    """Generate a human-readable catalog from the index."""
    index_path = Path(index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found: {index_path}")

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    lines = [
        "=" * 70,
        "LIBRARY CATALOG",
        "=" * 70,
        f"Library: {index['library_path']}",
        f"Total Documents: {index['total_documents']}",
        f"Extracted: {index['extracted_count']}",
        f"Last Updated: {index['updated_date']}",
        "=" * 70,
        "",
    ]

    for i, (key, doc) in enumerate(index["documents"].items(), 1):
        meta = doc.get("metadata", {})
        title = meta.get("title", key)
        author = meta.get("author", "Unknown")
        pages = meta.get("page_count", "?")
        status = "✓" if doc.get("extracted") else "○"

        lines.append(f"{i:3}. [{status}] {title}")
        lines.append(f"      Author: {author} | Pages: {pages}")
        lines.append(f"      File: {key}")
        lines.append("")

    return "\n".join(lines)
