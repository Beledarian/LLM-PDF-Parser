# PDF Parser MCP Server

A Model Context Protocol (MCP) server that extracts text from PDF files, with optional OCR support for scanned documents.

## Features

- **Text extraction** from PDF files using `pypdf`
- **Word Document support** - read `.docx` files with formatting (headers, tables)
- **OCR support** via Tesseract for scanned/image-based PDFs and DOCX images
- **URL support** - read documents directly from HTTP/HTTPS URLs
- **Page selection** - extract specific pages or ranges (PDF only)
- **Password protection** - decrypt protected PDFs

## Prerequisites

**For OCR support** (highly recommended), install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki):
- **Windows:** Download from UB-Mannheim or run `choco install tesseract`
- Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

## Installation & Setup

### Option 1: Automatic (Windows)
No manual setup required. The included `start_server.bat` script will automatically create a virtual environment and install all dependencies the first time you run it.

### Option 2: Manual (Mac/Linux/Custom)
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Configuration

### 1. Gemini CLI

**Method A: Using Batch Script (Recommended for Windows)**
```bash
gemini mcp add pdf-parser "C:\Path\To\LLM-PDF-Parser\start_server.bat"
```

**Method B: Using Python Directly**
```bash
gemini mcp add pdf-parser "python" --args "C:\Path\To\LLM-PDF-Parser\server.py"
```

### 2. Claude Desktop & Other MCP Clients

Add the following to your MCP configuration file (e.g., `claude_desktop_config.json` or VS Code settings).

**Method A: Using Batch Script (Recommended for Windows)**
Ensures dependencies are managed automatically.
```json
{
  "mcpServers": {
    "pdf-parser": {
      "command": "C:\\Path\\To\\LLM-PDF-Parser\\start_server.bat",
      "args": [],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

**Method B: Using Python Directly**
Requires you to handle the virtual environment and dependencies manually.
```json
{
  "mcpServers": {
    "pdf-parser": {
      "command": "python",
      "args": ["C:\\Path\\To\\LLM-PDF-Parser\\server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Tool: `read_pdf`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to PDF or URL (http/https) |
| `pages` | string | No | Page selection: `"0,1,5"` or `"0-5"` (0-indexed) |
| `password` | string | No | Password for encrypted PDFs |
| `ocr` | boolean | No | Enable Tesseract OCR for images (default: true) |

### Tool: `read_docx`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Absolute path to DOCX or URL (http/https) |
| `ocr` | boolean | No | Enable Tesseract OCR for embedded images (default: true) |

### Examples

```python
# Read entire PDF
read_pdf("C:/docs/report.pdf")

# Read specific pages from PDF
read_pdf("C:/docs/report.pdf", pages="0,2-5")

# Read DOCX file (preserves headers and tables)
read_docx("C:/docs/notes.docx")

# Read from URL
read_pdf("https://example.com/document.pdf")
read_docx("https://example.com/meeting.docx")

# Disable OCR (enabled by default)
read_pdf("C:/docs/scanned.pdf", ocr=False)

# Decrypt protected PDF
read_pdf("C:/docs/protected.pdf", password="secret")
```

## Requirements

- Python 3.10+
- `pypdf` - PDF text extraction
- `python-docx` - Word document extraction
- `pytesseract` - OCR wrapper (optional)
- `Pillow` - Image processing (optional)
- `requests` - URL downloads
- `mcp` - MCP server framework

## Notes

- Uses pure Python `pypdf` instead of `pymupdf` for ARM64 compatibility
- OCR requires Tesseract to be installed on the system
- Page numbers are 0-indexed in the `pages` parameter
