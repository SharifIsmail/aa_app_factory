# EUR-Lex API Integration

This module provides a flexible and robust interface for retrieving legal acts from the EUR-Lex database using SPARQL queries. The code has been refactored to follow modern software engineering practices while maintaining backward compatibility.

## Architecture Overview

The EUR-Lex integration consists of several components:

1. **`eur_lex_service.py`** - Core service class with enhanced SPARQL query logic
4. **`models.py`** - Pydantic models for comprehensive data validation and serialization
5. **`routes.py`** - FastAPI endpoints for web API access

## Features

- ✅ **Comprehensive Metadata**: Multiple date fields, Eurovoc classifications, and enhanced legal act information
- ✅ **Flexible API**: Multiple ways to access EUR-Lex data (service, utilities, CLI, web API)
- ✅ **Type Safety**: Full Pydantic model validation with comprehensive field coverage
- ✅ **Error Handling**: Comprehensive error handling with custom exceptions
- ✅ **Logging**: Structured logging with loguru
- ✅ **Backward Compatibility**: Existing code continues to work with property-based compatibility
- ✅ **Testing**: Unit tests with mocking
- ✅ **Documentation**: Comprehensive docstrings and examples

## Enhanced Data Model

The new data model provides comprehensive metadata about legal acts:

### LegalAct (Enhanced)
```python
class LegalAct(BaseModel):
    """Model representing a legal act from EUR-Lex with comprehensive metadata."""

    # Core identifiers
    expression_url: str  # URI of the work
    title: str = Field(default="N/A")  # Title of the legal act (defaults to "N/A")
    pdf_url: str = Field(default="")  # URL to the PDF version (defaults to empty string)

    # Classifications
    eurovoc_labels: Optional[str]  # Eurovoc classification labels (pipe-separated)

    # Multiple date fields
    document_date: Optional[datetime]  # Date of the document
    publication_date: datetime  # Publication date in Official Journal (required)
    effect_date: Optional[datetime]  # Date when the act comes into effect
    end_validity_date: Optional[datetime]  # Date when the act ends validity
    notification_date: Optional[datetime]  # Notification date

    # Backward compatibility properties
    @property
    def date(self) -> Optional[datetime]:
        """Returns publication_date for backward compatibility."""
        return self.publication_date
```

## Usage Examples

### 1. Using the Service Directly (Recommended)

```python
from datetime import datetime
from service.law_core.eur_lex_service import EurLexService, EurLexServiceError

# Get the service instance
service = EurLexService.get_instance()

try:
    # Query for legal acts with comprehensive metadata
    response = service.get_legal_acts_by_date_range(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 7),
        limit=100
    )

    print(f"Found {response.total_count} legal acts")

    # Access comprehensive metadata
    for act in response.legal_acts:
        print(f"Title: {act.title}")
        print(f"Work URI: {act.expression_url}")
        print(f"Publication Date: {act.publication_date}")
        print(f"Effect Date: {act.effect_date}")
        print(f"Validity End: {act.end_validity_date}")
        print(f"Eurovoc Labels: {act.eurovoc_labels}")
        print(f"PDF: {act.pdf_url}")
        print("---")

        # Backward compatibility still works
        print(f"Legacy date property: {act.date}")

except EurLexServiceError as e:
    print(f"Service error: {e}")
```

### 2. Working with Enhanced Metadata

```python
# Filter by Eurovoc classifications
environmental_acts = [
    act for act in response.legal_acts
    if act.eurovoc_labels and any(
        keyword in act.eurovoc_labels.lower()
        for keyword in ["environment", "climate", "green"]
    )
]

# Analyze date patterns
for act in response.legal_acts:
    if act.effect_date and act.publication_date:
        delay = (act.effect_date - act.publication_date).days
        print(f"Act '{act.title}' takes effect {delay} days after publication")

    if act.end_validity_date:
        print(f"Act '{act.title}' expires on {act.end_validity_date}")
```

### 3. Using Utility Functions (Backward Compatible)

