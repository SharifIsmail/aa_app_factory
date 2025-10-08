import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from loguru import logger

from service.law_core.chunker.models import (
    DocumentChunk,
)
from service.law_core.relevancy_classification.relevancy_prompts import (
    CHUNK_FACTFULNESS_ASSESSMENT_PROMPT,
)
from service.law_core.tools.llm_completion_tool import LLMCompletionTool
from service.models import (
    Citation,
    Factfulness,
    TeamDescription,
    TeamRelevancy,
)

# Configuration: Fallback behavior when LLM parsing fails or errors occur
FACTUALITY_FALLBACK_VALUE = False  # False = mark as not factual, True = mark as factual


class CitationTool(ABC):
    """Abstract base class for citation tools that ground global reasoning with chunk-level citations."""

    @abstractmethod
    def cite(
        self,
        team_relevancy: TeamRelevancy,
        chunks: List[DocumentChunk],
        team_profile: Optional[TeamDescription] = None,
        company_description: Optional[str] = None,
        max_workers: int = 3,
    ) -> List[Citation]:
        """Generate citations for team relevancies by analyzing global reasoning factfulness with pre-chunked documents."""
        pass


class LLMCitationTool(CitationTool):
    """LLM-based citation tool that generates citations for pre-chunked documents.

    This implementation:
    - Accepts pre-chunked documents (chunking done separately for efficiency)
    - Performs factfulness assessment for each individual chunk using LLM
    - Maps the global reasoning back to the document chunks deemed factual
    - Enables parallel processing of chunks across multiple teams
    """

    def __init__(
        self,
        llm_completion_tool: LLMCompletionTool,
        max_retries: int = 2,
    ):
        """Initialize the LLM citation tool.

        Args:
            llm_completion_tool: The LLM completion tool for making queries
            max_retries: Maximum number of retries if LLM response is malformed
        """
        self.llm_completion_tool = llm_completion_tool
        self.max_retries = max_retries

    def _build_factfulness_prompt(
        self,
        chunk: DocumentChunk,
        global_claim: str,
        team_profile: Optional[TeamDescription] = None,
        company_description: Optional[str] = None,
    ) -> str:
        """Build the prompt for LLM factfulness assessment."""
        team_profile_str = (
            team_profile.model_dump_json(indent=2) if team_profile else "Not provided"
        )
        company_desc = company_description or "Not provided"

        return CHUNK_FACTFULNESS_ASSESSMENT_PROMPT.format(
            global_claim=global_claim,
            chunk_content=chunk.content,
            team_profile=team_profile_str,
            company_description=company_desc,
        )

    def _parse_factfulness_response(self, raw_response: str) -> Tuple[str, bool | None]:
        """Parse the LLM response to extract reasoning and factfulness decision.

        Args:
            raw_response: Raw response from the LLM

        Returns:
            Tuple of (reasoning: str, is_factual: bool | fallback_to_false)
        """
        if not raw_response:
            return "", None

        decision_match = re.search(
            r"#DECISION:\s*(.*?)(?=#RESULT:|$)", raw_response, re.DOTALL | re.IGNORECASE
        )
        reasoning = decision_match.group(1).strip() if decision_match else ""

        result_match = re.search(r"#RESULT:\s*(YES|NO)", raw_response, re.IGNORECASE)
        if not result_match:
            logger.warning(
                f"Could not parse RESULT from LLM factfulness response: {raw_response[:200]}..."
            )
            # NOTE Fallback: use configured fallback mechanism if we can't parse the result
            return reasoning, FACTUALITY_FALLBACK_VALUE

        result_str = result_match.group(1).upper()
        is_factual = result_str == "YES"

        return reasoning, is_factual

    def _check_factfulness_with_llm(
        self,
        chunk: DocumentChunk,
        global_reasoning: str,
        team_profile: Optional[TeamDescription] = None,
        company_description: Optional[str] = None,
    ) -> Factfulness:
        """Checks factfulness of a chunk with an LLM using retries for malformed responses.

        Args:
            chunk: The document chunk to assess
            global_reasoning: The global claim about the legal act

        Returns:
            Factfulness object with assessment results. Fallback for factuality is False in case of errors.
        """
        prompt = self._build_factfulness_prompt(
            chunk=chunk,
            global_claim=global_reasoning,
            team_profile=team_profile,
            company_description=company_description,
        )

        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Querying LLM for chunk factfulness (attempt {attempt + 1})"
                )

                raw_response = self.llm_completion_tool.forward(
                    prompt=prompt,
                    purpose=f"Assess chunk factfulness for order_index: {chunk.order_index}",
                )

                reasoning, is_factual = self._parse_factfulness_response(raw_response)

                if is_factual is not None:
                    logger.debug(
                        f"Chunk {chunk.order_index} assessed as: {'FACTUAL' if is_factual else 'NOT FACTUAL'}"
                    )
                    return Factfulness(
                        is_factual=is_factual,
                        local_reasoning=reasoning,
                    )

                logger.warning(
                    f"Failed to parse LLM factfulness response on attempt {attempt + 1}"
                )

            except Exception as e:
                logger.error(
                    f"Error querying LLM for chunk factfulness on attempt {attempt + 1}: {e}"
                )
                last_exception = e
                if attempt == self.max_retries:
                    break

        # NOTE Fallback: use configured fallback mechanism if all retries failed
        fallback_status = "factual" if FACTUALITY_FALLBACK_VALUE else "not factual"
        logger.error(
            f"All retries failed for chunk {chunk.order_index}, marking as {fallback_status}"
        )
        error_message = (
            f"LLM factfulness assessment failed after {self.max_retries + 1} attempts"
        )
        if last_exception:
            error_message += f": {str(last_exception)}"

        return Factfulness(
            is_factual=FACTUALITY_FALLBACK_VALUE,
            local_reasoning=error_message,
        )

    def _cite_with_single_chunk(
        self,
        team_relevancy: TeamRelevancy,
        legal_act_chunk: DocumentChunk,
        team_profile: Optional[TeamDescription] = None,
        company_description: Optional[str] = None,
    ) -> Citation:
        """Generates one citation with a single chunk if factfulness is determined."""

        return Citation(
            chunk=legal_act_chunk,
            factfulness=self._check_factfulness_with_llm(
                legal_act_chunk,
                team_relevancy.reasoning,
                team_profile=team_profile,
                company_description=company_description,
            ),
        )

    def cite(
        self,
        team_relevancy: TeamRelevancy,
        chunks: List[DocumentChunk],
        team_profile: Optional[TeamDescription] = None,
        company_description: Optional[str] = None,
        max_workers: int = 3,
    ) -> List[Citation]:
        """Generate citations for pre-chunked documents for a team profile with parallel processing."""

        if not team_relevancy.is_relevant:
            # Return empty list for non-relevant teams to optimize memory usage and api calls.
            return []

        citations = []

        # Process chunks in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(chunks), max_workers)) as executor:
            # Submit all chunk processing tasks
            chunk_processing_tasks = {
                executor.submit(
                    self._cite_with_single_chunk,
                    team_relevancy,
                    chunk,
                    team_profile,
                    company_description,
                ): chunk
                for chunk in chunks
            }

            # Collect results as they complete, maintaining order by chunk.order_index
            chunk_results = {}
            for completed_task in as_completed(chunk_processing_tasks):
                chunk = chunk_processing_tasks[completed_task]
                try:
                    citation = completed_task.result()
                    chunk_results[chunk.order_index] = citation
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk.order_index}: {e}")
                    # Create error citation
                    error_citation = Citation(
                        chunk=chunk,
                        # NOTE Fallback: use configured fallback mechanism if error occurs
                        factfulness=Factfulness(
                            is_factual=FACTUALITY_FALLBACK_VALUE,
                            local_reasoning=f"Error processing chunk {chunk.order_index}: {e}",
                        ),
                    )
                    chunk_results[chunk.order_index] = error_citation

            # Sort citations by chunk order to maintain document structure
            citations = [chunk_results[i] for i in sorted(chunk_results.keys())]

        logger.info(
            f"Generated {len(citations)} citations out of {len(chunks)} chunks for team '{team_relevancy.team_name}'"
        )
        return citations


