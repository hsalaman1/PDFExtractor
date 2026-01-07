# PDFExtractor Local Setup Plan

## Overview

This plan provides step-by-step instructions to set up and run the PDFExtractor application locally on your computer. The application supports extracting text from PDF, Markdown (.md), and Word (.docx) documents through both a web interface and CLI tools.

---

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Node.js | 16.x or higher | `node --version` |
| npm | 8.x or higher | `npm --version` |
| Python | 3.9 or higher | `python3 --version` |
| pip | Latest | `pip3 --version` |
| Git | Any recent | `git --version` |

### System-Specific Requirements

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-dev nodejs npm git gcc make
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install -y python3 python3-pip python3-devel nodejs npm git gcc make
```

**macOS:**
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node python@3.9 git
```

**Windows:**
1. Install Node.js from https://nodejs.org/ (LTS version)
2. Install Python 3.9+ from https://python.org/downloads/
3. Install Git from https://git-scm.com/downloads
4. Ensure "Add to PATH" is checked during installation

---

## Step 1: Clone the Repository

```bash
# Navigate to your preferred directory
cd ~/projects  # or wherever you want to store the project

# Clone the repository
git clone https://github.com/hsalaman1/PDFExtractor.git

# Enter the project directory
cd PDFExtractor
```

---

## Step 2: Install Node.js Dependencies

```bash
# Install all Node.js packages
npm install
```

**Expected Output:**
```
added 30 packages, and audited 31 packages in 5s
found 0 vulnerabilities
```

**Dependencies Installed:**
- next@14.0.4 - React framework
- react@18.2.0 - UI library
- react-dom@18.2.0 - DOM rendering
- TypeScript and type definitions

---

## Step 3: Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed PyMuPDF-1.23.x python-docx-1.1.x pyyaml-6.x
```

**Dependencies Installed:**
- PyMuPDF>=1.23.0 - PDF text extraction
- python-docx>=1.1.0 - Word document parsing
- pyyaml>=6.0 - YAML frontmatter parsing

---

## Step 4: Run the Development Server (Web Interface)

```bash
# Start the Next.js development server
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.0.4
- Local:        http://localhost:3000
- Environments: .env.local

✓ Ready in 2.5s
```

**Access the Web Interface:**
- Open your browser and navigate to: **http://localhost:3000**

---

## Step 5: Using the Web Interface

1. **Upload a Document:**
   - Drag and drop a PDF, Markdown, or Word file onto the upload area
   - Or click "Browse" to select a file

2. **Select Output Format:**
   - **Text**: Human-readable formatted output
   - **JSON**: Structured data with metadata

3. **Extract Content:**
   - Click "Extract Text" button
   - Wait for processing (progress indicator shown)

4. **View Results:**
   - Metadata table displays file information
   - Table of Contents shows document structure
   - Text preview shows first 3000 characters

5. **Download:**
   - Click "Download" to save extracted content

---

## Step 6: Using CLI Tools (Alternative to Web Interface)

### Extract a Single Document

```bash
# Extract PDF to text
python3 pdf_extractor.py document.pdf

# Extract to JSON format
python3 pdf_extractor.py document.pdf --format json

# Extract to both formats
python3 pdf_extractor.py document.pdf --format both

# Extract specific pages (PDF only)
python3 pdf_extractor.py document.pdf --pages 1-5

# Verbose output
python3 pdf_extractor.py document.pdf --verbose
```

### Batch Processing

```bash
# Extract all documents in a folder
python3 pdf_extractor.py --batch ./documents/

# Index a library for searching
python3 pdf_extractor.py --index ./library/
```

### Search Extracted Documents

```bash
# Search for a term
python3 pdf_search.py "search term" ./extracted_files/

# Case-sensitive search
python3 pdf_search.py "SearchTerm" ./extracted_files/ --case-sensitive

# Regex search
python3 pdf_search.py "pattern.*match" ./extracted_files/ --regex

# JSON output
python3 pdf_search.py "term" ./extracted_files/ --json
```

---

## Step 7: Verify Installation

### Test Web Interface

1. Start dev server: `npm run dev`
2. Open http://localhost:3000
3. Upload a test PDF file
4. Verify extraction works and shows metadata

### Test CLI Tools

```bash
# Create a test file
echo "# Test Document

