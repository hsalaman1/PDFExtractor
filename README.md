# PDFExtractor

A Python tool for extracting text, metadata, and table of contents from PDF documents, with built-in search and library indexing capabilities.

## Features

- **Text Extraction**: Extract text from PDF files with page markers
- **Metadata Extraction**: Extract title, author, subject, keywords, and more
- **TOC Extraction**: Extract bookmarks/table of contents with page mappings
- **Batch Processing**: Process entire folders of PDFs at once
- **Library Indexing**: Create a searchable catalog of your document library
- **Full-Text Search**: Search across all extracted documents with context

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PDFExtractor

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Extract a Single PDF

```bash
python pdf_extractor.py document.pdf
```

This creates:
- `document.txt` - Extracted text with page markers
- `document_metadata.json` - Document metadata
- `document_toc.txt` - Table of contents (if available)

### Extract to JSON Format

```bash
python pdf_extractor.py document.pdf --format json
```

### Batch Process a Folder

```bash
python pdf_extractor.py --batch my_library/ --batch-output extracted/
```

### Build a Library Index

```bash
python pdf_extractor.py --index my_library/
```

### Search Your Library

```bash
python pdf_search.py "behavioral conditioning" my_library/
```

Output:
```
Found "behavioral conditioning" in 3 books:

1. Introduction to Behavioral Analysis (introduction_to_behavioral_analysis.pdf)
   - Page 45: "...the principles of behavioral conditioning were first..."
   - Page 127: "...modern behavioral conditioning techniques have evolved..."

2. Psychology Fundamentals (psychology_fundamentals.pdf)
   - Page 203: "...behavioral conditioning in clinical settings..."
```

## Usage

### pdf_extractor.py

```
Usage: pdf_extractor.py [OPTIONS] [INPUT]

Options:
  INPUT                     Input PDF file to extract
  --batch PATH              Process all PDFs in folder or from file list
  --batch-output DIR        Output directory for batch processing
  --continue-on-error       Continue processing if one PDF fails
  --index PATH              Build index for library at PATH
  --force                   Force re-indexing of all files
  -o, --output DIR          Output directory (default: same as input)
  -f, --format {txt,json,both}  Output format (default: txt)
  --json                    Output as JSON
  --no-metadata             Don't extract metadata
  --no-toc                  Don't extract table of contents
  --page-range RANGE        Extract specific pages (e.g., 10-50)
  -v, --verbose             Verbose output
```

### pdf_search.py

```
Usage: pdf_search.py [OPTIONS] PATTERN LIBRARY

Arguments:
  PATTERN                   Search pattern (text or regex)
  LIBRARY                   Path to library directory

Options:
  -r, --regex               Treat pattern as regular expression
  -c, --case-sensitive      Case-sensitive search
  --context N               Characters of context around matches (default: 80)
  --max-results N           Maximum results per file
  --json                    Output results as JSON
  -v, --verbose             Verbose output
```

## Output Formats

### Text Output (.txt)

```
# Document Title
# Author: Author Name
# Source: document.pdf
# Pages: 150
============================================================

--- Page 1 ---

Content of page 1...

--- Page 2 ---

Content of page 2...
```

### JSON Output (.json)

```json
{
  "source_file": "document.pdf",
  "extraction_date": "2025-01-06T14:30:00",
  "file_hash": "sha256:abc123...",
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "page_count": 150
  },
  "toc": [
    {"level": 1, "title": "Chapter 1", "page": 1}
  ],
  "pages": [
    {"page": 1, "text": "Content..."}
  ]
}
```

## Common Workflows

### Build a Searchable Library

```bash
# 1. Extract all PDFs
python pdf_extractor.py --batch books/ --format both --batch-output library/

# 2. Build the index
python pdf_extractor.py --index library/

# 3. Search
python pdf_search.py "search term" library/
```

### Extract Specific Chapters

```bash
python pdf_extractor.py textbook.pdf --page-range 45-120 -o chapter3/
```

## Project Structure

```
PDFExtractor/
├── pdf_extractor.py      # Main extraction CLI
├── pdf_search.py         # Search CLI
├── requirements.txt      # Python dependencies
├── src/
│   ├── __init__.py
│   ├── extractor.py      # PDF extraction module
│   ├── indexer.py        # Library indexing module
│   └── searcher.py       # Search module
└── README.md
```

## License

MIT License