```python
from datetime import datetime
from pathlib import Path


# Process the results with enhanced metadata
for act in legal_acts:
    print(f"Title: {act['title']}")
    print(f"Work URI: {act['expression_url']}")
    print(f"Publication Date: {act['publication_date']}")
    print(f"Eurovoc Labels: {act['eurovoc_labels']}")

    # Backward compatibility
    print(f"Legacy date: {act['date']}")  # Still available
```

### 4. Using the Web API

#### POST Request with Enhanced Response
```bash
curl -X POST "http://localhost:8000/legal-acts/search" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-07T00:00:00",
    "limit": 100
  }'
```

Expected response structure:
```json
{
  "legal_acts": [
    {
      "expression_url": "http://publications.europa.eu/resource/celex/32024R0001",
      "title": "Commission Regulation (EU) 2024/1...",
      "pdf_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R0001",
      "eurovoc_labels": "environment | climate change | sustainable development",
      "document_date": "2024-01-01T00:00:00",
      "publication_date": "2024-01-01T00:00:00",
      "effect_date": "2024-01-15T00:00:00",
      "end_validity_date": null,
      "notification_date": null
    }
  ],
  "total_count": 1,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-07T00:00:00"
}
```

## Enhanced Query Structure

The SPARQL query has been significantly enhanced to provide comprehensive metadata:

### Query Features
- **Multiple Date Fields**: Document date, publication date, effect date, validity end date, notification date
- **Eurovoc Classifications**: English-language subject classifications concatenated with pipe separators
- **Multilingual Support**: Prioritizes English titles with German fallback
- **Comprehensive Metadata**: Full work URIs and detailed publication information

### Query Structure
```sparql
SELECT
    ?work ?title ?pdf_url
    # Eurovoc classifications
    (GROUP_CONCAT(DISTINCT ?eurovoc_label; separator=" | ") AS ?all_eurovoc_labels)
    # Multiple date fields
    ?document_date ?publication_date ?effect_date ?end_validity_date ?notification_date
WHERE {
    # Core filtering by publication date
    ?work cdm:official-journal-act_date_publication ?publication_date .
    FILTER(?publication_date = "YYYY-MM-DD"^^xsd:date)

    # Optional date fields
    OPTIONAL { ?work cdm:work_date_document ?document_date }
    OPTIONAL { ?work cdm:resource_legal_date_entry-into-force ?effect_date }
    OPTIONAL { ?work cdm:resource_legal_date_end-of-validity ?end_validity_date }
    OPTIONAL { ?work cdm:resource_legal_date_notification ?notification_date }

    # Title and PDF with language preference
    OPTIONAL {
        ?expression cdm:expression_belongs_to_work ?work .
        ?expression cdm:expression_title ?title .
        ?expression cdm:expression_uses_language ?lang_concept .
        ?lang_concept dc:identifier ?title_language .
        FILTER(?title_language = "ENG" || ?title_language = "DEU")

        # PDF URL extraction
        OPTIONAL {
            ?manifestation cdm:manifestation_manifests_expression ?expression .
            ?manifestation cdm:manifestation_type "pdfa2a"^^xsd:string .
            ?item cdm:item_belongs_to_manifestation ?manifestation .
            BIND(?item AS ?pdf_url)
        }
    }

    # Eurovoc classifications
    OPTIONAL {
        ?work cdm:work_is_about_concept_eurovoc ?eurovoc_concept .
        ?eurovoc_concept skos:prefLabel ?eurovoc_label .
        FILTER(lang(?eurovoc_label) = "en")
    }
}
GROUP BY ?work ?title ?pdf_url ?document_date ?publication_date ?effect_date ?end_validity_date ?notification_date
ORDER BY DESC(?publication_date)
```

## Data Analysis Capabilities

The enhanced data model enables sophisticated analysis:

### Date Analysis
```python
# Find acts with immediate effect
immediate_effect = [
    act for act in legal_acts
    if act.effect_date == act.publication_date
]

# Find acts with delayed implementation
delayed_acts = [
    act for act in legal_acts
    if act.effect_date and act.publication_date and
    act.effect_date > act.publication_date
]

# Find temporary acts (with end dates)
temporary_acts = [
    act for act in legal_acts
    if act.end_validity_date
]
```

