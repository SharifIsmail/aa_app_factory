"""Fuzzy search utilities for tools that need hybrid scoring functionality."""

from thefuzz import fuzz


class FuzzySearchConfig:
    """Configuration for fuzzy search parameters."""

    def __init__(
        self,
        threshold_high: float = 0.8,
        threshold_medium: float = 0.6,
        threshold_low: float = 0.4,
        token_weight: float = 0.5,
        fuzzy_weight: float = 0.5,
    ) -> None:
        """
        Initialize fuzzy search configuration.
        """
        self.THRESHOLD_HIGH = threshold_high
        self.THRESHOLD_MEDIUM = threshold_medium
        self.THRESHOLD_LOW = threshold_low
        self.TOKEN_WEIGHT = token_weight
        self.FUZZY_WEIGHT = fuzzy_weight
        self.validate_weights()

    def validate_weights(self) -> None:
        """
        Validate that TOKEN_WEIGHT and FUZZY_WEIGHT sum to 1.0.
        """
        total_weight = self.TOKEN_WEIGHT + self.FUZZY_WEIGHT
        tolerance = 1e-10  # Small tolerance for floating point precision

        if abs(total_weight - 1.0) > tolerance:
            raise ValueError(
                f"TOKEN_WEIGHT and FUZZY_WEIGHT must sum to 1.0, "
                f"but got {self.TOKEN_WEIGHT} + {self.FUZZY_WEIGHT} = {total_weight}"
            )

    def get_cascading_thresholds(self) -> list[float]:
        """
        Get the cascading thresholds for fuzzy search.
        """

        return [self.THRESHOLD_HIGH, self.THRESHOLD_MEDIUM, self.THRESHOLD_LOW]


def calculate_hybrid_fuzzy_search_score(
    query: str, text: str, config: FuzzySearchConfig = None
) -> float:
    """
    Calculate a hybrid score using token-based and fuzzy string matching.

    Args:
        query: The search query string
        text: The text to compare against
        config: Configuration object with weights and thresholds (optional)

    Returns:
        Float score between 0 and 1, where 1 is a perfect match
    """
    if config is None:
        config = FuzzySearchConfig()

    if not query or not text:
        return 0.0

    # Token-based matching (handles word order and partial matches)
    token_set_score = fuzz.token_set_ratio(query, text) / 100
    token_sort_score = fuzz.token_sort_ratio(query, text) / 100
    average_token_score = (token_set_score + token_sort_score) / 2

    # Fuzzy string matching (handles typos and character-level similarity)
    fuzzy_score = fuzz.ratio(query, text) / 100

    # Weighted combination of both approaches
    return (config.TOKEN_WEIGHT * average_token_score) + (
        config.FUZZY_WEIGHT * fuzzy_score
    )
