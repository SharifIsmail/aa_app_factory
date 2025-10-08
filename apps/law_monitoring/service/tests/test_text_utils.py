"""Unit tests for XML metadata removal method."""

from service.law_core.utils.text_utils import remove_xml_metadata_from_html_content


def test_remove_xml_metadata_from_html_content() -> None:
    """Comprehensive test for remove_xml_metadata_from_html_content method.

    This test covers all XML metadata patterns that were causing issues
    and would have FAILED before the fix was implemented.
    """
    # Test case 1: Complete EUR-Lex document structure with all problematic elements
    problematic_html = """<div id="eli-container">
<?xml version="1.0" encoding="UTF-8"?>
<!-- XML metadata comment -->
xml version="1.0" encoding="UTF-8"?

L_202501350EN.000101.fmx.xml

<table>
<tr><td>European flag</td><td>Official Journal</td></tr>
</table>

<h1>REGULATION (EU) 2025/41 OF THE EUROPEAN PARLIAMENT</h1>
<p>This is the actual legal content that should be preserved.</p>
<!-- Another comment -->
</div>"""

    result = remove_xml_metadata_from_html_content(problematic_html)

    # XML metadata should be completely removed
    assert '<?xml version="1.0" encoding="UTF-8"?>' not in result
    assert 'xml version="1.0" encoding="UTF-8"?' not in result
    assert "L_202501350EN.000101.fmx.xml" not in result
    assert "<!-- XML metadata comment -->" not in result
    assert "<!-- Another comment -->" not in result

    # Legal content should be preserved
    assert "<h1>REGULATION (EU) 2025/41" in result
    assert "actual legal content" in result
    assert "<table>" in result
    assert "European flag" in result

    # Test case 2: Various filename patterns
    filename_patterns = [
        "L_202500041EN.000101.fmx.xml",  # L-series (Legislation)
        "C_202500458EN.000101.fmx.xml",  # C-series (Information and Notices)
        "R_202500123EN.000101.fmx.xml",  # R-series (Recommendations)
    ]

    for filename in filename_patterns:
        html_with_filename = f"""<div>
{filename}
<h1>Document for {filename[:1]}-series</h1>
</div>"""

        result = remove_xml_metadata_from_html_content(html_with_filename)
        assert filename not in result
        assert f"{filename[:1]}-series" in result

    # Test case 3: Normal content without XML metadata (should be unchanged)
    normal_html = """<div id="content">
<h1>Normal Document</h1>
<p>This is normal content without any XML metadata.</p>
</div>"""

    result = remove_xml_metadata_from_html_content(normal_html)
    assert result == normal_html

    # Test case 4: Empty and None inputs
    assert remove_xml_metadata_from_html_content("") == ""

    # Test case 5: Only XML metadata (should result in mostly empty content)
    only_xml = """xml version="1.0" encoding="UTF-8"?
L_202500041EN.000101.fmx.xml"""

    result = remove_xml_metadata_from_html_content(only_xml)
    assert "xml version" not in result
    assert "fmx.xml" not in result
    assert result.strip() == ""

    # Test case 6: Specific malformed XML declaration pattern from the bug report
    malformed_xml_html = """<div>
xml version="1.0" encoding="UTF-8"?
<h1>DIRECTIVE 2025/123</h1>
<p>Some law content here</p>
</div>"""

    result = remove_xml_metadata_from_html_content(malformed_xml_html)
    assert 'xml version="1.0" encoding="UTF-8"?' not in result
    assert "DIRECTIVE 2025/123" in result
    assert "Some law content here" in result