### Subject Classification Analysis
```python
# Analyze subject matter distribution
eurovoc_stats = {}
for act in legal_acts:
    if act.eurovoc_labels:
        for label in act.eurovoc_labels.split(" | "):
            eurovoc_stats[label] = eurovoc_stats.get(label, 0) + 1

# Most common subjects
sorted_subjects = sorted(eurovoc_stats.items(), key=lambda x: x[1], reverse=True)
print("Top 10 subjects:")
for subject, count in sorted_subjects[:10]:
    print(f"  {subject}: {count} acts")
```

## Backward Compatibility

### Migration Guide

Existing code using the original data model continues to work:

**Before (still works):**
```python
# Legacy property access
for act in legal_acts:
    print(f"Date: {act.date}")  # Returns publication_date
    print(f"URL: {act.expression_url}")  # Returns work URI
    print(f"Title: {act.title}")  # Same as before
    print(f"PDF: {act.pdf_url}")  # Same as before
```

**After (enhanced access):**
```python
# New comprehensive access
for act in legal_acts:
    print(f"Publication Date: {act.publication_date}")
    print(f"Effect Date: {act.effect_date}")
    print(f"Document Date: {act.document_date}")
    print(f"Validity End: {act.end_validity_date}")
    print(f"Notification Date: {act.notification_date}")
    print(f"Work URI: {act.work}")
    print(f"Eurovoc Labels: {act.eurovoc_labels}")
    print(f"Title: {act.title}")
    print(f"PDF: {act.pdf_url}")
```

## Configuration

### Environment Variables

The service uses the following configuration:

- **SPARQL Endpoint**: `https://publications.europa.eu/webapi/rdf/sparql` (hardcoded)
- **Default Limit**: 1000 results per day
- **Language Preference**: English ("ENG") with German ("DEU") fallback for titles
- **Document Type**: PDF/A-2a format
- **Eurovoc Language**: English labels only
- **Data Validation**: Records with missing publication_date are skipped
- **Default Values**:
  - title defaults to "N/A"
  - pdf_url defaults to empty string ""
  - eurovoc_labels can be None

### Customization Options

To customize the enhanced service behavior:

1. **Modify date fields** in the SPARQL query to include additional date types
2. **Change language preferences** in the title and Eurovoc sections
3. **Adjust Eurovoc filtering** to include multiple languages
4. **Add additional metadata fields** by extending the SELECT clause

## Performance Considerations

### Enhanced Query Performance
- **Grouping**: Results are grouped to handle multiple Eurovoc labels per act
- **Optional Fields**: All enhanced fields are optional to maintain query performance
- **Date Filtering**: Efficient date-based filtering maintains speed
- **Language Preference**: Prioritized language selection reduces result size

### Memory Usage
- **Eurovoc Labels**: Concatenated strings may increase memory usage
- **Multiple Dates**: Additional date fields increase object size
- **Backward Compatibility**: Property methods add minimal overhead

## Error Handling

Enhanced error handling covers the new data model:

```python
try:
    response = service.get_legal_acts_by_date_range(start_date, end_date)

    # Check for comprehensive data
    for act in response.legal_acts:
        # publication_date is now required - missing ones are skipped during parsing
        if not act.eurovoc_labels:
            logger.info(f"Act {act.expression_url} has no Eurovoc classifications")
        if not act.pdf_url:
            logger.info(f"Act {act.expression_url} has no PDF URL available")

except EurLexServiceError as e:
    logger.error(f"Service error: {e}")
except ValueError as e:
    logger.error(f"Data validation error: {e}")
```

## Testing

The enhanced service includes comprehensive tests:

```bash
# Run all tests including enhanced data model tests
pytest src/service/tests/test_eur_lex.py

# Test specific enhanced features
pytest src/service/tests/test_eur_lex.py::TestEnhancedLegalAct

# Test backward compatibility
pytest src/service/tests/test_eur_lex.py::TestBackwardCompatibility
```

## API Reference

For detailed API documentation, see the docstrings in each module:

- `service.eur_lex_service.EurLexService` - Enhanced service with comprehensive metadata
- `service.models.LegalAct` - Enhanced data model with multiple date fields and classifications
- `service.models.LegalActsResponse` - Response model for comprehensive legal act data