This is a test paragraph." > test.md

# Extract it
python3 pdf_extractor.py test.md --format json

# Check output
cat test.json
```

---

## Project Structure Reference

```
PDFExtractor/
├── api/                    # Vercel serverless functions
│   ├── extract.py         # Main extraction API endpoint
│   ├── requirements.txt   # Python deps for Vercel
│   └── runtime.txt        # Python version (3.9)
├── pages/                  # Next.js pages
│   ├── index.tsx          # Main web UI
│   ├── _app.tsx           # App wrapper
│   └── _document.tsx      # HTML template
├── src/                    # Python extraction modules
│   ├── extractor.py       # PDF extraction
│   ├── markdown_extractor.py
│   ├── docx_extractor.py
│   ├── indexer.py         # Library indexing
│   └── searcher.py        # Search functionality
├── pdf_extractor.py       # Main CLI tool
├── pdf_search.py          # Search CLI tool
├── package.json           # Node.js dependencies
├── requirements.txt       # Python dependencies
└── vercel.json            # Deployment config
```

---

## Common Issues & Solutions

### Issue: `npm install` fails with permission errors

**Solution:**
```bash
# Use npm with correct permissions
npm install --legacy-peer-deps
```

### Issue: PyMuPDF installation fails

**Solution (Linux):**
```bash
sudo apt install python3-dev libmupdf-dev
pip install PyMuPDF --no-cache-dir
```

**Solution (macOS):**
```bash
xcode-select --install
pip install PyMuPDF --no-cache-dir
```

### Issue: Port 3000 already in use

**Solution:**
```bash
# Use a different port
npm run dev -- -p 3001
```

### Issue: Python command not found

**Solution:**
```bash
# Use python3 instead of python
python3 pdf_extractor.py document.pdf

# Or create an alias
alias python=python3
```

### Issue: Virtual environment not activating

**Solution (Windows PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

---

## Environment Variables (Optional)

No environment variables are required for local development. The application works out of the box.

For custom configurations, create a `.env.local` file:
```bash
# Optional: Custom port
PORT=3001

# Optional: Enable debug mode
DEBUG=true
```

---

## Available npm Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (hot reload) |
| `npm run build` | Create production build |
| `npm start` | Run production server |
| `npm run lint` | Run ESLint checks |

---

## Supported File Formats

| Format | Extension | Features |
|--------|-----------|----------|
| PDF | .pdf | Full text, metadata, TOC, page-by-page |
| Markdown | .md | YAML frontmatter, headings, sections |
| Word | .docx | Paragraphs, metadata, heading styles |

---

## Output Formats

### Text Output (.txt)
```
# Document Title
# Author: Author Name
# Source: document.pdf
============================================================

--- Page 1 ---
Content here...
```

### JSON Output (.json)
```json
{
  "source_file": "document.pdf",
  "file_type": "pdf",
  "extraction_date": "2026-01-07T12:00:00",
  "file_hash": "sha256:abc123...",
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "page_count": 10
  },
  "toc": [...],
  "pages": [...],
  "text_output": "..."
}
```

---

## Quick Start Summary

```bash
# 1. Clone repository
git clone https://github.com/hsalaman1/PDFExtractor.git
cd PDFExtractor

# 2. Install Node.js dependencies
npm install

# 3. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# 4. Start development server
npm run dev

# 5. Open browser
# Navigate to http://localhost:3000
```

---

## Next Steps After Setup

1. **Test with sample documents** - Try extracting various PDF, MD, and DOCX files
2. **Explore CLI tools** - Use batch processing for multiple files
3. **Build search index** - Index a document library for searching
4. **Customize output** - Modify extraction parameters as needed

---

## Support

If you encounter issues:
1. Check the Common Issues section above
2. Verify all prerequisites are installed correctly
3. Ensure virtual environment is activated for Python commands
4. Check console output for specific error messages

---

*Plan created: 2026-01-07*
*Application: PDFExtractor v1.0.0*
