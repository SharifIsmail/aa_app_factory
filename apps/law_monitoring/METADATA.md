# Metadata Integration Guide

This document provides a comprehensive guide for integrating new metadata fields end-to-end in the law monitoring system, based on the document type metadata implementation.

## Overview

The law monitoring system has a complete data flow from EUR-Lex → Backend Storage → Report Generation → Frontend Display. To add new metadata, you need to update files at each stage of this pipeline.

## Data Flow Architecture

```
EUR-Lex API → Discovery Worker → Storage → Report Generation → Frontend Display
     ↓              ↓           ↓            ↓                    ↓
SPARQL Query   Law Data     LawData      PDF/HTML/Word      Vue Components
               Storage      Model        Reports            TypeScript Types
```

## Files to Update for New Metadata

### 1. Backend Data Models (`service/src/service/models.py`)

**Purpose**: Define the data structure and validation

**Required Changes**:
- Add new fields to `LegalAct` model (for EUR-Lex data)
- Add new fields to `LawData` model (for stored law data)
- Add enums if the field has predefined values
- Add mapping functions for complex data types

**Example**:
```python
# Add to LegalAct model
document_type: Optional[str] = Field(
    default=None,
    description="Document type URI (directive, regulation, etc.)",
)
document_type_label: Optional[DocumentTypeLabel] = Field(
    default=DocumentTypeLabel.UNKNOWN,
    description="Human-readable document type label",
)

# Add enum for controlled values
class DocumentTypeLabel(str, Enum):
    DIRECTIVE = "DIRECTIVE"
    REGULATION = "REGULATION"
    # ... other values
    
    @classmethod
    def from_eur_lex_label(cls, eur_lex_label: Optional[str]) -> "DocumentTypeLabel":
        # Mapping logic here
```

### 2. EUR-Lex Service (`service/src/service/law_core/eur_lex_service.py`)

**Purpose**: Extract metadata from EUR-Lex SPARQL API

**Required Changes**:
- Add new fields to SPARQL query SELECT clause
- Add OPTIONAL blocks to extract the new metadata
- Update GROUP BY clause to include new fields
- Add parsing logic in `_parse_sparql_json_result` method
- Apply validation and mapping functions

**Example**:
```python
# In SPARQL query
SELECT 
    ?work ?title ?pdf_url
    ?document_type ?document_type_label  # Add new fields
    
# Add OPTIONAL extraction block
OPTIONAL {
    ?work cdm:work_has_resource-type ?document_type .
    ?document_type skos:prefLabel ?document_type_label .
    FILTER(lang(?document_type_label) = "en")
}

# Update GROUP BY
GROUP BY ?work ?title ?pdf_url ?document_type ?document_type_label

# Add parsing logic
document_type = result.get("document_type", {}).get("value", None)
document_type_label = result.get("document_type_label", {}).get("value", None)

# Add to LegalAct construction
return LegalAct(
    # ... existing fields
    document_type=document_type,
    document_type_label=DocumentTypeLabel.from_eur_lex_label(document_type_label),
)
```

### 3. Discovery Worker (`service/src/service/law_core/background_work/discovery_worker.py`)

**Purpose**: Store discovered metadata in the data storage

**Required Changes**:
- Add new fields to the law data dictionary that gets stored

**Example**:
```python
# Add to law data storage
{
    # ... existing fields
    "document_type": legal_act.document_type,
    "document_type_label": legal_act.document_type_label,
}
```

### 4. Law Data Service (`service/src/service/law_data_service.py`)

**Purpose**: Load stored law data into LawData models

**Required Changes**:
- Add new fields to `LawData` construction in `_load_and_parse_law_file` method

**Example**:
```python
return LawData(
    # ... existing fields
    document_type=raw_data.get("document_type"),
    document_type_label=raw_data.get("document_type_label"),
)
```

### 5. Summary Worker (`service/src/service/law_core/background_work/summary_worker.py`)

**Purpose**: Include metadata in report generation pipeline

**Required Changes**:
- Add new fields to metadata dictionary passed to report generation

**Example**:
```python
metadata = {
    # ... existing fields
    "document_type": law_data.get("document_type_label", "N/A"),
}
```

### 6. Report Generators (`service/src/service/law_core/artifacts/generators/`)

