#!/usr/bin/env python3
"""
DocExtractor - Extract text, metadata, and TOC from documents.

Supported formats: PDF, Markdown (.md), Word (.docx)

Usage:
    python pdf_extractor.py input.pdf [options]
    python pdf_extractor.py document.docx [options]
    python pdf_extractor.py readme.md [options]
    python pdf_extractor.py --batch folder/ [options]
    python pdf_extractor.py --index library/
"""

import argparse
import sys
from pathlib import Path

# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".docx"}


def get_file_type(file_path: Path) -> str:
    """Determine file type from extension."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in (".md", ".markdown"):
        return "markdown"
    elif ext == ".docx":
        return "docx"
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_file(file_path: Path, output_dir, output_format: str, include_metadata: bool, include_toc: bool) -> dict:
    """Extract content from a file based on its type."""
    file_type = get_file_type(file_path)

    if file_type == "pdf":
        from src.extractor import extract_pdf
        return extract_pdf(
            pdf_path=file_path,
            output_dir=output_dir,
            output_format=output_format,
            include_metadata=include_metadata,
            include_toc=include_toc,
        )
    elif file_type == "markdown":
        from src.markdown_extractor import extract_markdown
        return extract_markdown(
            md_path=file_path,
            output_dir=output_dir,
            output_format=output_format,
        )
    elif file_type == "docx":
        from src.docx_extractor import extract_docx
        return extract_docx(
            docx_path=file_path,
            output_dir=output_dir,
            output_format=output_format,
        )


def parse_page_range(page_range: str, total_pages: int) -> list[int]:
    """Parse page range specification into list of page numbers."""
    pages = []

    for part in page_range.split(","):
        part = part.strip()
        if "-" in part:
            if part.startswith("-"):
                end = int(part[1:])
                pages.extend(range(1, min(end + 1, total_pages + 1)))
            elif part.endswith("-"):
                start = int(part[:-1])
                pages.extend(range(start, total_pages + 1))
            else:
                start, end = map(int, part.split("-"))
                pages.extend(range(start, min(end + 1, total_pages + 1)))
        else:
            pages.append(int(part))

    return sorted(set(pages))


def extract_single(args) -> bool:
    """Extract a single file."""
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return False

    try:
        get_file_type(input_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    try:
        output_format = args.format
        if args.json:
            output_format = "json"

        result = extract_file(
            file_path=input_path,
            output_dir=args.output,
            output_format=output_format,
            include_metadata=not args.no_metadata,
            include_toc=not args.no_toc,
        )

        if args.verbose:
            meta = result["metadata"]
            file_type = result.get("file_type", "pdf")
            print(f"Extracted: {result['source_file']} ({file_type})")
            print(f"  Title: {meta.get('title', 'N/A')}")
            print(f"  Author: {meta.get('author', 'N/A')}")
            if "page_count" in meta:
                print(f"  Pages: {meta.get('page_count', 'N/A')}")
            if "word_count" in meta:
                print(f"  Words: {meta.get('word_count', 'N/A')}")
            print(f"  TOC entries: {len(result.get('toc', []))}")
            print(f"  Output files:")
            for f in result.get("output_files", []):
                print(f"    - {f}")
        else:
            output_count = len(result.get("output_files", []))
            print(f"Extracted: {result['source_file']} -> {output_count} files")

        return True

    except Exception as e:
        print(f"Error extracting {args.input}: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def extract_batch(args) -> bool:
    """Extract multiple files from a directory."""
    batch_path = Path(args.batch)
    if not batch_path.exists():
        print(f"Error: Batch path not found: {batch_path}", file=sys.stderr)
        return False

    # Get list of supported files
    if batch_path.is_file():
        with open(batch_path, "r") as f:
            files = [Path(line.strip()) for line in f if line.strip()]
    else:
        files = []
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(batch_path.rglob(f"*{ext}"))

    if not files:
        print("No supported files found to process.")
        print(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        return True

    output_dir = Path(args.batch_output) if args.batch_output else None

    print(f"Processing {len(files)} files...")

    success_count = 0
    fail_count = 0
    errors = []

    output_format = args.format
    if args.json:
        output_format = "json"

    for i, file_path in enumerate(files, 1):
        progress = f"[{i}/{len(files)}]"

        try:
            file_output = output_dir if output_dir else file_path.parent

            result = extract_file(
                file_path=file_path,
                output_dir=file_output,
                output_format=output_format,
                include_metadata=not args.no_metadata,
                include_toc=not args.no_toc,
            )

            file_type = result.get("file_type", "pdf")
            print(f"{progress} ✓ {file_path.name} ({file_type})")
            success_count += 1

        except Exception as e:
            print(f"{progress} ✗ {file_path.name}: {e}")
            errors.append((file_path, str(e)))
            fail_count += 1

            if not args.continue_on_error:
                print("Stopping due to error. Use --continue-on-error to process remaining files.")
                break

    print()
    print(f"Completed: {success_count} files")
    if fail_count:
        print(f"Failed: {fail_count} files")

        error_log = (output_dir or Path(".")) / "error_log.txt"
        with open(error_log, "w") as f:
            for file_path, error in errors:
                f.write(f"{file_path}: {error}\n")
        print(f"Error log saved to: {error_log}")

    return fail_count == 0


def build_index(args) -> bool:
    """Build a library index."""
    from src.indexer import build_index, get_catalog

    try:
        index = build_index(
            library_path=args.index,
            force_reindex=args.force,
        )

        if args.verbose:
            print(get_catalog(Path(args.index) / "library_index.json"))
        else:
            print(f"Indexed {index['total_documents']} documents ({index['extracted_count']} extracted)")
            print(f"Index saved to: {Path(args.index) / 'library_index.json'}")

        return True

    except Exception as e:
        print(f"Error building index: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Extract text, metadata, and TOC from documents (PDF, Markdown, Word).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported formats:
  - PDF (.pdf)
  - Markdown (.md, .markdown)
  - Word (.docx)

Examples:
  %(prog)s document.pdf                     Extract single PDF
  %(prog)s readme.md -o ./output/           Extract Markdown file
  %(prog)s report.docx --format json        Extract Word document as JSON
  %(prog)s --batch library/ --continue-on-error   Process all files in folder
  %(prog)s --index library/                 Build searchable index
        """
    )

    # Input options
    parser.add_argument("input", nargs="?", help="Input file to extract (PDF, Markdown, or Word)")

    # Batch processing
    parser.add_argument("--batch", metavar="PATH",
                        help="Process all supported files in folder or from file list")
    parser.add_argument("--batch-output", metavar="DIR",
                        help="Output directory for batch processing")
    parser.add_argument("--continue-on-error", action="store_true",
                        help="Continue processing if one file fails")

    # Indexing
    parser.add_argument("--index", metavar="PATH",
                        help="Build index for library at PATH")
    parser.add_argument("--force", action="store_true",
                        help="Force re-indexing of all files")

    # Output options
    parser.add_argument("-o", "--output", metavar="DIR",
                        help="Output directory (default: same as input)")
    parser.add_argument("-f", "--format", choices=["txt", "json", "both"],
                        default="txt", help="Output format (default: txt)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON (shortcut for --format json)")
    parser.add_argument("--no-metadata", action="store_true",
                        help="Don't extract metadata")
    parser.add_argument("--no-toc", action="store_true",
                        help="Don't extract table of contents")

    # Page selection (PDF only)
    parser.add_argument("--page-range", metavar="RANGE",
                        help="Extract specific pages (PDF only, e.g., 10-50)")

    # Other options
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("--version", action="version", version="DocExtractor 1.1.0")

    args = parser.parse_args()

    # Determine operation mode
    if args.index:
        success = build_index(args)
    elif args.batch:
        success = extract_batch(args)
    elif args.input:
        success = extract_single(args)
    else:
        parser.print_help()
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
