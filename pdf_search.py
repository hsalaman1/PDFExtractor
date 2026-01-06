#!/usr/bin/env python3
"""
PDF Search - Search across extracted PDF text files.

Usage:
    python pdf_search.py "keyword" library/
    python pdf_search.py --regex "pattern.*match" library/
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Search across extracted PDF text files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "behavioral conditioning" library/
  %(prog)s --regex "behavio[u]?r" library/
  %(prog)s "keyword" library/ --json
  %(prog)s "keyword" library/ --max-results 5
        """
    )

    parser.add_argument("pattern", help="Search pattern (text or regex)")
    parser.add_argument("library", help="Path to library directory")

    parser.add_argument("-r", "--regex", action="store_true",
                        help="Treat pattern as regular expression")
    parser.add_argument("-c", "--case-sensitive", action="store_true",
                        help="Case-sensitive search")
    parser.add_argument("--context", type=int, default=80,
                        help="Characters of context around matches (default: 80)")
    parser.add_argument("--max-results", type=int, metavar="N",
                        help="Maximum results per file")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Import here to avoid slow startup for --help
    from src.searcher import search_library, format_search_results

    try:
        results = search_library(
            library_path=args.library,
            pattern=args.pattern,
            is_regex=args.regex,
            case_sensitive=args.case_sensitive,
            context_chars=args.context,
            max_results_per_file=args.max_results,
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(format_search_results(results))

            if args.verbose:
                print(f"\nSearched {results['files_searched']} files")

        return 0 if results["total_matches"] > 0 else 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
