"""
EUR-Lex Document Chunker

This module provides functionality to semantically chunk EUR-Lex legal documents
based on their hierarchical structure.
"""

import json
import re
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from loguru import logger

from service.law_core.chunker.chunker import Chunker
from service.law_core.chunker.models import ChunkType, DocumentChunk


class EurLexChunker(Chunker):
    """
    Semantic chunker for EUR-Lex legal documents.
    """

    def __init__(self) -> None:
        # Enhanced patterns for different document elements
        self.patterns = {
            # Regulation/directive/decision title with year and number
            "regulation_title": re.compile(
                r"((?:COMMISSION\s+(?:IMPLEMENTING\s+)?|)(?:REGULATION|DIRECTIVE|DECISION)\s+\([^)]+\)\s+\d+/\d+.*?(?:OF\s+THE\s+(?:EUROPEAN\s+COMMISSION|EUROPEAN\s+PARLIAMENT\s+AND\s+OF\s+THE\s+COUNCIL))?)",
                re.IGNORECASE,
            ),
            # Communication title pattern
            "communication_title": re.compile(
                r"^COMMUNICATION FROM THE (?:COMMISSION|EUROPEAN COMMISSION)",
                re.MULTILINE,
            ),
            # Document reference pattern (e.g., "(C/2025/595)")
            "document_reference": re.compile(r"^\([A-Z]+/\d{4}/\d+\)$", re.MULTILINE),
            # Date pattern (e.g., "of 4 August 2025")
            "date_pattern": re.compile(r"of\s+\d+\s+\w+\s+\d{4}"),
            # Subject line (usually starts with lowercase and describes action)
            "subject_line": re.compile(r"^[a-z][^.]*$", re.MULTILINE),
            # Structured field patterns for communications (field_name: value or field_name on separate line)
            "structured_field": re.compile(r"^([A-Z][A-Za-z\s]+):\s*$", re.MULTILINE),
            "structured_field_name_only": re.compile(
                r"^(Issuing country|Subject of commemoration|Description of the design|Date of issue|Estimated number of coins to be issued)$",
                re.MULTILINE,
            ),
            "structured_field_value_only": re.compile(r"^:\s*(.+)$", re.MULTILINE),
            # EU Institution declaration (Commission, Parliament and Council)
            "commission_header": re.compile(
                r"THE EUROPEAN (?:COMMISSION|PARLIAMENT AND THE COUNCIL OF THE EUROPEAN UNION),",
                re.MULTILINE,
            ),
            # Legal basis patterns
            "having_regard": re.compile(r"^Having regard to", re.MULTILINE),
            "after_consulting": re.compile(r"^After consulting", re.MULTILINE),
            # Whereas clause
            "whereas": re.compile(r"^Whereas:", re.MULTILINE),
            # Individual whereas articles/numbered items (e.g., "(1)", "(2)", etc.)
            "whereas_article": re.compile(r"^\s*\((\d+)\)\s*$", re.MULTILINE),
            # Main section headers (e.g., "1. PROCEDURE", "2. PRODUCT CONCERNED")
            "main_section": re.compile(
                r"^\s*(\d+)\.\s+([A-Z][A-Z\s,&()-]+)(?:\s*$)", re.MULTILINE
            ),
            # Subsection headers (e.g., "1.1. Initiation", "1.2. Registration")
            "subsection": re.compile(
                r"^\s*(\d+)\.(\d+)\.\s+([A-Z][A-Za-z\s,&()-]+)(?:\s*$)", re.MULTILINE
            ),
            # Paragraphs in table format (e.g., "| (1) | content |")
            "paragraph_table": re.compile(r"^\s*\|\s*\((\d+)\)\s*\|", re.MULTILINE),
            # Regular paragraphs (simple numbered format)
            "paragraph_simple": re.compile(r"^\s*\((\d+)\)\s+", re.MULTILINE),
            # Inline footnote references (e.g., "( 1 )")
            "inline_footnote_ref": re.compile(r"^\s*\(\s*(\d+)\s*\)\s*$", re.MULTILINE),
            # Table rows (markdown-style tables)
            "table_row": re.compile(r"^\s*\|[^|]*\|", re.MULTILINE),
            "table_separator": re.compile(r"^\s*\|[\s\-|]+\|", re.MULTILINE),
            # Annex header
            "annex": re.compile(r"^ANNEX", re.MULTILINE),
            # Reference patterns (footnotes, citations)
            "footnote": re.compile(r"\(\d+\)"),
            "eli_reference": re.compile(r"ELI:\s*http://data\.europa\.eu/eli/"),
            # End markers
            "issn": re.compile(r"ISSN\s+\d{4}-\d{4}"),
        }

    def fetch_document(self, url: str) -> str:
        """
        Fetch a EUR-Lex document from the web and extract text content.

        Args:
            url: The EUR-Lex document URL

        Returns:
            Cleaned text content of the document
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Handle different URL formats - try to convert to document format if needed
            original_url = url
            if "cellar/" in url and not url.endswith("/DOC_1"):
                # Try to add the standard document suffix if missing
                if not any(
                    suffix in url
                    for suffix in [".0006.03/DOC_1", ".0001.03/DOC_1", "/DOC_"]
                ):
                    url = url + ".0006.03/DOC_1"

            logger.debug(f"Fetching EUR-Lex document: {url}")

            response = requests.get(url, headers=headers, timeout=30)

            # If the modified URL fails, try the original URL
            if response.status_code != 200 and url != original_url:
                logger.debug(f"Modified URL failed, trying original: {original_url}")
                response = requests.get(original_url, headers=headers, timeout=30)
                url = original_url

            response.raise_for_status()

            logger.debug(f"Fetched EUR-Lex document of length {len(response.content)}")

            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Check if we got an RDF response instead of HTML
            if soup.find("rdf:RDF"):
                # This is likely an RDF metadata response, try to get the actual document
                if not url.endswith("/DOC_1"):
                    document_url = url + ".0006.03/DOC_1"
                    logger.debug(
                        f"Got RDF response, trying document URL: {document_url}"
                    )
                    response = requests.get(document_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.content, "html.parser")

            # Remove unwanted elements
            for element in soup(
                ["script", "style", "nav", "header", "footer", "aside"]
            ):
                element.decompose()

            # Extract main content with improved fallback chain
            main_content = (
                soup.find("div", class_="eli-main-content")
                or soup.find("div", class_="eli-container")
                or soup.find("div", class_="eli-subdivision")
                or soup.find("main")
                or soup.find("article")
                or soup.find("div", class_="content")
                or soup.find("body")
            )

            if main_content:
                # Get text while preserving structure
                text = main_content.get_text(separator="\n", strip=True)

                # Clean up text
                lines = []
                for line in text.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("×"):  # Remove UI elements
                        lines.append(line)

                cleaned_text = "\n".join(lines)

                # Validate we got meaningful content
                if len(cleaned_text) < 100:
                    raise RuntimeError(
                        f"Document content too short ({len(cleaned_text)} chars), might be invalid"
                    )

                return cleaned_text
            else:
                raise RuntimeError(f"Could not find main content in the document {url}")

        except Exception as e:
            raise Exception(f"Error fetching document: {e}")

    def chunk_document(self, text: str) -> List[DocumentChunk]:
        """
        Chunk a EUR-Lex document into semantic sections.

        Args:
            text: The full document text

        Returns:
            List of DocumentChunk objects representing semantic sections
        """
        chunks = []
        lines = text.split("\n")

        # Identify document structure boundaries
        boundaries = self._identify_document_boundaries(text)

        # Determine document type globally
        is_communication = self.patterns["communication_title"].search(text) is not None

        # Process each major section
        for boundary in boundaries:
            section_chunks = self._process_section(
                text,
                lines,
                boundary["start"],
                boundary["end"],
                boundary["type"],
                is_communication,
            )
            chunks.extend(section_chunks)

        # Post-process chunks to fix positions and relationships
        chunks = self._post_process_chunks(chunks, lines)

        return chunks

    def _identify_document_boundaries(self, text: str) -> List[Dict]:
        """Identify major structural boundaries in the document."""
        lines = text.split("\n")
        boundaries = []

        # Track positions of major elements
        title_pos = None
        communication_title_pos = None
        commission_pos = None
        whereas_pos = None
        main_section_pos = None
        structured_fields_start = None
        annex_pos = None
        end_pos = len(lines)

        for i, line in enumerate(lines):
            # Document title (regulation/directive)
            if self.patterns["regulation_title"].search(line) and title_pos is None:
                title_pos = i

            # Communication title
            elif (
                self.patterns["communication_title"].search(line)
                and communication_title_pos is None
            ):
                communication_title_pos = i

            # Commission declaration
            elif (
                self.patterns["commission_header"].search(line)
                and commission_pos is None
            ):
                commission_pos = i

            # Whereas clause
            elif self.patterns["whereas"].search(line) and whereas_pos is None:
                whereas_pos = i

            # First main section
            elif (
                self.patterns["main_section"].search(line) and main_section_pos is None
            ):
                main_section_pos = i

            # Structured fields (for communications)
            elif (
                self.patterns["structured_field"].search(line)
                and structured_fields_start is None
                and communication_title_pos is not None
            ):
                structured_fields_start = i

            # Annex
            elif self.patterns["annex"].search(line) and annex_pos is None:
                annex_pos = i

        # Create boundary definitions
        current_pos = 0

        # Determine document type and create appropriate boundaries
        is_communication = communication_title_pos is not None

        if is_communication:
            # For communications: header -> main_content (including structured fields) -> references
            # Find where structured content might end (look for footnotes or references)
            structured_content_end = end_pos
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i].strip()
                if line and not (
                    self.patterns["eli_reference"].search(line)
                    or line.startswith("OJ ")
                    or "See" in line
                ):
                    structured_content_end = i + 1
                    break

            # Header section (title, subject, document reference)
            header_end = min(
                (communication_title_pos or 0) + 5,
                structured_fields_start or structured_content_end,
            )
            boundaries.append(
                {"type": "header", "start": current_pos, "end": header_end}
            )
            current_pos = header_end

            # Main content section (structured fields and content)
            if structured_content_end > current_pos:
                boundaries.append(
                    {
                        "type": "main_content",
                        "start": current_pos,
                        "end": structured_content_end,
                    }
                )
                current_pos = structured_content_end

            # References section (if any remaining content)
            if current_pos < end_pos:
                boundaries.append(
                    {"type": "references", "start": current_pos, "end": end_pos}
                )
        else:
            # Original logic for regulations/directives
            # Header section (title, date, subject)
            if commission_pos:
                boundaries.append(
                    {"type": "header", "start": current_pos, "end": commission_pos}
                )
                current_pos = commission_pos

            # Preamble section (commission + legal basis + whereas)
            if main_section_pos:
                boundaries.append(
                    {"type": "preamble", "start": current_pos, "end": main_section_pos}
                )
                current_pos = main_section_pos
            elif commission_pos and current_pos < end_pos:
                # If we have commission header but no main sections, create preamble section for the rest
                boundaries.append(
                    {"type": "preamble", "start": current_pos, "end": end_pos}
                )
                current_pos = end_pos

            # Main sections
            if annex_pos:
                boundaries.append(
                    {"type": "main_content", "start": current_pos, "end": annex_pos}
                )
                current_pos = annex_pos
            elif main_section_pos:
                boundaries.append(
                    {"type": "main_content", "start": current_pos, "end": end_pos}
                )
                current_pos = end_pos

            # Annex section
            if annex_pos:
                boundaries.append(
                    {"type": "annex", "start": current_pos, "end": end_pos}
                )

        # Fallback: if no boundaries were created, create a basic structure
        if not boundaries:
            # If we have a commission header, split around it
            if commission_pos:
                boundaries.append({"type": "header", "start": 0, "end": commission_pos})
                boundaries.append(
                    {"type": "preamble", "start": commission_pos, "end": end_pos}
                )
            else:
                # Minimal fallback: treat the whole document as main content for communications
                doc_type = "main_content" if is_communication else "preamble"
                boundaries.append({"type": doc_type, "start": 0, "end": end_pos})

        return boundaries

    def _process_section(
        self,
        text: str,
        lines: List[str],
        start: int,
        end: int,
        section_type: str,
        is_communication: bool = False,
    ) -> List[DocumentChunk]:
        """Process a major document section."""
        section_text = "\n".join(lines[start:end])

        if section_type == "header":
            return self._process_header_section(section_text, start)
        elif section_type == "preamble":
            return self._process_preamble_section(section_text, start)
        elif section_type == "main_content":
            return self._process_main_content_section(
                section_text, start, is_communication
            )
        elif section_type == "annex":
            return self._process_annex_section(section_text, start)
        elif section_type == "references":
            return self._process_references_section(section_text, start)

        return []

    def _process_header_section(
        self, text: str, start_line: int
    ) -> List[DocumentChunk]:
        """Process the document header section."""
        chunks = []
        lines = text.split("\n")
        current_pos = start_line

        # Check if this is a communication
        is_communication = self.patterns["communication_title"].search(text)

        if is_communication:
            # Process communication header
            content_parts: list[str] = []
            for line in lines:
                line = line.strip()
                if line:
                    # Communication title
                    if self.patterns["communication_title"].search(line):
                        title_chunk = DocumentChunk(
                            chunk_type=ChunkType.TITLE,
                            content=line,
                            title="Communication Title",
                            level=0,
                            start_pos=current_pos,
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(title_chunk)

                    # Document reference (e.g., "(C/2025/595)")
                    elif self.patterns["document_reference"].search(line):
                        ref_chunk = DocumentChunk(
                            chunk_type=ChunkType.REFERENCE,
                            content=line,
                            title="Document Reference",
                            level=0,
                            start_pos=current_pos,
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(ref_chunk)

                    # Subject line for communications (often longer descriptive text)
                    elif len(line) > 20 and not any(
                        p.search(line)
                        for p in [
                            self.patterns["communication_title"],
                            self.patterns["document_reference"],
                        ]
                    ):
                        subject_chunk = DocumentChunk(
                            chunk_type=ChunkType.SUBJECT,
                            content=line,
                            title="Subject",
                            level=0,
                            start_pos=current_pos,
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(subject_chunk)

                current_pos += 1
        else:
            # Original regulation/directive header processing
            # Extract regulation title
            title_match = self.patterns["regulation_title"].search(text)
            if title_match:
                title_chunk = DocumentChunk(
                    chunk_type=ChunkType.TITLE,
                    content=title_match.group(1),
                    title="Regulation Title",
                    level=0,
                    start_pos=current_pos,
                    order_index=-1,  # Placeholder
                )
                chunks.append(title_chunk)

            # Process remaining header content
            header_content_parts: list[str] = []
            for line in lines:
                line = line.strip()
                if line:
                    # Check for date
                    if self.patterns["date_pattern"].search(line):
                        if header_content_parts:
                            # Save accumulated content
                            header_chunk = DocumentChunk(
                                chunk_type=ChunkType.HEADER,
                                content="\n".join(header_content_parts),
                                level=0,
                                start_pos=current_pos,
                                order_index=-1,  # Placeholder
                            )
                            chunks.append(header_chunk)
                            header_content_parts = []

                        # Add date chunk
                        date_chunk = DocumentChunk(
                            chunk_type=ChunkType.DATE,
                            content=line,
                            level=0,
                            start_pos=current_pos,
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(date_chunk)

                    # Check for subject line (usually lowercase, descriptive)
                    elif self.patterns["subject_line"].match(line) and len(line) > 20:
                        subject_chunk = DocumentChunk(
                            chunk_type=ChunkType.SUBJECT,
                            content=line,
                            level=0,
                            start_pos=current_pos,
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(subject_chunk)

                    else:
                        header_content_parts.append(line)

                current_pos += 1

            # Add any remaining content
            if header_content_parts:
                header_chunk = DocumentChunk(
                    chunk_type=ChunkType.HEADER,
                    content="\n".join(header_content_parts),
                    level=0,
                    start_pos=current_pos,
                    order_index=-1,  # Placeholder
                )
                chunks.append(header_chunk)

        return chunks

    def _process_preamble_section(
        self, text: str, start_line: int
    ) -> List[DocumentChunk]:
        """Process the preamble section."""
        chunks = []
        lines = text.split("\n")
        current_pos = start_line
        current_content: list[str] = []
        current_type = ChunkType.PREAMBLE

        for line in lines:
            line = line.strip()
            if not line:
                current_pos += 1
                continue

            # Commission declaration
            if self.patterns["commission_header"].search(line):
                if current_content:
                    if current_type == ChunkType.WHEREAS:
                        # Use special whereas processing
                        whereas_content = "\n".join(current_content)
                        whereas_chunks = self._process_whereas_content(
                            whereas_content, current_pos - len(current_content)
                        )
                        chunks.extend(whereas_chunks)
                    else:
                        chunk = DocumentChunk(
                            chunk_type=current_type,
                            content="\n".join(current_content),
                            level=1,
                            start_pos=current_pos - len(current_content),
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(chunk)
                    current_content = []

                current_type = ChunkType.COMMISSION_DECLARATION
                current_content.append(line)

            # Legal basis
            elif self.patterns["having_regard"].search(line) or self.patterns[
                "after_consulting"
            ].search(line):
                if current_content and current_type != ChunkType.LEGAL_BASIS:
                    if current_type == ChunkType.WHEREAS:
                        # Use special whereas processing
                        whereas_content = "\n".join(current_content)
                        whereas_chunks = self._process_whereas_content(
                            whereas_content, current_pos - len(current_content)
                        )
                        chunks.extend(whereas_chunks)
                    else:
                        chunk = DocumentChunk(
                            chunk_type=current_type,
                            content="\n".join(current_content),
                            level=1,
                            start_pos=current_pos - len(current_content),
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(chunk)
                    current_content = []

                current_type = ChunkType.LEGAL_BASIS
                current_content.append(line)

            # Whereas clause
            elif self.patterns["whereas"].search(line):
                if current_content:
                    if current_type == ChunkType.WHEREAS:
                        # Use special whereas processing
                        whereas_content = "\n".join(current_content)
                        whereas_chunks = self._process_whereas_content(
                            whereas_content, current_pos - len(current_content)
                        )
                        chunks.extend(whereas_chunks)
                    else:
                        chunk = DocumentChunk(
                            chunk_type=current_type,
                            content="\n".join(current_content),
                            level=1,
                            start_pos=current_pos - len(current_content),
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(chunk)
                    current_content = []

                # Start collecting whereas content for special processing
                current_type = ChunkType.WHEREAS
                current_content.append(line)

            else:
                current_content.append(line)

            current_pos += 1

        # Add final content
        if current_content:
            if current_type == ChunkType.WHEREAS:
                # Use special whereas processing
                whereas_content = "\n".join(current_content)
                whereas_chunks = self._process_whereas_content(
                    whereas_content, current_pos - len(current_content)
                )
                chunks.extend(whereas_chunks)
            else:
                chunk = DocumentChunk(
                    chunk_type=current_type,
                    content="\n".join(current_content),
                    level=1,
                    start_pos=current_pos - len(current_content),
                    order_index=-1,  # Placeholder
                )
                chunks.append(chunk)

        return chunks

    def _process_whereas_content(
        self, whereas_text: str, start_line: int
    ) -> List[DocumentChunk]:
        """
        Process WHEREAS content and split it into individual chunks per numbered article.

        Args:
            whereas_text: The complete WHEREAS section text
            start_line: Starting line number for positioning

        Returns:
            List of DocumentChunk objects for each WHEREAS article
        """
        chunks = []
        lines = whereas_text.split("\n")

        # Find all whereas article markers
        article_positions: List[Dict[str, int | str]] = []
        for i, line in enumerate(lines):
            match = self.patterns["whereas_article"].match(line.strip())
            if match:
                article_num = match.group(1)
                article_positions.append({"line": i, "number": article_num})

        # If no articles found, return the whole content as a single chunk
        if not article_positions:
            chunk = DocumentChunk(
                chunk_type=ChunkType.WHEREAS,
                content=whereas_text.strip(),
                level=1,
                start_pos=start_line,
                title="Whereas clause",
                order_index=-1,  # Placeholder
            )
            chunks.append(chunk)
            return chunks

        # Process each article
        for i, article_pos in enumerate(article_positions):
            article_num = str(article_pos["number"])
            article_start_line = int(article_pos["line"])

            # Determine article end (next article or end of content)
            if i + 1 < len(article_positions):
                article_end_line = int(article_positions[i + 1]["line"])
            else:
                article_end_line = len(lines)

            # Extract article content
            article_lines = lines[article_start_line:article_end_line]
            article_content = "\n".join(article_lines).strip()

            # Create chunk for this article
            if article_content:
                chunk = DocumentChunk(
                    chunk_type=ChunkType.WHEREAS,
                    content=article_content,
                    paragraph_number=article_num,
                    level=2,
                    start_pos=start_line + article_start_line,
                    title=f"Whereas article ({article_num})",
                    order_index=-1,  # Placeholder
                )
                chunks.append(chunk)

        return chunks

    def _process_main_content_section(
        self, text: str, start_line: int, is_communication: bool = False
    ) -> List[DocumentChunk]:
        """Process main numbered sections and their subsections."""
        chunks = []

        if is_communication:
            # For communications, process structured fields and content
            return self._process_communication_content(text, start_line)

        # Original processing for regulations/directives
        # Find all main sections
        main_sections = list(self.patterns["main_section"].finditer(text))
        lines = text.split("\n")

        for i, section_match in enumerate(main_sections):
            section_num = section_match.group(1)
            section_title = section_match.group(2).strip()

            # Determine section boundaries
            section_start_line = text[: section_match.start()].count("\n")
            if i + 1 < len(main_sections):
                section_end_line = text[: main_sections[i + 1].start()].count("\n")
            else:
                section_end_line = len(lines)

            section_text = "\n".join(lines[section_start_line:section_end_line])

            # Create main section chunk
            main_chunk = DocumentChunk(
                chunk_type=ChunkType.MAIN_SECTION,
                content=section_text,
                section_number=section_num,
                title=section_title,
                level=1,
                start_pos=start_line + section_start_line,
                order_index=-1,  # Placeholder
            )
            chunks.append(main_chunk)

            # Process subsections and paragraphs within this section
            sub_chunks = self._process_section_content(
                section_text, section_num, start_line + section_start_line
            )
            chunks.extend(sub_chunks)

        return chunks

    def _process_section_content(
        self, section_text: str, section_num: str, start_line: int
    ) -> List[DocumentChunk]:
        """Process subsections and paragraphs within a main section."""
        chunks = []

        # Find subsections
        subsections = list(self.patterns["subsection"].finditer(section_text))
        lines = section_text.split("\n")

        if subsections:
            # Process each subsection
            for i, subsection_match in enumerate(subsections):
                subsection_num = (
                    f"{subsection_match.group(1)}.{subsection_match.group(2)}"
                )
                subsection_title = subsection_match.group(3).strip()

                # Determine subsection boundaries
                subsection_start_line = section_text[: subsection_match.start()].count(
                    "\n"
                )
                if i + 1 < len(subsections):
                    subsection_end_line = section_text[
                        : subsections[i + 1].start()
                    ].count("\n")
                else:
                    subsection_end_line = len(lines)

                subsection_text = "\n".join(
                    lines[subsection_start_line:subsection_end_line]
                )

                # Create subsection chunk
                subsection_chunk = DocumentChunk(
                    chunk_type=ChunkType.SUBSECTION,
                    content=subsection_text,
                    section_number=section_num,
                    subsection_number=subsection_num,
                    title=subsection_title,
                    level=2,
                    start_pos=start_line + subsection_start_line,
                    order_index=-1,  # Placeholder
                )
                chunks.append(subsection_chunk)

                # Process paragraphs within subsection
                para_chunks = self._process_paragraphs(
                    subsection_text,
                    section_num,
                    subsection_num,
                    start_line + subsection_start_line,
                )
                chunks.extend(para_chunks)
        else:
            # No subsections, process paragraphs directly in the main section
            para_chunks = self._process_paragraphs(
                section_text, section_num, None, start_line
            )
            chunks.extend(para_chunks)

        return chunks

    def _process_paragraphs(
        self,
        text: str,
        section_num: str,
        subsection_num: Optional[str],
        start_line: int,
    ) -> List[DocumentChunk]:
        """Process numbered paragraphs within a section."""
        chunks: List[DocumentChunk] = []

        # Try table format first (| (1) | content |)
        paragraphs = list(self.patterns["paragraph_table"].finditer(text))

        # If no table format, try simple format
        if not paragraphs:
            paragraphs = list(self.patterns["paragraph_simple"].finditer(text))

        if not paragraphs:
            return chunks

        lines = text.split("\n")

        for i, para_match in enumerate(paragraphs):
            para_num = para_match.group(1)

            # Determine paragraph boundaries
            para_start_line = text[: para_match.start()].count("\n")
            if i + 1 < len(paragraphs):
                para_end_line = text[: paragraphs[i + 1].start()].count("\n")
            else:
                para_end_line = len(lines)

            para_text = "\n".join(lines[para_start_line:para_end_line])

            # Clean paragraph text (remove table formatting)
            cleaned_text = self._clean_paragraph_text(para_text)

            if cleaned_text.strip():
                para_chunk = DocumentChunk(
                    chunk_type=ChunkType.PARAGRAPH,
                    content=cleaned_text,
                    section_number=section_num,
                    subsection_number=subsection_num,
                    paragraph_number=para_num,
                    level=3,
                    start_pos=start_line + para_start_line,
                    order_index=-1,  # Placeholder
                )
                chunks.append(para_chunk)

        return chunks

    def _process_annex_section(self, text: str, start_line: int) -> List[DocumentChunk]:
        """Process annex sections."""
        chunks = []

        # Check if this is a table-based annex
        if self.patterns["table_row"].search(text):
            # Process as table
            table_chunk = DocumentChunk(
                chunk_type=ChunkType.ANNEX,
                content=text.strip(),
                title="ANNEX",
                level=1,
                start_pos=start_line,
                metadata={"content_type": "table"},
                order_index=-1,  # Placeholder
            )
            chunks.append(table_chunk)
        else:
            # Process as regular text sections
            parts = re.split(r"\n\s*\n", text)
            current_pos = start_line

            for part in parts:
                if part.strip():
                    chunk = DocumentChunk(
                        chunk_type=ChunkType.ANNEX,
                        content=part.strip(),
                        level=1,
                        start_pos=current_pos,
                        order_index=-1,  # Placeholder
                    )
                    chunks.append(chunk)
                    current_pos += part.count("\n") + 2

        return chunks

    def _process_communication_content(
        self, text: str, start_line: int
    ) -> List[DocumentChunk]:
        """Process content for communication documents with structured fields."""
        chunks = []
        lines = text.split("\n")
        current_pos = start_line
        current_content: list[str] = []
        current_field_name = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Skip empty lines in the loop but count them for positioning
            if not line_stripped:
                current_pos += 1
                continue

            # Check if this is a structured field header (e.g., "Issuing country:")
            field_match = self.patterns["structured_field"].search(line_stripped)
            if field_match:
                # Save previous field content if any
                if current_content and current_field_name:
                    chunk = DocumentChunk(
                        chunk_type=ChunkType.PARAGRAPH,
                        content="\n".join(current_content),
                        title=current_field_name,
                        level=1,
                        start_pos=current_pos - len(current_content),
                        order_index=-1,  # Placeholder
                    )
                    chunks.append(chunk)
                    current_content = []

                # Start new field
                current_field_name = field_match.group(1).strip()
                current_content = [line_stripped]

            # Check if this is a field name without colon (e.g., "Issuing country")
            # followed by value line (e.g., ": Croatia")
            elif (
                self.patterns["structured_field_name_only"].search(line_stripped)
                and i + 1 < len(lines)
                and self.patterns["structured_field_value_only"].search(
                    lines[i + 1].strip()
                )
            ):
                # Save previous field content if any
                if current_content and current_field_name:
                    chunk = DocumentChunk(
                        chunk_type=ChunkType.PARAGRAPH,
                        content="\n".join(current_content),
                        title=current_field_name,
                        level=1,
                        start_pos=current_pos - len(current_content),
                        order_index=-1,  # Placeholder
                    )
                    chunks.append(chunk)
                    current_content = []

                # Start new field with both name and value
                field_name = line_stripped
                current_field_name = field_name
                next_line = lines[i + 1].strip()
                value_match = self.patterns["structured_field_value_only"].search(
                    next_line
                )
                if value_match:
                    field_value = value_match.group(1).strip()
                    current_content = [f"{field_name}: {field_value}"]
                else:
                    current_content = [line_stripped, next_line]

            # Check if this is a value line (starts with ":") - skip if already processed above
            elif (
                self.patterns["structured_field_value_only"].search(line_stripped)
                and i > 0
                and self.patterns["structured_field_name_only"].search(
                    lines[i - 1].strip()
                )
            ):
                # This line was already processed in the previous iteration
                pass

            # Check for inline footnote references (e.g., "( 1 )")
            elif self.patterns["inline_footnote_ref"].search(line_stripped):
                # Save current content if any
                if current_content:
                    if current_field_name:
                        chunk = DocumentChunk(
                            chunk_type=ChunkType.PARAGRAPH,
                            content="\n".join(current_content),
                            title=current_field_name,
                            level=1,
                            start_pos=current_pos - len(current_content),
                            order_index=-1,  # Placeholder
                        )
                    else:
                        chunk = DocumentChunk(
                            chunk_type=ChunkType.PARAGRAPH,
                            content="\n".join(current_content),
                            level=1,
                            start_pos=current_pos - len(current_content),
                            order_index=-1,  # Placeholder
                        )
                    chunks.append(chunk)
                    current_content = []
                    current_field_name = None

                # Create footnote reference chunk
                footnote_chunk = DocumentChunk(
                    chunk_type=ChunkType.REFERENCE,
                    content=line_stripped,
                    title="Footnote Reference",
                    level=2,
                    start_pos=current_pos,
                    order_index=-1,  # Placeholder
                )
                chunks.append(footnote_chunk)

            else:
                # Regular content line
                current_content.append(line_stripped)

            current_pos += 1

        # Add any remaining content
        if current_content:
            if current_field_name:
                chunk = DocumentChunk(
                    chunk_type=ChunkType.PARAGRAPH,
                    content="\n".join(current_content),
                    title=current_field_name,
                    level=1,
                    start_pos=current_pos - len(current_content),
                    order_index=-1,  # Placeholder
                )
            else:
                chunk = DocumentChunk(
                    chunk_type=ChunkType.PARAGRAPH,
                    content="\n".join(current_content),
                    level=1,
                    start_pos=current_pos - len(current_content),
                    order_index=-1,  # Placeholder
                )
            chunks.append(chunk)

        return chunks

    def _process_references_section(
        self, text: str, start_line: int
    ) -> List[DocumentChunk]:
        """Process references and footnotes section."""
        chunks = []
        lines = text.split("\n")
        current_pos = start_line
        current_content: list[str] = []

        for line in lines:
            line_stripped = line.strip()
            if line_stripped:
                # Check if this looks like a footnote or reference
                if (
                    self.patterns["eli_reference"].search(line_stripped)
                    or line_stripped.startswith("OJ ")
                    or line_stripped.startswith("See")
                ):
                    # Save any accumulated content first
                    if current_content:
                        chunk = DocumentChunk(
                            chunk_type=ChunkType.REFERENCE,
                            content="\n".join(current_content),
                            level=1,
                            start_pos=current_pos - len(current_content),
                            order_index=-1,  # Placeholder
                        )
                        chunks.append(chunk)
                        current_content = []

                    # Create reference chunk
                    ref_chunk = DocumentChunk(
                        chunk_type=ChunkType.REFERENCE,
                        content=line_stripped,
                        title="Reference",
                        level=1,
                        start_pos=current_pos,
                        order_index=-1,  # Placeholder
                    )
                    chunks.append(ref_chunk)
                else:
                    current_content.append(line_stripped)

            current_pos += 1

        # Add any remaining content
        if current_content:
            chunk = DocumentChunk(
                chunk_type=ChunkType.REFERENCE,
                content="\n".join(current_content),
                level=1,
                start_pos=current_pos - len(current_content),
                order_index=-1,  # Placeholder
            )
            chunks.append(chunk)

        return chunks

    def _clean_paragraph_text(self, text: str) -> str:
        """Clean paragraph text by removing table formatting."""
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip table separator lines
            if self.patterns["table_separator"].match(line):
                continue

            # Clean table cell content
            if line.strip().startswith("|") and line.strip().endswith("|"):
                # Extract content between pipes
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                # Join meaningful cells (skip empty ones and numbers-only)
                meaningful_cells = [
                    cell
                    for cell in cells
                    if cell and not cell.isdigit() and cell != "---"
                ]
                if meaningful_cells:
                    cleaned_lines.append(" ".join(meaningful_cells))
            else:
                if line.strip():
                    cleaned_lines.append(line.strip())

        return "\n".join(cleaned_lines)

    def _post_process_chunks(
        self, chunks: List[DocumentChunk], lines: List[str]
    ) -> List[DocumentChunk]:
        """Post-process chunks to fix positions and add metadata."""
        # Sort chunks by start position
        chunks.sort(key=lambda x: x.start_pos or 0)

        # Set end positions - create new instances since DocumentChunk is frozen
        updated_chunks = []
        for i, chunk in enumerate(chunks):
            if i + 1 < len(chunks):
                new_end_pos = chunks[i + 1].start_pos
            else:
                new_end_pos = len(lines)

            # Create new chunk with updated end_pos
            updated_chunk = DocumentChunk(
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                section_number=chunk.section_number,
                subsection_number=chunk.subsection_number,
                paragraph_number=chunk.paragraph_number,
                title=chunk.title,
                level=chunk.level,
                start_pos=chunk.start_pos,
                end_pos=new_end_pos,
                metadata=chunk.metadata,
                order_index=i,  # Set the final order index
            )
            updated_chunks.append(updated_chunk)

        chunks = updated_chunks

        return chunks

    def get_chunk_summary(self, chunks: List[DocumentChunk]) -> Dict[str, int]:
        """Get a summary of chunk types and counts."""
        summary: Dict[str, int] = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type.value
            summary[chunk_type] = summary.get(chunk_type, 0) + 1
        return summary

    def export_chunks_to_dict(self, chunks: List[DocumentChunk]) -> List[Dict]:
        """Export chunks to dictionary format."""
        return [chunk.to_dict() for chunk in chunks]

    def export_chunks_to_json(
        self, chunks: List[DocumentChunk], filename: Optional[str] = None
    ) -> str:
        """Export chunks to JSON format."""
        data = {
            "total_chunks": len(chunks),
            "chunk_summary": self.get_chunk_summary(chunks),
            "chunks": self.export_chunks_to_dict(chunks),
        }

        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

    def chunk_from_url(self, url: str) -> List[DocumentChunk]:
        """
        Fetch and chunk an EUR-Lex document from a URL.

        Args:
            url: The EUR-Lex document URL

        Returns:
            List of DocumentChunk objects
        """
        text = self.fetch_document(url)
        logger.debug(f"Fetched document from {url} with {len(text)} characters.")
        # Chunk document
        chunks = self.chunk_document(text)

        return chunks

    def _join_chunks_on(self) -> str:
        return "\n\n"
