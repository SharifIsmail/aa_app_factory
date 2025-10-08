from typing import Any, Dict, Iterable, List

from intelligence_layer.evaluation import Example, SingleOutputEvaluationLogic
from intelligence_layer.evaluation.aggregation.aggregator import AggregationLogic

from evaluation.core.pandas_comparator import (
    PandasComparator,
    PandasComparisonConfig,
)
from evaluation.core.pandas_vibe_comparator import PandasVibeComparator
from evaluation.core.text_comparator import TextComparator
from evaluation.intelligence_layer_eval.supplier_briefing_models import (
    PandasComparisonResult,
    PandasObjectData,
    QuestionDifficulty,
    SupplierBriefingAggregation,
    SupplierBriefingEvaluation,
    SupplierBriefingExpectedOutput,
    SupplierBriefingInputDetails,
    SupplierBriefingOutput,
    TextComparisonDetails,
    TextComparisonResult,
    TextComparisonStatus,
    VibeCheckResult,
    VibeCheckStatus,
)
from service.core.utils.pandas_json_utils import (
    deserialize_pandas_object_from_json,
)


class SupplierBriefingEvaluationLogic(
    SingleOutputEvaluationLogic[
        SupplierBriefingInputDetails,
        SupplierBriefingOutput,
        SupplierBriefingExpectedOutput,
        SupplierBriefingEvaluation,
    ]
):
    def __init__(self) -> None:
        self.text_comparator = TextComparator()
        self.pandas_vibe_comparator = PandasVibeComparator()

    @staticmethod
    def _compare_pandas_objects(
        golden_pandas_objects: List[PandasObjectData],
        output_pandas_objects: List[PandasObjectData],
        pandas_comparison_config: PandasComparisonConfig,
    ) -> PandasComparisonResult:
        golden_pandas_objects_deserialized = [
            deserialize_pandas_object_from_json(obj.pandas_object_json)
            for obj in golden_pandas_objects
        ]
        output_pandas_objects_deserialized = [
            deserialize_pandas_object_from_json(obj.pandas_object_json)
            for obj in output_pandas_objects
        ]

        # Handle empty lists
        if (
            not golden_pandas_objects_deserialized
            and not output_pandas_objects_deserialized
        ):
            score = 1.0
        elif (
            not golden_pandas_objects_deserialized
            and output_pandas_objects_deserialized
        ) or (
            golden_pandas_objects_deserialized
            and not output_pandas_objects_deserialized
        ):
            score = 0.0
        else:
            pandas_comparator = PandasComparator(pandas_comparison_config)
            # Compare in order and average scores; penalize unmatched with 0
            max_len = max(
                len(golden_pandas_objects_deserialized),
                len(output_pandas_objects_deserialized),
            )
            total = 0.0
            for idx in range(max_len):
                left = (
                    golden_pandas_objects_deserialized[idx]
                    if idx < len(golden_pandas_objects_deserialized)
                    else None
                )
                right = (
                    output_pandas_objects_deserialized[idx]
                    if idx < len(output_pandas_objects_deserialized)
                    else None
                )
                if left is None or right is None:
                    pair_score = 0.0
                else:
                    pair_score = pandas_comparator.compare(left, right)
                total += float(pair_score)
            score = total / float(max_len) if max_len > 0 else 1.0

        return PandasComparisonResult(
            score=score,
        )

    def _vibe_check_pandas_objects(
        self,
        golden_cleaned: List[Dict[str, str]],
        current_cleaned: List[Dict[str, Any]],
        exact_match: bool,
        research_question: str,
    ) -> VibeCheckResult:
        if exact_match:
            return VibeCheckResult(
                status=VibeCheckStatus.EXACT_MATCH_SKIP,
                score=1.0,
                reasoning="Exact match",
            )

        # If one side empty, return 0 early
        if (not golden_cleaned and current_cleaned) or (
            golden_cleaned and not current_cleaned
        ):
            return VibeCheckResult(
                status=VibeCheckStatus.NO_OVERLAP_EMPTY_SKIP,
                score=0.0,
                reasoning="One side empty",
            )

        # Otherwise, ask LLM judge
        return self.pandas_vibe_comparator.compare(
            golden_cleaned, current_cleaned, research_question
        )

    def _compare_text(
        self, golden_text: str, current_text: str
    ) -> TextComparisonResult:
        return self.text_comparator.compare(golden_text, current_text)

    def do_evaluate_single_output(
        self,
        example: Example[SupplierBriefingInputDetails, SupplierBriefingExpectedOutput],
        output: SupplierBriefingOutput,
    ) -> SupplierBriefingEvaluation:
        pandas_objects_comparison_details = self._compare_pandas_objects(
            example.expected_output.pandas_objects,
            output.pandas_objects,
            example.input.pandas_comparison_config,
        )

        text_result = (
            self._compare_text(example.expected_output.text, output.text)
            if example.expected_output.text
            else TextComparisonResult(
                is_match=True,
                details=TextComparisonDetails(
                    status=TextComparisonStatus.SKIPPED,
                    reason="No expected text provided",
                ),
            )
        )

        pandas_objects_match = pandas_objects_comparison_details.score == 1.0
        overall_match = pandas_objects_match and text_result.is_match

        # Vibe check for pandas objects
        golden_cleaned = [
            {
                "data": pandas_object.pandas_object_json.get("data", ""),
                "type": pandas_object.pandas_object_json.get("type", ""),
            }
            for pandas_object in example.expected_output.pandas_objects
        ]
        current_cleaned = [
            {
                "data": pandas_object.pandas_object_json.get("data", ""),
                "type": pandas_object.pandas_object_json.get("type", ""),
            }
            for pandas_object in output.pandas_objects
        ]

        vibe_details = self._vibe_check_pandas_objects(
            golden_cleaned,
            current_cleaned,
            pandas_objects_match,
            example.input.research_question,
        )

        return SupplierBriefingEvaluation(
            is_correct=overall_match,
            pandas_objects_score=pandas_objects_comparison_details.score,
            text_match=text_result.is_match,
            text_details=text_result.details.model_dump(exclude_none=True),
            question_id=example.input.metadata.get("question_id"),
            research_question=example.input.research_question,
            question_difficulty=example.input.question_difficulty,
            has_pandas_objects=len(example.expected_output.pandas_objects) > 0,
            pandas_objects_count=len(output.pandas_objects),
            vibe_score=vibe_details.score,
            vibe_details=vibe_details.model_dump(exclude_none=True),
        )


