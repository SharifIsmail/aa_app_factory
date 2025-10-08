from pathlib import Path

import pytest

SPEC_PATH = Path(__file__).resolve().parent.parent / "provider_interface_spec.md"


def test_spec_document_exists():
    assert SPEC_PATH.exists(), "provider_interface_spec.md is missing"


@pytest.mark.parametrize(
    "section_header",
    [
        "# External Legal Act Provider Specification",
        "## 1. Python Module Interface",
        "## 2. HTTP Content Endpoint",
        "## 3. Configuration Hand-off",
        "## 4. Error Reporting Expectations",
    ],
)
def test_spec_contains_required_sections(section_header: str):
    content = SPEC_PATH.read_text(encoding="utf-8")
    assert section_header in content, f"Missing section '{section_header}' in spec document"


def test_spec_contains_html_example():
    content = SPEC_PATH.read_text(encoding="utf-8")
    assert "<article" in content and "data-law-monitoring=\"legal-act\"" in content, (
        "Spec should include sample HTML article with data-law-monitoring attribute"
    )
