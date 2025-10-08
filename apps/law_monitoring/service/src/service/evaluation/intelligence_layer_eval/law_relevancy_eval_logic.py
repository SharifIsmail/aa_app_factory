from typing import Iterable, List, TypedDict

from law_relevancy_task import LawRelevancyInputDetails  # type: ignore
from pharia_studio_sdk.evaluation import (
    Example,
    SingleOutputEvaluationLogic,
)
from pharia_studio_sdk.evaluation.aggregation.aggregator import AggregationLogic
from pydantic import BaseModel

from service.models import TeamRelevancyWithCitations


class ConfusionMatrix(TypedDict):
    """Type definition for confusion matrix."""

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class LawRelevancyEvaluation(BaseModel):
    """Evaluation results for law relevancy classification."""

    is_correct: bool
    expected_relevant: bool
    predicted_relevant: bool
    ratio_of_relevant_teams: float
    total_teams_assessed: int
    relevant_teams_count: int


class LawRelevancyEvaluationLogic(
    SingleOutputEvaluationLogic[
        LawRelevancyInputDetails,
        List[TeamRelevancyWithCitations],
        bool,
        LawRelevancyEvaluation,
    ]
):
    """Evaluation logic for law relevancy classification."""

    def do_evaluate_single_output(
        self,
        example: Example[LawRelevancyInputDetails, bool],
        output: List[TeamRelevancyWithCitations],
    ) -> LawRelevancyEvaluation:
        """Evaluate a single example."""
        expected_relevant = example.expected_output

        # Get prediction from output - any team relevant means overall relevant
        predicted_relevant = any(team.is_relevant for team in output)

        # Calculate basic metrics
        is_correct = expected_relevant == predicted_relevant

        # Calculate confidence (ratio of teams that found it relevant)
        ratio_of_relevant_teams = (
            len([team for team in output if team.is_relevant]) / len(output)
            if output
            else 0.0
        )

        return LawRelevancyEvaluation(
            is_correct=is_correct,
            expected_relevant=expected_relevant,
            predicted_relevant=predicted_relevant,
            ratio_of_relevant_teams=ratio_of_relevant_teams,
            total_teams_assessed=len(output),
            relevant_teams_count=len([team for team in output if team.is_relevant]),
        )


class LawRelevancyAggregation(BaseModel):
    """Aggregation results for law relevancy evaluation."""

    total_examples: int
    accuracy: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float


class LawRelevancyAggregationLogic(
    AggregationLogic[LawRelevancyEvaluation, LawRelevancyAggregation]
):
    """Aggregation logic for law relevancy evaluation results."""

    def aggregate(
        self,
        evaluations: Iterable[LawRelevancyEvaluation],
    ) -> LawRelevancyAggregation:
        """Aggregate evaluation results across all examples."""
        all_evaluations = list(evaluations)
        total_examples = len(all_evaluations)

        if not all_evaluations:
            return LawRelevancyAggregation(
                total_examples=total_examples,
                accuracy=0.0,
                tp=0,
                fp=0,
                tn=0,
                fn=0,
                precision=0.0,
                recall=0.0,
                f1=0.0,
            )

        # Basic metrics
        correct_predictions = sum(
            1 for eval_result in all_evaluations if eval_result.is_correct
        )
        accuracy = (
            correct_predictions / total_examples if total_examples > 0 else float("nan")
        )

        # Confusion matrix
        true_positives = sum(
            1
            for eval_result in all_evaluations
            if eval_result.expected_relevant and eval_result.predicted_relevant
        )
        false_positives = sum(
            1
            for eval_result in all_evaluations
            if not eval_result.expected_relevant and eval_result.predicted_relevant
        )
        true_negatives = sum(
            1
            for eval_result in all_evaluations
            if not eval_result.expected_relevant and not eval_result.predicted_relevant
        )
        false_negatives = sum(
            1
            for eval_result in all_evaluations
            if eval_result.expected_relevant and not eval_result.predicted_relevant
        )

        # Calculate precision, recall, F1
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else float("nan")
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else float("nan")
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else float("nan")
        )

        return LawRelevancyAggregation(
            total_examples=total_examples,
            accuracy=accuracy,
            tp=true_positives,
            tn=true_negatives,
            fp=false_positives,
            fn=false_negatives,
            precision=precision,
            recall=recall,
            f1=f1_score,
        )