# Example usage - Efficient chunking and parallel processing:
#
# # 1. Chunk once per legal act (not per team)
# chunker = SomeChunker(...)
# chunks = chunker.chunk(legal_act.full_text)  # Done once!
#
# # 2. Create citation tool (reusable across teams)
# llm_tool = LLMCompletionTool(...)
# citation_tool = LLMCitationTool(
#     llm_completion_tool=llm_tool,
#     max_retries=2
# )
#
# # 3. Process multiple teams in parallel using same chunks
# citations_relevant_team = citation_tool.cite(
#     team_relevancy=relevant_team_relevancy,  # is_relevant=True
#     chunks=chunks,  # Reuse pre-chunked data
#     team_profile=engineering_team,
#     company_description="Company ABC"
# )
# # Returns: [Citation(...), Citation(...), ...] with factfulness assessments
#
# citations_non_relevant_team = citation_tool.cite(
#     team_relevancy=non_relevant_team_relevancy,  # is_relevant=False
#     chunks=chunks,  # Same chunks, different team context
#     team_profile=legal_team,
#     company_description="Company ABC"
# )
# # Returns: [] (empty list) - optimized for memory usage
#
# # Benefits:
# # - Chunk once, use many times (efficient)
# # - Parallel processing of teams possible
# # - Memory optimized: empty lists for non-relevant teams
# # - Each citation contains: chunk (with order_index), factfulness
# # - Configurable fallback behavior via FACTUALITY_FALLBACK_VALUE constant
