"""
Parsing utilities for company data extraction.
"""


def parse_company_data_from_agent_steps_logs(
    text: str,
) -> dict[str, dict[str, str | None]]:
    """
    Parse the agent steps logs with format "# DATA I HAVE GATHERED SO FAR:" and bullet points with source URLs.

    Args:
        text (str): The agent steps log text to parse, with format like:
            # DATA I HAVE GATHERED SO FAR:
            - Company name: SHELL NIGERIA EXPLORATION PROPERTIES CHARLIE LTD (SOURCE URL: https://example.com)

    Returns:
        dict: A dictionary with keys from labels and values/sources from the text
    """
    if not text:
        return {}

    result = {}
    lines = text.split("\n")

    # Flag to indicate if we're in the "DATA I HAVE GATHERED SO FAR" section
    in_gathered_data = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if we're entering the gathered data section
        if "# DATA I HAVE GATHERED SO FAR:" in line:
            in_gathered_data = True
            continue

        # Check if we're leaving the gathered data section
        if line.startswith("#") and "DATA I HAVE GATHERED SO FAR" not in line:
            in_gathered_data = False
            continue

        # Skip lines that aren't in the gathered data section or don't start with a dash
        if not in_gathered_data or not line.startswith("-"):
            continue

        try:
            # Remove the leading dash and space
            line = line[1:].strip()

            # Split by colon to get label and value+source
            if ":" not in line:
                continue

            label_part, value_part = line.split(":", 1)
            label = label_part.strip()

            # Default values
            value = "Not specified"
            source_url = None

            # Extract source URL if present
            if "(SOURCE URL:" in value_part:
                value_source_parts = value_part.split("(SOURCE URL:", 1)
                value = value_source_parts[0].strip()

                # Extract the URL from the source part
                source_url = value_source_parts[1].strip()
                if source_url.endswith(")"):
                    source_url = source_url[:-1].strip()
            else:
                value = value_part.strip()

            # Add to result dictionary
            result[label] = {"value": value, "source_url": source_url}

        except Exception as e:
            # If parsing fails for a line, continue with other lines
            print(f"Error parsing line '{line}': {str(e)}")
            continue

    return result


def parse_company_data_re_fetch_after_feedback_results(
    text: str,
) -> dict[str, dict[str, str | None]]:
    """
    Parse the structured company data response into a dictionary.
    Each property has one value and one or more source URLs.

    Args:
        text (str): The structured company data text to parse

    Returns:
        dict: A dictionary with keys from property names and values/sources
    """
    if not text:
        return {}

    result = {}
    current_property = None
    current_urls: list[str] = []

    lines = text.split("\n")

    for line in lines:
        line = line.strip().replace("*", "")
        if not line or ":" not in line:
            continue

        # Extract label and value
        label, value = [part.strip() for part in line.split(":", 1)]

        # Handle Source lines
        if label == "Source":
            if current_property and value and not value.endswith("[SEARCH]"):
                current_urls.append(value)
            continue

        # Skip specific labels we want to ignore
        if label in ["Sources", "Note", "Feedback Addressed", "Remaining Issues"]:
            continue

        # Any line that's not a source is a property and its value
        if not label.startswith("Source"):
            # If we have a previous property, add it to the result before starting a new one
            if current_property and current_property in result:
                # Add URLs to the existing property
                result[current_property]["source_url"] = (
                    current_urls[0] if current_urls else None
                )

            # Start tracking a new property
            if label not in result:
                result[label] = {"value": value, "source_url": None}
                current_property = label
                current_urls = []

    # Update source URL for the last property
    if current_property and current_property in result and current_urls:
        result[current_property]["source_url"] = (
            current_urls[0] if current_urls else None
        )

    return result