**Purpose**: Display metadata in generated reports (PDF, HTML, Word)

**Files to Update**:
- `pdf_generator.py`
- `html_generator.py` 
- `word_generator.py`

**Required Changes**:
- Add display logic for new metadata fields
- Update templates to show the new information

**Example** (PDF Generator):
```python
# Add to Basic Information section
if law_summary_data.get("document_type"):
    story.extend(
        self._create_info_item(
            "DOCUMENT TYPE",
            str(law_summary_data["document_type"]),
            info_label_style,
            info_value_style,
        )
    )
```

### 7. Frontend TypeScript Types (`ui/src/modules/monitoring/types/index.ts`)

**Purpose**: Define TypeScript interfaces and types for frontend

**Required Changes**:
- Add new fields to `PreprocessedLaw` interface
- Add enums if needed for controlled values
- Update helper functions if necessary

**Example**:
```typescript
export enum DocumentTypeLabel {
  DIRECTIVE = 'DIRECTIVE',
  REGULATION = 'REGULATION',
  // ... other values
}

export interface PreprocessedLaw {
  // ... existing fields
  document_type: string | null;
  document_type_label: DocumentTypeLabel | null;
}
```

### 8. Frontend Components (`ui/src/modules/monitoring/components/`)

**Purpose**: Display metadata in the user interface

**Key Component**: `MonitoringDisplayAccordionContent.vue`

**Required Changes**:
- Add conditional rendering logic for new metadata
- Add styling and visual design
- Import necessary types

**Example**:
```vue
<!-- Add metadata display section -->
<div v-if="law.document_type || law.document_type_label">
  <AaText size="base" weight="bold" class="mb-2">Document Type</AaText>
  <div class="flex items-center gap-2">
    <span :class="[
      'inline-block rounded-full px-3 py-1 text-xs font-medium',
      law.document_type_label === DocumentTypeLabel.DIRECTIVE
        ? 'bg-green-100 text-green-800'
        : 'bg-gray-100 text-gray-800',
    ]">
      {{ law.document_type_label }}
    </span>
  </div>
</div>
```

## Implementation Checklist

### Phase 1: Backend Data Flow
- [ ] Update `models.py` with new fields and enums
- [ ] Modify EUR-Lex service SPARQL query
- [ ] Update discovery worker storage
- [ ] Fix law data service loading
- [ ] Update summary worker metadata

### Phase 2: Report Generation  
- [ ] Update PDF generator
- [ ] Update HTML generator
- [ ] Update Word generator

### Phase 3: Frontend Integration
- [ ] Add TypeScript types
- [ ] Update Vue components
- [ ] Add styling and visual design
- [ ] Test conditional rendering

### Phase 4: Testing & Validation
- [ ] Run backend linting (`./lint.sh`)
- [ ] Run frontend linting (`./lint_frontend.sh`)
- [ ] Test EUR-Lex data extraction
- [ ] Verify report generation
- [ ] Test frontend display

## Common Patterns

### Enum Mapping Pattern
When EUR-Lex returns varied string values, create a mapping function:
```python
@classmethod
def from_eur_lex_label(cls, eur_lex_label: Optional[str]) -> "EnumType":
    if not eur_lex_label:
        return cls.UNKNOWN
    
    normalized = eur_lex_label.upper().strip()
    
    # Direct mappings
    mappings = {
        "VALUE1": cls.ENUM1,
        "VALUE2": cls.ENUM2,
    }
    
    if normalized in mappings:
        return mappings[normalized]
    
    # Pattern matching for variations
    if "PATTERN" in normalized:
        return cls.ENUM1
    
    return cls.OTHER
```

### SPARQL Query Pattern
For extracting new metadata from EUR-Lex:
```sparql
# Add to SELECT clause
?new_field ?new_field_label

# Add OPTIONAL extraction block
OPTIONAL {
    ?work cdm:work_has_property ?new_field .
    ?new_field skos:prefLabel ?new_field_label .
    FILTER(lang(?new_field_label) = "en")
}

# Update GROUP BY
GROUP BY ?work ?title ... ?new_field ?new_field_label
```

