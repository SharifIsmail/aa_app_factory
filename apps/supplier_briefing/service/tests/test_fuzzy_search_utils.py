"""Unit tests for fuzzy search utilities."""

import pytest

from service.agent_core.tools.utils.fuzzy_search_utils import (
    FuzzySearchConfig,
    calculate_hybrid_fuzzy_search_score,
)


def test_get_cascading_thresholds() -> None:
    """Test that cascading thresholds are returned in correct order."""
    config = FuzzySearchConfig()
    thresholds = config.get_cascading_thresholds()

    assert thresholds[0] > thresholds[1] > thresholds[2]


def test_custom_weights_validation() -> None:
    """Test that custom weights are validated to sum to 1.0."""
    # Test valid custom weights
    FuzzySearchConfig(token_weight=0.7, fuzzy_weight=0.3)
    # Should not raise an exception

    # Test invalid weights that don't sum to 1
    with pytest.raises(
        ValueError, match="TOKEN_WEIGHT and FUZZY_WEIGHT must sum to 1.0"
    ):
        FuzzySearchConfig(token_weight=0.6, fuzzy_weight=0.3)


def test_exact_match_returns_one() -> None:
    """Test that identical strings return a score of 1.0."""
    query = "test string"
    text = "test string"
    score = calculate_hybrid_fuzzy_search_score(query, text)
    assert score == 1.0


def test_completely_different_strings_low_score() -> None:
    """Test that completely different strings return a low score."""
    query = "apple"
    text = "zebra"
    score = calculate_hybrid_fuzzy_search_score(query, text)
    assert 0.0 <= score <= 0.2


def test_partial_match_medium_score() -> None:
    """Test that partial matches return medium scores."""
    query = "construction work"
    text = "construction industry"
    score = calculate_hybrid_fuzzy_search_score(query, text)
    assert 0.6 <= score


def test_typo_tolerance() -> None:
    """Test that minor typos still produce reasonable scores."""
    query = "manufacturing"
    text = "manufaturing"  # Missing 'c'
    score = calculate_hybrid_fuzzy_search_score(query, text)
    assert score >= 0.7  # Should still be quite high


def test_empty_strings() -> None:
    """Test behavior with empty strings."""
    score = calculate_hybrid_fuzzy_search_score("", "")
    assert score == 0.0

    score = calculate_hybrid_fuzzy_search_score("test", "")
    assert score == 0.0

    score = calculate_hybrid_fuzzy_search_score("", "test")
    assert score == 0.0


def test_custom_config_affects_scoring() -> None:
    """Test that custom configuration affects the scoring."""
    # Use a case where token and fuzzy scores will be different
    # "apple orange" vs "orange apple" - same tokens, different order
    query = "apple orange"
    text = "orange apple banana"

    # Default config
    default_score = calculate_hybrid_fuzzy_search_score(query, text)

    # Config favoring token matching (should score higher due to token overlap)
    token_heavy_config = FuzzySearchConfig(token_weight=0.9, fuzzy_weight=0.1)
    token_heavy_score = calculate_hybrid_fuzzy_search_score(
        query, text, token_heavy_config
    )

    # Config favoring fuzzy matching (should score lower due to character differences)
    fuzzy_heavy_config = FuzzySearchConfig(token_weight=0.1, fuzzy_weight=0.9)
    fuzzy_heavy_score = calculate_hybrid_fuzzy_search_score(
        query, text, fuzzy_heavy_config
    )

    # Token-heavy should score higher than fuzzy-heavy for this case
    assert token_heavy_score > fuzzy_heavy_score
    # Scores should be different from default
    assert default_score != token_heavy_score
    assert default_score != fuzzy_heavy_score