class SupplierBriefingAggregationLogic(
    AggregationLogic[SupplierBriefingEvaluation, SupplierBriefingAggregation]
):
    """Simple IL aggregation logic."""

    def aggregate(
        self, evaluations: Iterable[SupplierBriefingEvaluation]
    ) -> SupplierBriefingAggregation:
        """Aggregate evaluation results into overall metrics."""

        eval_list = list(evaluations)

        if not eval_list:
            return SupplierBriefingAggregation(
                pass_rate=0.0,
                pandas_score=0.0,
                pass_rate_text=0.0,
                avg_vibe_score=0.0,
                pass_rate_easy=0.0,
                pass_rate_hard=0.0,
            )

        # Calculate metrics
        total = len(eval_list)
        correct = sum(1 for e in eval_list if e.is_correct)
        # Average pandas score across evaluations
        pandas_objects_score_sum = sum(float(e.pandas_objects_score) for e in eval_list)

        text_evaluated = [
            e
            for e in eval_list
            if e.text_details.get("status") != TextComparisonStatus.SKIPPED.value
        ]
        text_correct = sum(1 for e in text_evaluated if e.text_match)
        text_total = len(text_evaluated)

        avg_vibe_score = round(
            sum(float(e.vibe_score) for e in eval_list) / total if total > 0 else 0.0, 3
        )

        pass_rate = round(correct / total, 3)
        pandas_score = round(pandas_objects_score_sum / total if total > 0 else 0.0, 3)
        pass_rate_text = round(text_correct / text_total, 3) if text_total > 0 else None

        # Pass rate over easy examples
        easy_examples = [
            e for e in eval_list if e.question_difficulty == QuestionDifficulty.EASY
        ]
        if easy_examples:
            pass_rate_easy = round(
                sum(1 for e in easy_examples if e.is_correct) / len(easy_examples), 3
            )
        else:
            pass_rate_easy = None

        hard_examples = [
            e for e in eval_list if e.question_difficulty == QuestionDifficulty.HARD
        ]
        if hard_examples:
            pass_rate_hard = round(
                sum(1 for e in hard_examples if e.is_correct) / len(hard_examples), 3
            )
        else:
            pass_rate_hard = None

        return SupplierBriefingAggregation(
            pass_rate=pass_rate,
            pandas_score=pandas_score,
            pass_rate_text=pass_rate_text,
            avg_vibe_score=avg_vibe_score,
            pass_rate_easy=pass_rate_easy,
            pass_rate_hard=pass_rate_hard,
        )
