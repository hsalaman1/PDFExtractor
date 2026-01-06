"""Search functionality for extracted PDF content."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SearchResult:
    """A single search match."""
    file_path: str
    title: str
    page: int
    context: str
    match_start: int
    match_end: int


def search_file(
    file_path: Path,
    pattern: str,
    is_regex: bool = False,
    case_sensitive: bool = False,
    context_chars: int = 80,
) -> list[SearchResult]:
    """
    Search a single text file for matches.

    Args:
        file_path: Path to text file
        pattern: Search pattern (string or regex)
        is_regex: Whether pattern is a regex
        case_sensitive: Whether search is case-sensitive
        context_chars: Number of characters of context around match

    Returns:
        List of SearchResult objects
    """
    results = []

    if not file_path.exists():
        return results

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Build regex pattern
    flags = 0 if case_sensitive else re.IGNORECASE
    if is_regex:
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    else:
        # Escape special characters for literal search
        regex = re.compile(re.escape(pattern), flags)

    # Find page markers and build page map
    page_pattern = re.compile(r"--- Page (\d+) ---")
    page_positions = [(0, 1)]  # Default to page 1
    for match in page_pattern.finditer(content):
        page_positions.append((match.end(), int(match.group(1))))

    def get_page_for_position(pos: int) -> int:
        """Get page number for a character position."""
        page = 1
        for start_pos, page_num in page_positions:
            if pos >= start_pos:
                page = page_num
            else:
                break
        return page

    # Extract title from first line
    title = file_path.stem
    first_line = content.split("\n")[0] if content else ""
    if first_line.startswith("# "):
        title = first_line[2:].strip()

    # Find all matches
    for match in regex.finditer(content):
        start = match.start()
        end = match.end()

        # Extract context
        ctx_start = max(0, start - context_chars)
        ctx_end = min(len(content), end + context_chars)

        # Expand to word boundaries
        while ctx_start > 0 and content[ctx_start - 1] not in " \n\t":
            ctx_start -= 1
        while ctx_end < len(content) and content[ctx_end] not in " \n\t":
            ctx_end += 1

        context = content[ctx_start:ctx_end].strip()
        context = " ".join(context.split())  # Normalize whitespace

        # Add ellipsis if truncated
        if ctx_start > 0:
            context = "..." + context
        if ctx_end < len(content):
            context = context + "..."

        results.append(SearchResult(
            file_path=str(file_path),
            title=title,
            page=get_page_for_position(start),
            context=context,
            match_start=start - ctx_start + (3 if ctx_start > 0 else 0),
            match_end=end - ctx_start + (3 if ctx_start > 0 else 0),
        ))

    return results


def search_library(
    library_path: str | Path,
    pattern: str,
    is_regex: bool = False,
    case_sensitive: bool = False,
    context_chars: int = 80,
    max_results_per_file: Optional[int] = None,
    index_path: Optional[str | Path] = None,
) -> dict:
    """
    Search across all extracted text files in a library.

    Args:
        library_path: Path to library directory
        pattern: Search pattern
        is_regex: Whether pattern is a regex
        case_sensitive: Whether search is case-sensitive
        context_chars: Characters of context around matches
        max_results_per_file: Limit results per file (None = unlimited)
        index_path: Optional path to library index for metadata

    Returns:
        Dictionary with search results grouped by file
    """
    library_path = Path(library_path)
    if not library_path.exists():
        raise FileNotFoundError(f"Library path not found: {library_path}")

    # Load index if available for metadata
    index = None
    if index_path:
        index_path = Path(index_path)
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
    else:
        default_index = library_path / "library_index.json"
        if default_index.exists():
            with open(default_index, "r", encoding="utf-8") as f:
                index = json.load(f)

    # Find all text files
    text_files = list(library_path.rglob("*.txt"))

    # Filter out TOC files
    text_files = [f for f in text_files if not f.name.endswith("_toc.txt")]

    results_by_file = {}
    total_matches = 0

    for txt_path in text_files:
        results = search_file(
            txt_path,
            pattern,
            is_regex=is_regex,
            case_sensitive=case_sensitive,
            context_chars=context_chars,
        )

        if not results:
            continue

        if max_results_per_file and len(results) > max_results_per_file:
            results = results[:max_results_per_file]

        # Get PDF path and metadata
        pdf_path = txt_path.with_suffix(".pdf")
        file_key = str(pdf_path.relative_to(library_path)) if pdf_path.exists() else txt_path.stem

        # Get title from index or results
        title = results[0].title if results else txt_path.stem
        if index and file_key in index.get("documents", {}):
            doc = index["documents"][file_key]
            title = doc.get("metadata", {}).get("title", title)

        results_by_file[file_key] = {
            "title": title,
            "file_path": str(txt_path),
            "pdf_path": str(pdf_path) if pdf_path.exists() else None,
            "match_count": len(results),
            "matches": [
                {
                    "page": r.page,
                    "context": r.context,
                }
                for r in results
            ],
        }
        total_matches += len(results)

    return {
        "pattern": pattern,
        "is_regex": is_regex,
        "case_sensitive": case_sensitive,
        "files_searched": len(text_files),
        "files_with_matches": len(results_by_file),
        "total_matches": total_matches,
        "results": results_by_file,
    }


def format_search_results(results: dict) -> str:
    """Format search results for display."""
    lines = []

    if results["total_matches"] == 0:
        return f'No matches found for "{results["pattern"]}"'

    lines.append(f'Found "{results["pattern"]}" in {results["files_with_matches"]} books:')
    lines.append("")

    for i, (file_key, file_results) in enumerate(results["results"].items(), 1):
        title = file_results["title"]
        pdf_name = Path(file_key).name if file_results["pdf_path"] else file_key

        lines.append(f"{i}. {title} ({pdf_name})")

        for match in file_results["matches"]:
            lines.append(f"   - Page {match['page']}: \"{match['context']}\"")

        lines.append("")

    return "\n".join(lines)
