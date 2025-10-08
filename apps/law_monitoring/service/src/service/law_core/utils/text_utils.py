"""Text processing utilities for law analysis."""

import re
from datetime import datetime

from loguru import logger


def extract_field(text: str, field_name: str) -> str:
    """Extract content of a field marked with =FIELD_NAME= up to next field or end."""
    if not text:
        return ""

    field_marker = f"={field_name}="
    if field_marker not in text:
        logger.warning(f"Field marker '{field_marker}' not found in text.")
        return ""

    start = text.find(field_marker) + len(field_marker)
    next_field = text.find("=", start)
    if next_field == -1:
        return text[start:].strip()
    return text[start:next_field].strip()


def extract_section_content(
    text: str, section_name: str, next_section_name: str | None = None
) -> str:
    """Extract content between two section markers."""
    if not text:
        return ""

    section_marker = f"={section_name}="
    if section_marker not in text:
        logger.warning(f"Section marker '{section_marker}' not found in text.")
        return ""

    start = text.find(section_marker) + len(section_marker)

    end_search_start_point = start
    if next_section_name:
        next_marker = f"={next_section_name}="
        # Find the next marker *after* the current section's content begins
        end = text.find(next_marker, end_search_start_point)
        if end == -1:
            # If next_section_name is provided but not found, assume current section goes to end of text
            logger.warning(
                f"Next section marker '{next_marker}' not found after '{section_marker}'. "
                f"Taking content until the end of the text for section '{section_name}'."
            )
            end = len(text)
    else:
        # If no next_section_name, current section goes to end of text
        end = len(text)

    return text[start:end].strip()


def has_revenue_based_penalties(text: str) -> bool:
    """Check if the text indicates revenue-based penalties."""
    value = extract_field(text, "Revenue-Based Penalties")
    return value.upper() == "YES"


def combine_roles_and_penalties_for_display(matrix_content: str) -> str:
    """Extract only the table rows from the COMPLIANCE MATRIX content."""
    logger.info("Extracting table rows from compliance matrix content")

    table_lines = []
    if not matrix_content:  # Handle empty or None matrix_content
        logger.warning("Compliance matrix content is empty. Returning empty string.")
        return ""

    for line in matrix_content.split("\n"):
        if "|" in line and line.strip() and not line.startswith("="):
            table_lines.append(line.strip())

    combined_data = "\n".join(table_lines)

    logger.info(
        f"Extracted {len(table_lines)} table rows from compliance matrix content"
    )
    return combined_data


def remove_xml_metadata_from_html_content(content_str: str) -> str:
    """Remove XML metadata from HTML content before converting to markdown.

    This function is specifically designed to clean HTML content from EUR-Lex documents
    that contains XML processing instructions and filename references that should not
    be part of the final law text.

    Args:
        content_str: The HTML content string to clean

    Returns:
        str: Cleaned HTML content with XML metadata removed
    """
    if not content_str:
        return ""

    # Remove XML processing instructions (e.g., <?xml version="1.0" encoding="UTF-8"?>)
    content_str = re.sub(r"<\?xml[^>]*\?>", "", content_str)

    # Remove XML comments that might contain file references
    content_str = re.sub(r"<!--[^>]*-->", "", content_str)

    # Remove malformed XML declarations (missing opening bracket)
    content_str = re.sub(r'xml version="[^"]*" encoding="[^"]*"\?', "", content_str)

    # Remove any standalone XML-like lines that might appear as text nodes
    lines = content_str.split("\n")
    filtered_lines = []
    for line in lines:
        stripped_line = line.strip()
        # Skip lines that look like XML metadata
        if (
            stripped_line.startswith("xml version=")
            or stripped_line.endswith(".fmx.xml")
            or re.match(r"^[A-Z]_\d+[A-Z]+\.\d+\.fmx\.xml$", stripped_line)
            or re.match(r'^xml version="[^"]*" encoding="[^"]*"\?$', stripped_line)
        ):
            continue
        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def remove_xml_metadata(text: str) -> str:
    """Remove XML metadata lines that appear at the beginning of law texts.

    This function removes:
    1. XML declaration without proper opening bracket: xml version="1.0" encoding="UTF-8"?
    2. Filename references like: L_202501350EN.000101.fmx.xml

    Args:
        text: The input text containing XML metadata

    Returns:
        str: Text with XML metadata removed
    """
    if not text:
        return ""

    # Remove XML declaration line (missing opening bracket)
    text = re.sub(
        r'^xml version="[^"]*" encoding="[^"]*"\?\s*\n?', "", text, flags=re.MULTILINE
    )

    # Remove filename references (.fmx.xml files)
    text = re.sub(
        r"^[A-Z]_\d+[A-Z]+\.\d+\.fmx\.xml\s*\n?", "", text, flags=re.MULTILINE
    )

    # Remove any remaining isolated lines with just XML fragments at the start
    lines = text.split("\n")
    cleaned_lines = []

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        # Skip lines that are XML metadata fragments at the beginning
        if i < 5 and (  # Only check first 5 lines
            stripped_line.startswith("xml version=")
            or stripped_line.endswith(".fmx.xml")
            or (
                stripped_line
                and re.match(r"^[A-Z]_\d+[A-Z]+\.\d+\.fmx\.xml$", stripped_line)
            )
        ):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def clean_text(text: str) -> str:
    """Clean text by removing XML metadata, extra whitespace and normalizing line breaks."""
    if not text:
        return ""

    # First remove XML metadata
    text = remove_xml_metadata(text)

    # Normalize line breaks
    text = re.sub(r"\r\n|\r", "\n", text)

    # Remove excessive whitespace
    text = re.sub(r" +", " ", text)

    # Remove excessive line breaks (more than 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to a maximum length, preserving word boundaries."""
    if not text or len(text) <= max_length:
        return text

    # Find the last space before the max length
    truncated = text[: max_length - len(suffix)]
    last_space = truncated.rfind(" ")

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + suffix


def format_date_for_display(date_val: str | datetime | None) -> str | None:
    """Format date values for display in reports.

    Args:
        date_val: Date value (can be string, datetime, or None)

    Returns:
        str | None: Formatted date string (YYYY-MM-DD) or None
    """
    if date_val is None:
        return None
    if isinstance(date_val, str):
        # If it's a string, extract just the date part (YYYY-MM-DD)
        return date_val[:10] if len(date_val) >= 10 else date_val
    if hasattr(date_val, "strftime"):
        # If it's a datetime object, format it
        return date_val.strftime("%Y-%m-%d")
    return str(date_val)


def remove_images_from_text(text: str) -> str:
    """Remove images from text."""
    return re.sub(r"<img\b[^>]*>", "", text, flags=re.IGNORECASE).strip()
