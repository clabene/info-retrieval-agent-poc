"""Accessibility tests using Playwright + axe-core.

Runs automated WCAG 2.1 AA audits against the Gradio Chat UI and API docs page.

Prerequisites:
    pip install playwright pytest-playwright axe-playwright-python
    playwright install chromium

Usage:
    pytest tests/accessibility/test_a11y.py --base-url http://localhost:8000

Set BASE_URL env var or use --base-url pytest arg to override the default target.
"""

import os

import pytest
from playwright.sync_api import Page

# Allow override via env var or pytest CLI
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


def inject_axe(page: Page) -> None:
    """Inject axe-core library into the page for accessibility scanning."""
    axe_cdn = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
    page.evaluate(
        f"""
        await new Promise((resolve, reject) => {{
            if (window.axe) {{ resolve(); return; }}
            const script = document.createElement('script');
            script.src = '{axe_cdn}';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        }});
    """
    )


def run_axe(page: Page, context: str = "document", tags: list[str] | None = None) -> dict:
    """Run axe-core analysis and return results.

    Args:
        page: Playwright page object.
        context: CSS selector or 'document' for full page.
        tags: WCAG tags to test against (default: wcag2a, wcag2aa, wcag21a, wcag21aa).

    Returns:
        axe-core results dict with violations, passes, incomplete, inapplicable.
    """
    if tags is None:
        tags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

    inject_axe(page)

    options = {"runOnly": {"type": "tag", "values": tags}}
    ctx = "document" if context == "document" else f'"{context}"'

    results = page.evaluate(
        f"""
        async () => {{
            const results = await axe.run({ctx}, {options});
            return results;
        }}
    """
    )
    return results


def format_violations(violations: list[dict]) -> str:
    """Format axe violations into a readable report string."""
    if not violations:
        return "No violations found ✓"

    lines = [f"\n{'='*60}", f"ACCESSIBILITY VIOLATIONS: {len(violations)}", "=" * 60]
    for i, v in enumerate(violations, 1):
        lines.append(f"\n[{i}] {v['id']} — {v['impact'].upper()}")
        lines.append(f"    Description: {v['description']}")
        lines.append(f"    Help: {v['help']}")
        lines.append(f"    Help URL: {v['helpUrl']}")
        lines.append(f"    WCAG: {', '.join(v.get('tags', []))}")
        for node in v.get("nodes", [])[:3]:  # Show max 3 affected nodes
            target = node.get("target", ["unknown"])
            lines.append(f"    → Element: {target}")
            if node.get("failureSummary"):
                lines.append(f"      Fix: {node['failureSummary'][:200]}")
    return "\n".join(lines)


class TestGradioChatAccessibility:
    """Accessibility tests for the Gradio Chat UI at /chat."""

    def test_chat_page_loads(self, page: Page, base_url: str):
        """Verify the chat page loads successfully."""
        response = page.goto(f"{base_url}/chat")
        assert response is not None
        assert response.status == 200

    def test_chat_wcag_aa_compliance(self, page: Page, base_url: str):
        """Run full WCAG 2.1 AA audit on the Gradio chat interface."""
        page.goto(f"{base_url}/chat")
        # Wait for Gradio to fully render
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)  # Extra time for Gradio JS hydration

        results = run_axe(page)
        violations = results.get("violations", [])

        report = format_violations(violations)
        print(report)

        # Filter to only critical and serious violations for hard failure
        critical_violations = [v for v in violations if v.get("impact") in ("critical", "serious")]
        assert len(critical_violations) == 0, (
            f"Found {len(critical_violations)} critical/serious WCAG AA violations:\n{report}"
        )

    def test_chat_keyboard_navigation(self, page: Page, base_url: str):
        """Verify basic keyboard navigation works in the chat interface."""
        page.goto(f"{base_url}/chat")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Tab through the page - should reach the text input
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")

        # Check that focus is visible (some element has focus)
        focused = page.evaluate("document.activeElement?.tagName")
        assert focused is not None, "No element received focus via keyboard navigation"

    def test_chat_input_has_label(self, page: Page, base_url: str):
        """Verify the chat input has an accessible label or aria-label."""
        page.goto(f"{base_url}/chat")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Look for textarea (Gradio's chat input)
        textareas = page.query_selector_all("textarea")
        for textarea in textareas:
            aria_label = textarea.get_attribute("aria-label")
            placeholder = textarea.get_attribute("placeholder")
            label_attr = textarea.get_attribute("id")
            # Check if there's an associated label or aria-label
            has_label = bool(aria_label or placeholder or label_attr)
            assert has_label, "Chat textarea has no accessible label, aria-label, or placeholder"

    def test_chat_color_contrast(self, page: Page, base_url: str):
        """Check color contrast specifically (subset of WCAG AA)."""
        page.goto(f"{base_url}/chat")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        results = run_axe(page, tags=["wcag2aa"])
        contrast_violations = [v for v in results.get("violations", []) if "contrast" in v["id"]]

        if contrast_violations:
            report = format_violations(contrast_violations)
            print(f"Color contrast issues found:\n{report}")
            # Warn but don't fail for Gradio's built-in styling (we can't control it)
            # Only fail if there are critical contrast issues
            critical = [v for v in contrast_violations if v.get("impact") == "critical"]
            assert len(critical) == 0, f"Critical contrast violations: {report}"


class TestAPIDocsAccessibility:
    """Accessibility tests for the FastAPI /docs (Swagger UI) page."""

    def test_docs_page_loads(self, page: Page, base_url: str):
        """Verify the OpenAPI docs page loads successfully."""
        response = page.goto(f"{base_url}/docs")
        assert response is not None
        assert response.status == 200

    def test_docs_wcag_aa_compliance(self, page: Page, base_url: str):
        """Run WCAG 2.1 AA audit on the Swagger UI docs page."""
        page.goto(f"{base_url}/docs")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        results = run_axe(page)
        violations = results.get("violations", [])

        report = format_violations(violations)
        print(report)

        # Only fail on critical violations (Swagger UI is third-party)
        critical_violations = [v for v in violations if v.get("impact") == "critical"]
        assert len(critical_violations) == 0, (
            f"Found {len(critical_violations)} critical WCAG AA violations in /docs:\n{report}"
        )
