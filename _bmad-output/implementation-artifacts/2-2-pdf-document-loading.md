# Story 2.2: PDF Document Loading

Status: ready-for-dev

## Story

As a developer,
I want to load PDF files from a local directory,
so that their content is available for chunking and embedding.

## Acceptance Criteria

1. All `.pdf` files in `./data/pdfs/` are loaded as LlamaIndex Document objects
2. Each document's metadata includes `file_name`, `file_path`, and `source_type: "pdf"`
3. A malformed or unreadable PDF is logged as a warning and processing continues
4. Function returns a list of Documents (empty list if no PDFs found)

## Tasks / Subtasks

- [ ] Task 1: Implement PDF loading function (AC: #1, #2, #3, #4)
  - [ ] Add `load_pdf_documents(pdf_dir: str = "./data/pdfs") -> list[Document]` to `src/core/ingestion.py`
  - [ ] Use `SimpleDirectoryReader` with `required_exts=[".pdf"]` and `recursive=False`
  - [ ] Add custom metadata: `source_type: "pdf"` to each document via `file_metadata` callback or post-processing
  - [ ] Wrap in try/except to handle missing directory or read errors gracefully
  - [ ] Return empty list if directory doesn't exist or has no PDFs
- [ ] Task 2: Write tests (AC: #1-#4)
  - [ ] Create `tests/test_ingestion.py`
  - [ ] Test: loads PDFs from directory (use a small test PDF or mock)
  - [ ] Test: metadata includes file_name, file_path, source_type
  - [ ] Test: returns empty list when directory is empty
  - [ ] Test: returns empty list when directory doesn't exist
  - [ ] Test: continues on malformed file (mock SimpleDirectoryReader raising per-file)

## Dev Notes

### Implementation Pattern

```python
from llama_index.core import SimpleDirectoryReader, Document

def load_pdf_documents(pdf_dir: str = "./data/pdfs") -> list[Document]:
    ...
```

SimpleDirectoryReader automatically extracts: `file_path`, `file_name`, `file_type`, `file_size`, `creation_date`, `last_modified_date`. We just need to add `source_type: "pdf"`.

### Anti-Patterns to Avoid

- Do NOT use PyMuPDF (AGPL license) — stick with default pypdf reader (MIT)
- Do NOT process URLs here — that's Story 2.3
- Do NOT chunk or embed here — that's Story 2.4

### References

- [Source: architecture.md#Project Structure & Boundaries → src/core/ingestion.py]
- [Source: technical research → Integration Pattern 2: Document Loading]
- [Source: prd.md#FR1, FR7, FR8]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

### Change Log