### Frontend Display Pattern
For conditional metadata display:
```vue
<div v-if="law.new_field">
  <AaText size="base" weight="bold" class="mb-2">Field Label</AaText>
  <div class="metadata-display">
    {{ law.new_field }}
  </div>
</div>
```

## Troubleshooting

### Common Issues
1. **Enum Validation Errors**: EUR-Lex returns values not in your enum
   - Solution: Add mapping function or expand enum values

2. **Missing Data in Reports**: Metadata not flowing through to reports
   - Check: Summary worker metadata dictionary
   - Check: Report generator templates

3. **Frontend Type Errors**: TypeScript compilation failures
   - Check: Interface definitions match backend models
   - Check: Enum imports in components

4. **SPARQL Query Errors**: Invalid or incomplete queries
   - Test queries in EUR-Lex SPARQL endpoint
   - Validate GROUP BY includes all SELECT fields

### Validation Commands
```bash
# Backend
cd service && ./lint.sh
cd service && uv run pytest src/service/tests/api_tests/test_eur_lex.py

# Frontend  
cd ui && ./lint_frontend.sh
cd ui && pnpm run type-check
cd ui && pnpm run build
```

## Example: Document Type Implementation

This guide is based on the successful implementation of document type metadata. The complete implementation touched all the files mentioned above and demonstrates the full end-to-end integration pattern.

**Reference Commit:** `[COMMIT_HASH_PLACEHOLDER]` - Complete document type metadata integration

Key files modified:
- `service/src/service/models.py` - Added DocumentTypeLabel enum and mapping
- `service/src/service/law_core/eur_lex_service.py` - Enhanced SPARQL query
- `service/src/service/law_core/background_work/discovery_worker.py` - Added storage
- `service/src/service/law_data_service.py` - Fixed loading
- `service/src/service/law_core/background_work/summary_worker.py` - Added to metadata
- `ui/src/modules/monitoring/types/index.ts` - Added TypeScript types with color mapping
- `ui/src/modules/monitoring/components/MonitoringDisplayAccordionContent.vue` - Added display

This implementation provides a complete template for integrating any new metadata field in the law monitoring system.

## Commit Strategy for Metadata Integration

### Single Commit Approach (Recommended)

For metadata features like document type integration, use a **single comprehensive commit** that includes:

1. **Complete Feature Implementation**: All files updated in one atomic commit
2. **End-to-End Validation**: Ensure the feature works from EUR-Lex → Frontend
3. **Quality Checks**: Run linting and type checking before committing
4. **Clear Documentation**: Update this METADATA.md file with the new pattern

### Pre-Commit Checklist

Before committing metadata integration changes:

- [ ] **Backend linting passes**: `./lint.sh` 
- [ ] **Frontend linting passes**: `./lint_frontend.sh`
- [ ] **Type checking passes**: `pnpm run type-check`
- [ ] **Enum synchronization**: Frontend and backend enums match exactly
- [ ] **Color mapping centralized**: No hardcoded styling logic in components
- [ ] **Data flow tested**: Validate EUR-Lex → Backend → Frontend → Reports
- [ ] **Documentation updated**: Add implementation details to METADATA.md

### Commit Message Pattern

```
feat: implement [metadata_name] metadata end-to-end integration

Add comprehensive [metadata_name] metadata support from EUR-Lex to frontend display:

**Backend Models & Data Pipeline:**
- Add [MetadataEnum] enum with EUR-Lex metadata types
- Extend LegalAct and LawData models with [metadata_fields]
- Add validation and mapping for EUR-Lex metadata labels

**EUR-Lex Service:**
- Enhance SPARQL query to extract [metadata_name] metadata
- Add robust parsing and enum mapping
- Handle unknown values gracefully with fallback

**Data Pipeline:**
- Update discovery worker to store metadata
- Fix law data service to include metadata in LawData construction  
- Update summary worker to pass metadata to report generation

**Report Generation:**
- Add metadata display to PDF, HTML, and Word reports
- Include metadata in report templates and pipeline

**Frontend Integration:**
- Add TypeScript types and enums
- Update PreprocessedLaw interface 
- Add color-coded display with centralized styling utility
- Implement graceful fallback handling

**Documentation:**
- Update METADATA.md with implementation patterns

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

This approach ensures clean git history and provides a complete reference implementation for future metadata integrations.