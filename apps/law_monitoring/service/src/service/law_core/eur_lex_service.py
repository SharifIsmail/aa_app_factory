"""
EUR-Lex API Service

This module provides a service for retrieving legal acts from the EUR-Lex database
using SPARQL queries. It's designed to be flexible and easily integrated into
larger applications.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional

import requests
from loguru import logger
from rdflib.query import ResultRow

from service.core.utils.singleton import SingletonMeta
from service.core.utils.utils import parse_date_string
from service.models import (
    DocumentTypeLabel,
    LegalAct,
    LegalActsResponse,
    OfficialJournalSeries,
)


class EurLexServiceError(Exception):
    """Custom exception for EUR-Lex service errors."""

    pass


class EurLexService(metaclass=SingletonMeta):
    """Service for interacting with the EUR-Lex SPARQL endpoint."""

    SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
    # Pre-computed set of valid document type labels for efficient lookup
    VALID_DOCUMENT_TYPE_LABELS = {
        label.value for label in DocumentTypeLabel if label != DocumentTypeLabel.OTHER
    }

    def __init__(self) -> None:
        """Initialize the EUR-Lex service."""
        if hasattr(self, "_initialized"):
            return

        logger.info("Initializing EurLexService")
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "EurLexService":
        """Get the singleton instance. Creates one if it doesn't exist."""
        return cls()

    def _parse_error_response(self, response: requests.Response) -> str:
        """
        Parse error response from EUR-Lex endpoint to extract meaningful error information.

        Args:
            response: The HTTP response object

        Returns:
            Formatted error message with extracted information
        """
        status_code = response.status_code
        content_type = response.headers.get("content-type", "").lower()

        # Start with basic error info
        error_info = f"HTTP {status_code}"

        # Map common status codes to descriptions
        status_descriptions = {
            400: "Bad Request - Invalid SPARQL query syntax",
            401: "Unauthorized - Authentication required",
            403: "Forbidden - Access denied",
            404: "Not Found - Endpoint not available",
            429: "Too Many Requests - Rate limit exceeded",
            500: "Internal Server Error - Server-side error",
            502: "Bad Gateway - Gateway error",
            503: "Service Unavailable - Service temporarily down",
            504: "Gateway Timeout - Request timeout",
        }

        if status_code in status_descriptions:
            error_info += f" ({status_descriptions[status_code]})"

        try:
            response_text = response.text

            # Handle HTML responses (like maintenance pages)
            if "text/html" in content_type or "<html" in response_text.lower():
                # Extract title from HTML
                title_match = re.search(
                    r"<title[^>]*>(.*?)</title>",
                    response_text,
                    re.IGNORECASE | re.DOTALL,
                )
                if title_match:
                    title = title_match.group(1).strip()
                    error_info += f" - {title}"

                # Look for common maintenance or error messages
                maintenance_patterns = [
                    r"under maintenance",
                    r"temporarily unavailable",
                    r"service unavailable",
                    r"maintenance mode",
                    r"scheduled maintenance",
                ]

                for pattern in maintenance_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        error_info += " (Site under maintenance)"
                        break

                # Extract any visible error message from body
                body_match = re.search(
                    r"<body[^>]*>(.*?)</body>", response_text, re.IGNORECASE | re.DOTALL
                )
                if body_match:
                    body_content = body_match.group(1)
                    # Remove HTML tags and get first meaningful text
                    clean_text = re.sub(r"<[^>]+>", " ", body_content)
                    clean_text = re.sub(r"\s+", " ", clean_text).strip()
                    if clean_text and len(clean_text) < 200:
                        error_info += f" - {clean_text}"

            # Handle JSON responses (API errors)
            elif "application/json" in content_type:
                try:
                    error_data = json.loads(response_text)
                    if isinstance(error_data, dict):
                        # Look for common error fields
                        error_fields = [
                            "error",
                            "message",
                            "error_description",
                            "detail",
                        ]
                        for field in error_fields:
                            if field in error_data:
                                error_info += f" - {error_data[field]}"
                                break
                except json.JSONDecodeError:
                    pass

            # Handle plain text responses
            elif "text/plain" in content_type:
                if response_text and len(response_text) < 200:
                    error_info += f" - {response_text.strip()}"

            # If we couldn't extract meaningful info, show truncated response
            if error_info == f"HTTP {status_code}" and response_text:
                truncated_text = response_text[:150].strip()
                if len(response_text) > 150:
                    truncated_text += "..."
                error_info += f" - Response: {truncated_text}"

        except Exception as e:
            logger.debug(f"Error parsing error response: {e}")
            error_info += " - Could not parse error details"

        return error_info

    def get_legal_acts_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 1000
    ) -> LegalActsResponse:
        """
        Retrieve legal acts published within a specified date range.

        Args:
            start_date: Start date for the query
            end_date: End date for the query (inclusive)
            limit: Maximum number of results per day (default: 1000)

        Returns:
            LegalActsResponse containing the list of legal acts and metadata

        Raises:
            EurLexServiceError: If there's an error querying the EUR-Lex database
            ValueError: If the date range is invalid
        """
        if end_date < start_date:
            logger.error(
                f"End date must be after or equal to start date: {end_date} < {start_date}"
            )
            raise ValueError("End date must be after or equal to start date")

        logger.info(
            f"Querying EUR-Lex for legal acts from {start_date.date()} to {end_date.date()}"
        )

        all_legal_acts = []
        current_date = start_date

        try:
            while current_date <= end_date:
                logger.debug(f"Processing date: {current_date.date()}")

                daily_acts = self._get_legal_acts_for_date(current_date, limit)
                all_legal_acts.extend(daily_acts)

                current_date += timedelta(days=1)

            logger.info(f"Successfully retrieved {len(all_legal_acts)} legal acts")

            return LegalActsResponse(
                legal_acts=all_legal_acts,
                total_count=len(all_legal_acts),
                start_date=start_date,
                end_date=end_date,
            )

        except Exception as e:
            logger.error(f"Error querying EUR-Lex database: {str(e)}")
            raise EurLexServiceError(f"Failed to retrieve legal acts: {str(e)}") from e

    def _get_legal_acts_for_date(self, date: datetime, limit: int) -> list[LegalAct]:
        """
        Retrieve legal acts for a specific date using requests.

        Args:
            date: The date to query for
            limit: Maximum number of results

        Returns:
            List of LegalAct objects for the specified date
        """
        query = self._build_sparql_query(date, limit)

        try:
            params = {"query": query, "format": "json"}

            response = requests.post(
                self.SPARQL_ENDPOINT,
                data=params,
                timeout=60,
                headers={"Accept": "application/sparql-results+json"},
            )

            if response.status_code != 200:
                parsed_error = self._parse_error_response(response)
                logger.error(f"SPARQL query failed: {parsed_error}")

                # Log additional context for debugging if needed
                logger.debug(f"Full response text: {response.text[:1000]}")

                return []

            data = response.json()
            results = data.get("results", {}).get("bindings", [])

            legal_acts = []
            for result in results:
                legal_act = self._parse_sparql_json_result(result)
                if legal_act:
                    legal_acts.append(legal_act)

            logger.debug(f"Retrieved {len(legal_acts)} acts for {date.date()}")
            return legal_acts

        except requests.exceptions.Timeout as e:
            logger.error(
                f"SPARQL query timeout for date {date.date()}: Request took longer than 60 seconds"
            )
            raise EurLexServiceError(
                f"SPARQL query timeout for date {date.date()}: Request took longer than 60 seconds"
            ) from e

        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Connection error for SPARQL query on date {date.date()}: Unable to connect to EUR-Lex endpoint"
            )
            raise EurLexServiceError(
                f"Connection error for date {date.date()}: Unable to connect to EUR-Lex endpoint"
            ) from e

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Network error executing SPARQL query for date {date.date()}: {str(e)}"
            )
            raise EurLexServiceError(
                f"Network error for date {date.date()}: {str(e)}"
            ) from e

        except Exception as e:
            logger.error(
                f"Unexpected error executing SPARQL query for date {date.date()}: {str(e)}"
            )
            raise EurLexServiceError(
                f"SPARQL query failed for date {date.date()}: {str(e)}"
            ) from e

    def _build_sparql_query(self, date: datetime, limit: int = None) -> str:
        """
        Build the enhanced SPARQL query for retrieving works with associated metadata for a specific date.

        Args:
            date: The date to query for
            limit: Maximum number of results

        Returns:
            SPARQL query string with comprehensive metadata
            Metadata includes:
            - Expression URL (mandatory)
            - Title (English preferred, German as fallback only if no English exists)
            - PDF URL (optional)
            - Eurovoc labels (concatenated, in English, optional)
            - Document date (when the document was published, optional)
            - Publication date (when the document was published in the Official Journal, mandatory)
            - Effect date (when the document came into force, optional)
            - End validity date (when the document stopped being valid, optional)
            - Notification date (when the document was notified, optional)
        """
        return f"""
        PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT 
            ?work ?title ?pdf_url
            (GROUP_CONCAT(DISTINCT ?eurovoc_label; separator="|") AS ?all_eurovoc_labels)
            ?document_date ?publication_date ?effect_date ?end_validity_date ?notification_date
            ?document_type ?document_type_label
            ?oj_series
            
        WHERE {{
            # Core query - filter by specific publication date
            ?work cdm:official-journal-act_date_publication ?publication_date .
            FILTER(?publication_date = "{date.date()}"^^xsd:date)
            
            # === REQUIRED: Title - English preferred, German as backup ===
            {{
                # Try English first
                ?expression cdm:expression_belongs_to_work ?work .
                ?expression cdm:expression_title ?title .
                ?expression cdm:expression_uses_language ?lang_concept .
                ?lang_concept dc:identifier "ENG" .
            }}
            UNION
            {{
                # Use German only if no English exists for this work
                ?expression cdm:expression_belongs_to_work ?work .
                ?expression cdm:expression_title ?title .
                ?expression cdm:expression_uses_language ?lang_concept .
                ?lang_concept dc:identifier "DEU" .
                
                # Only if no English expression exists
                FILTER NOT EXISTS {{
                    ?eng_expression cdm:expression_belongs_to_work ?work .
                    ?eng_expression cdm:expression_uses_language ?eng_lang .
                    ?eng_lang dc:identifier "ENG" .
                }}
            }}
            
            # === DATES ===
            OPTIONAL {{ ?work cdm:work_date_document ?document_date }}
            OPTIONAL {{ ?work cdm:resource_legal_date_entry-into-force ?effect_date }}
            OPTIONAL {{ ?work cdm:resource_legal_date_end-of-validity ?end_validity_date }}
            OPTIONAL {{ ?work cdm:resource_legal_date_notification ?notification_date }}
            
            # Get PDF URL for the selected expression
            OPTIONAL {{
                ?manifestation cdm:manifestation_manifests_expression ?expression .
                ?manifestation cdm:manifestation_type "pdfa2a"^^xsd:string .
                ?item cdm:item_belongs_to_manifestation ?manifestation .
                BIND(?item AS ?pdf_url)
            }}
            
            # Get English EUROVOC descriptors
            OPTIONAL {{
                ?work cdm:work_is_about_concept_eurovoc ?eurovoc_concept .
                ?eurovoc_concept skos:prefLabel ?eurovoc_label .
                FILTER(lang(?eurovoc_label) = "en")
            }}
            
            # === DOCUMENT TYPE IDENTIFICATION ===
            # Get document type (directive, regulation, etc.)
            OPTIONAL {{
                ?work cdm:work_has_resource-type ?document_type .
                ?document_type skos:prefLabel ?document_type_label .
                FILTER(lang(?document_type_label) = "en")
            }}
            
            # === OFFICIAL JOURNAL SERIES IDENTIFICATION ===
            # Get OJ series (L-series for legislation, C-series for communication)
            OPTIONAL {{
                ?work cdm:official-journal-act_part_of_collection_document ?oj_series .
            }}
            
        }}
        GROUP BY ?work ?title ?pdf_url ?document_date ?publication_date ?effect_date ?end_validity_date ?notification_date ?document_type ?document_type_label ?oj_series  
        ORDER BY DESC(?publication_date)
        {f"LIMIT {limit}" if limit else ""}
        """

    def _build_sparql_query_retrieve_single_act(self, expression_url: str) -> str:
        """
        Build a SPARQL query to fetch a single work by its expression URL with full metadata.

        Args:
            expression_url: EUR-Lex work/expression URL (e.g., http://publications.europa.eu/resource/cellar/....)

        Returns:
            SPARQL query string
        """
        return f"""
        PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT 
            ?work ?title ?pdf_url
            (GROUP_CONCAT(DISTINCT ?eurovoc_label; separator="|") AS ?all_eurovoc_labels)
            ?document_date ?publication_date ?effect_date ?end_validity_date ?notification_date
            ?document_type ?document_type_label
            ?oj_series
        WHERE {{
            VALUES ?work {{ <{expression_url}> }}

            # === REQUIRED: Title - English preferred, German as backup ===
            {{
                # Try English first
                ?expression cdm:expression_belongs_to_work ?work .
                ?expression cdm:expression_title ?title .
                ?expression cdm:expression_uses_language ?lang_concept .
                ?lang_concept dc:identifier "ENG" .
            }}
            UNION
            {{
                # Use German only if no English exists for this work
                ?expression cdm:expression_belongs_to_work ?work .
                ?expression cdm:expression_title ?title .
                ?expression cdm:expression_uses_language ?lang_concept .
                ?lang_concept dc:identifier "DEU" .
                FILTER NOT EXISTS {{
                    ?eng_expression cdm:expression_belongs_to_work ?work .
                    ?eng_expression cdm:expression_uses_language ?eng_lang .
                    ?eng_lang dc:identifier "ENG" .
                }}
            }}

            # === DATES ===
            OPTIONAL {{ ?work cdm:work_date_document ?document_date }}
            OPTIONAL {{ ?work cdm:resource_legal_date_entry-into-force ?effect_date }}
            OPTIONAL {{ ?work cdm:resource_legal_date_end-of-validity ?end_validity_date }}
            OPTIONAL {{ ?work cdm:resource_legal_date_notification ?notification_date }}
            OPTIONAL {{ ?work cdm:official-journal-act_date_publication ?publication_date }}

            # Get PDF URL for the selected expression
            OPTIONAL {{
                ?manifestation cdm:manifestation_manifests_expression ?expression .
                ?manifestation cdm:manifestation_type "pdfa2a"^^xsd:string .
                ?item cdm:item_belongs_to_manifestation ?manifestation .
                BIND(?item AS ?pdf_url)
            }}

            # Get English EUROVOC descriptors
            OPTIONAL {{
                ?work cdm:work_is_about_concept_eurovoc ?eurovoc_concept .
                ?eurovoc_concept skos:prefLabel ?eurovoc_label .
                FILTER(lang(?eurovoc_label) = "en")
            }}

            # === DOCUMENT TYPE IDENTIFICATION ===
            OPTIONAL {{
                ?work cdm:work_has_resource-type ?document_type .
                ?document_type skos:prefLabel ?document_type_label .
                FILTER(lang(?document_type_label) = "en")
            }}

            # === OFFICIAL JOURNAL SERIES IDENTIFICATION ===
            OPTIONAL {{
                ?work cdm:official-journal-act_part_of_collection_document ?oj_series .
            }}
        }}
        GROUP BY ?work ?title ?pdf_url ?document_date ?publication_date ?effect_date ?end_validity_date ?notification_date ?document_type ?document_type_label ?oj_series
        LIMIT 1
        """

    def get_legal_act_by_expression_url(
        self, expression_url: str
    ) -> Optional[LegalAct]:
        """
        Retrieve a single legal act by its EUR-Lex expression URL.

        Args:
            expression_url: EUR-Lex work/expression URL

        Returns:
            LegalAct if found, otherwise None
        """
        query = self._build_sparql_query_retrieve_single_act(expression_url)

        try:
            params = {"query": query, "format": "json"}
            response = requests.post(
                self.SPARQL_ENDPOINT,
                data=params,
                timeout=60,
                headers={"Accept": "application/sparql-results+json"},
            )

            if response.status_code != 200:
                parsed_error = self._parse_error_response(response)
                logger.error(f"SPARQL single-work query failed: {parsed_error}")
                return None

            data = response.json()
            results = data.get("results", {}).get("bindings", [])
            if not results:
                return None

            return self._parse_sparql_json_result(results[0])

        except Exception as e:
            logger.error(f"Error querying single work '{expression_url}': {e}")
            return None

    def _parse_sparql_json_result(self, result: dict) -> Optional[LegalAct]:
        """
        Parse a SPARQL JSON result into a LegalAct object.

        Args:
            result: JSON result from SPARQL endpoint

        Returns:
            LegalAct object or None if parsing fails
        """
        try:
            # Extract values from JSON result structure
            expression_url = result.get("work", {}).get("value", "")
            title = result.get("title", {}).get("value", "N/A")
            pdf_url = result.get("pdf_url", {}).get("value", "")
            eurovoc_labels = result.get("all_eurovoc_labels", {}).get("value", None)
            if eurovoc_labels:
                # Split the pipe-separated string into a list
                eurovoc_labels = eurovoc_labels.split("|")
            else:
                eurovoc_labels = None

            # Parse all date fields
            pub_date_str = result.get("publication_date", {}).get("value", "")
            publication_date = parse_date_string(pub_date_str)

            doc_date_str = result.get("document_date", {}).get("value", "")
            document_date = parse_date_string(doc_date_str) if doc_date_str else None

            effect_date_str = result.get("effect_date", {}).get("value", "")
            effect_date = (
                parse_date_string(effect_date_str) if effect_date_str else None
            )

            end_date_str = result.get("end_validity_date", {}).get("value", "")
            end_validity_date = (
                parse_date_string(end_date_str) if end_date_str else None
            )

            notif_date_str = result.get("notification_date", {}).get("value", "")
            notification_date = (
                parse_date_string(notif_date_str) if notif_date_str else None
            )

            document_type = result.get("document_type", {}).get("value", None)
            raw_document_type_label = result.get("document_type_label", {}).get(
                "value", DocumentTypeLabel.UNKNOWN.value
            )

            # Check if the document type label exists in our enum
            if raw_document_type_label in self.VALID_DOCUMENT_TYPE_LABELS:
                document_type_label = DocumentTypeLabel(raw_document_type_label)
            else:
                logger.warning(
                    f"Unknown document type label '{raw_document_type_label}' mapped to OTHER"
                )
                document_type_label = DocumentTypeLabel.OTHER

            # Extract and process OJ series - transform URI directly to label
            oj_series_uri = result.get("oj_series", {}).get("value", None)
            oj_series_label = OfficialJournalSeries.from_eur_lex_uri(oj_series_uri)

            return LegalAct(
                expression_url=expression_url,
                title=title,
                pdf_url=pdf_url,
                eurovoc_labels=eurovoc_labels,
                document_date=document_date,
                publication_date=publication_date,
                effect_date=effect_date,
                end_validity_date=end_validity_date,
                notification_date=notification_date,
                document_type=document_type,
                document_type_label=document_type_label,
                oj_series_label=oj_series_label,
            )

        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse SPARQL JSON result: {e}")
            return None

    def _parse_sparql_row(self, row: ResultRow) -> Optional[LegalAct]:
        """
        Legacy method - kept for backward compatibility but not used.
        The new implementation uses _parse_sparql_json_result instead.
        """
        logger.warning("_parse_sparql_row called - this method is deprecated")
        return None


# Create a singleton instance to be imported
eur_lex_service = EurLexService()
