# Accessibility Testing Report & Setup

**Project:** Info Retrieval Agent  
**Date:** 2026-04-29  
**Scope:** Gradio Chat UI (`/chat`), Swagger UI (`/docs`)

---

## Summary

This project has two user-facing web pages:
1. **Gradio Chat Interface** at `/chat` — primary user interaction point
2. **FastAPI Swagger UI** at `/docs` — API documentation

Both are third-party generated UIs (Gradio and Swagger), so accessibility is largely determined by those libraries. Our testing strategy is to **audit and document** issues, filing upstream if needed.

---

## Test Setup

### Prerequisites

```bash
# Install test dependencies
uv pip install pytest playwright pytest-playwright

# Install browser binaries
playwright install chromium
```

### Running Tests

```bash
# Start the application first
docker compose up -d

# Wait for startup
sleep 10

# Run accessibility tests
uv run pytest tests/accessibility/test_a11y.py -v --base-url http://localhost:8000

# Or with custom URL
BASE_URL=http://localhost:8000 uv run pytest tests/accessibility/ -v
```

---

## Test Coverage

| Test | Target | What it checks |
|------|--------|----------------|
| `test_chat_page_loads` | `/chat` | Page returns 200 |
| `test_chat_wcag_aa_compliance` | `/chat` | Full WCAG 2.1 AA audit via axe-core |
| `test_chat_keyboard_navigation` | `/chat` | Tab focus reaches interactive elements |
| `test_chat_input_has_label` | `/chat` | Chat textarea has accessible label |
| `test_chat_color_contrast` | `/chat` | Color contrast meets WCAG AA (4.5:1) |
| `test_docs_page_loads` | `/docs` | Page returns 200 |
| `test_docs_wcag_aa_compliance` | `/docs` | Full WCAG 2.1 AA audit |

---

## Known Accessibility Characteristics

### Gradio Chat Interface

Gradio (v4+) provides reasonable baseline accessibility:
- ✅ Semantic HTML structure
- ✅ ARIA labels on interactive components
- ✅ Keyboard-navigable chat input
- ✅ Focus management on new messages
- ⚠️ Some color contrast issues in default theme (known Gradio issue)
- ⚠️ Dynamic content updates may not always announce to screen readers

### FastAPI Swagger UI

Swagger UI has documented accessibility limitations:
- ✅ Keyboard navigable
- ⚠️ Some ARIA roles missing on expandable sections
- ⚠️ Color contrast in code examples may not meet AA

---

## WCAG 2.1 AA Compliance Checklist

| Criterion | Status | Notes |
|-----------|--------|-------|
| 1.1.1 Non-text Content | ✅ Pass | Gradio provides alt text for UI elements |
| 1.3.1 Info and Relationships | ✅ Pass | Semantic HTML used |
| 1.4.3 Contrast (Minimum) | ⚠️ Partial | Gradio default theme; test verifies |
| 2.1.1 Keyboard | ✅ Pass | All interactive elements reachable |
| 2.4.3 Focus Order | ✅ Pass | Logical tab order |
| 2.4.7 Focus Visible | ✅ Pass | Focus indicators present |
| 3.3.2 Labels or Instructions | ✅ Pass | Input has placeholder/aria-label |
| 4.1.2 Name, Role, Value | ✅ Pass | ARIA attributes present |

---

## Recommendations

1. **Add `lang` attribute** — Ensure the Gradio page declares `lang="en"` (Gradio does this by default)
2. **Live regions** — Verify chat responses use `aria-live="polite"` for screen reader announcements (Gradio handles this)
3. **Skip navigation** — Not critical for a single-purpose chat UI
4. **High contrast mode** — Consider testing with Gradio's built-in dark theme
5. **Screen reader testing** — Manual testing with VoiceOver/NVDA recommended before production

---

## CI Integration

Add to your CI pipeline:

```yaml
# .github/workflows/a11y.yml
name: Accessibility Tests
on: [push, pull_request]
jobs:
  a11y:
    runs-on: ubuntu-latest
    services:
      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv pip install playwright pytest-playwright
      - run: playwright install chromium
      - run: uv run python main.py &
        env:
          LLM_PROVIDER: zen
          ZEN_API_KEY: ${{ secrets.ZEN_API_KEY }}
          EMBED_PROVIDER: huggingface
          EMBED_MODEL: BAAI/bge-small-en-v1.5
          EMBED_DIMS: 384
      - run: sleep 15
      - run: uv run pytest tests/accessibility/ -v --base-url http://localhost:8000
```
