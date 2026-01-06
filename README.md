# Document Extractor

A web application and CLI tool for extracting text, metadata, and table of contents from documents, with built-in search and library indexing capabilities.

**Supported Formats:** PDF, Markdown (.md), Word (.docx)

**Live Demo**: Deploy your own instance on Vercel in minutes!

## Features

- **Multi-Format Support**: Extract from PDF, Markdown, and Word documents
- **Text Extraction**: Extract text with page/section markers
- **Metadata Extraction**: Extract title, author, subject, keywords, and more
- **TOC Extraction**: Extract bookmarks/headings as table of contents
- **Batch Processing**: Process entire folders of documents at once
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

### Extract Documents

```bash
# Extract a PDF
python pdf_extractor.py document.pdf

# Extract a Markdown file
python pdf_extractor.py readme.md

# Extract a Word document
python pdf_extractor.py report.docx
```

This creates:
- `document.txt` - Extracted text with page/section markers
- `document_metadata.json` - Document metadata
- `document_toc.txt` - Table of contents (if available)

### Extract to JSON Format

```bash
python pdf_extractor.py document.pdf --format json
```

### Batch Process a Folder

Process all supported documents (PDF, Markdown, Word) in a folder:

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

Supported formats: PDF (.pdf), Markdown (.md), Word (.docx)

Options:
  INPUT                     Input file to extract
  --batch PATH              Process all supported files in folder
  --batch-output DIR        Output directory for batch processing
  --continue-on-error       Continue processing if one file fails
  --index PATH              Build index for library at PATH
  --force                   Force re-indexing of all files
  -o, --output DIR          Output directory (default: same as input)
  -f, --format {txt,json,both}  Output format (default: txt)
  --json                    Output as JSON
  --no-metadata             Don't extract metadata
  --no-toc                  Don't extract table of contents
  --page-range RANGE        Extract specific pages (PDF only)
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

## Format-Specific Features

### PDF Documents
- Page-by-page text extraction
- PDF bookmarks as TOC
- Full metadata (author, creator, dates)

### Markdown Files
- YAML frontmatter parsing (title, author, tags)
- Headings extracted as TOC
- Section-based organization

### Word Documents (.docx)
- Paragraph-based extraction
- Heading styles as TOC
- Core properties metadata

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
  "file_type": "pdf",
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
# 1. Extract all documents (PDF, Markdown, Word)
python pdf_extractor.py --batch books/ --format both --batch-output library/

# 2. Build the index
python pdf_extractor.py --index library/

# 3. Search
python pdf_search.py "search term" library/
```

### Extract Specific Chapters (PDF only)

```bash
python pdf_extractor.py textbook.pdf --page-range 45-120 -o chapter3/
```

## Deploy to Vercel

### Quick Deploy

1. **Fork or clone this repository** to your GitHub account

2. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub

3. **Click "Add New Project"**

4. **Import your repository**:
   - Select the repository from your GitHub
   - Vercel will auto-detect the Next.js framework

5. **Deploy**:
   - Click "Deploy"
   - Wait for the build to complete (2-3 minutes)

6. **Your app is live!**
   - Vercel provides a URL like `https://doc-extractor-xxx.vercel.app`

### Manual Deployment (CLI)

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# For production deployment
vercel --prod
```

### Environment & Limits

**Vercel Free Tier**:
- 60 second function timeout (configured in vercel.json)
- 50MB max function size
- Works well for documents up to ~20MB

**For larger documents**, consider:
- Vercel Pro plan (longer timeouts)
- Self-hosting on a VPS
- Using the CLI tool locally

## Project Structure

```
PDFExtractor/
├── app/                      # Next.js App Router
│   ├── layout.tsx            # Root layout
│   └── page.tsx              # Main page (upload UI)
├── api/                      # Vercel Serverless Functions
│   ├── extract.py            # Document extraction endpoint
│   └── requirements.txt      # Python dependencies
├── src/                      # CLI modules
│   ├── extractor.py          # PDF extraction module
│   ├── markdown_extractor.py # Markdown extraction module
│   ├── docx_extractor.py     # Word extraction module
│   ├── indexer.py            # Library indexing module
│   └── searcher.py           # Search module
├── pdf_extractor.py          # CLI tool
├── pdf_search.py             # Search CLI
├── vercel.json               # Vercel configuration
├── package.json              # Node.js dependencies
└── README.md
```

## License

MIT License
