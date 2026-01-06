#!/usr/bin/env python3
"""
PDFExtractor - Extract text, metadata, and TOC from PDF documents.

Usage:
    python pdf_extractor.py input.pdf [options]
    python pdf_extractor.py --batch folder/ [options]
    python pdf_extractor.py --index library/
"""

import argparse
import sys
from pathlib import Path


def parse_page_range(page_range: str, total_pages: int) -> list[int]:
    """Parse page range specification into list of page numbers."""
    pages = []

    for part in page_range.split(","):
        part = part.strip()
        if "-" in part:
            if part.startswith("-"):
                # -50 means first 50 pages
                end = int(part[1:])
                pages.extend(range(1, min(end + 1, total_pages + 1)))
            elif part.endswith("-"):
                # 10- means page 10 to end
                start = int(part[:-1])
                pages.extend(range(start, total_pages + 1))
            else:
                # 10-50 means pages 10 through 50
                start, end = map(int, part.split("-"))
                pages.extend(range(start, min(end + 1, total_pages + 1)))
        else:
            # Single page number
            pages.append(int(part))

    return sorted(set(pages))


def extract_single(args) -> bool:
    """Extract a single PDF file."""
    from src.extractor import extract_pdf

    try:
        output_format = args.format
        if args.json:
            output_format = "json"

        result = extract_pdf(
            pdf_path=args.input,
            output_dir=args.output,
            output_format=output_format,
            include_metadata=not args.no_metadata,
            include_toc=not args.no_toc,
        )

        if args.verbose:
            meta = result["metadata"]
            print(f"Extracted: {result['source_file']}")
            print(f"  Title: {meta.get('title', 'N/A')}")
            print(f"  Author: {meta.get('author', 'N/A')}")
            print(f"  Pages: {meta.get('page_count', 'N/A')}")
            print(f"  TOC entries: {len(result.get('toc', []))}")
            print(f"  Output files:")
            for f in result["output_files"]:
                print(f"    - {f}")
        else:
            print(f"Extracted: {result['source_file']} -> {len(result['output_files'])} files")

        return True

    except Exception as e:
        print(f"Error extracting {args.input}: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def extract_batch(args) -> bool:
    """Extract multiple PDF files from a directory."""
    from src.extractor import extract_pdf

    batch_path = Path(args.batch)
    if not batch_path.exists():
        print(f"Error: Batch path not found: {batch_path}", file=sys.stderr)
        return False

    # Get list of PDFs
    if batch_path.is_file():
        # Text file with list of paths
        with open(batch_path, "r") as f:
            pdf_files = [Path(line.strip()) for line in f if line.strip()]
    else:
        # Directory
        pdf_files = list(batch_path.rglob("*.pdf"))

    if not pdf_files:
        print("No PDF files found to process.")
        return True

    output_dir = Path(args.batch_output) if args.batch_output else None

    print(f"Processing {len(pdf_files)} PDF files...")

    success_count = 0
    fail_count = 0
    errors = []

    output_format = args.format
    if args.json:
        output_format = "json"

    for i, pdf_path in enumerate(pdf_files, 1):
        progress = f"[{i}/{len(pdf_files)}]"

        try:
            # Determine output directory for this file
            if output_dir:
                file_output = output_dir
            else:
                file_output = pdf_path.parent

            result = extract_pdf(
                pdf_path=pdf_path,
                output_dir=file_output,
                output_format=output_format,
                include_metadata=not args.no_metadata,
                include_toc=not args.no_toc,
            )

            print(f"{progress} ✓ {pdf_path.name}")
            success_count += 1

        except Exception as e:
            print(f"{progress} ✗ {pdf_path.name}: {e}")
            errors.append((pdf_path, str(e)))
            fail_count += 1

            if not args.continue_on_error:
                print("Stopping due to error. Use --continue-on-error to process remaining files.")
                break

    print()
    print(f"Completed: {success_count} files")
    if fail_count:
        print(f"Failed: {fail_count} files")

        # Write error log
        if output_dir:
            error_log = output_dir / "error_log.txt"
        else:
            error_log = Path("error_log.txt")

        with open(error_log, "w") as f:
            for pdf_path, error in errors:
                f.write(f"{pdf_path}: {error}\n")
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
        description="Extract text, metadata, and TOC from PDF documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                     Extract single PDF
  %(prog)s document.pdf -o ./output/        Extract to specific directory
  %(prog)s document.pdf --format json       Output as JSON
  %(prog)s --batch library/ --continue-on-error   Process all PDFs in folder
  %(prog)s --index library/                 Build searchable index
        """
    )

    # Input options
    parser.add_argument("input", nargs="?", help="Input PDF file to extract")

    # Batch processing
    parser.add_argument("--batch", metavar="PATH",
                        help="Process all PDFs in folder or from file list")
    parser.add_argument("--batch-output", metavar="DIR",
                        help="Output directory for batch processing")
    parser.add_argument("--continue-on-error", action="store_true",
                        help="Continue processing if one PDF fails")

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

    # Page selection
    parser.add_argument("--page-range", metavar="RANGE",
                        help="Extract specific pages (e.g., 10-50, 10,20,30)")

    # Other options
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")
    parser.add_argument("--version", action="version", version="PDFExtractor 1.0.0")

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
