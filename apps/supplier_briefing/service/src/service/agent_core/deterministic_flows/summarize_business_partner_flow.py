"""Deterministic flow for summarizing business partners."""

import time
from typing import Any, Dict, Sequence, Tuple

from smolagents import ActionStep, TaskStep

from service.agent_core.models import FlowResponse, SyntheticToolCall

from .base import BaseDeterministicFlow


class SummarizeBusinessPartnerFlow(BaseDeterministicFlow):
    """Flow that summarizes a business partner using the summarize_business_partners tool."""

    def run(
        self, flow_params: Dict[str, Any] | None = None
    ) -> Tuple[FlowResponse, Sequence[ActionStep | TaskStep]]:
        """Execute the business partner summarization flow."""
        summarize_tool = self.tools["summarize_business_partners"]
        save_tool = self.tools["save_data"]
        present_tool = self.tools["present_results"]
        start_time = time.time()

        # Extract parameters
        partner_id = flow_params.get("business_partner_id") if flow_params else None
        if not partner_id:
            raise ValueError("business_partner_id is required")

        # Push explainability steps
        self.push_deterministic_explained_action_step(
            f"Retrieving business partner data for ID {partner_id}..."
        )

        # Use the real summarize_business_partners tool
        try:
            partner_summary = summarize_tool.forward(business_partner_ids=partner_id)
            self.push_deterministic_explained_action_step(
                f"Successfully loaded business partner {partner_id} data"
            )
        except ValueError as e:
            error_msg = str(e)
            self.push_deterministic_explained_action_step(f"Error: {error_msg}")
            final_message = FlowResponse(data=f"Error: {error_msg}")

            action_step = self.create_synthetic_action_step(
                start_time=start_time,
                thought=f"Attempted to summarize business partner {partner_id} but encountered an error",
                tool_calls=[
                    SyntheticToolCall(
                        name="summarize_business_partners",
                        arguments={"business_partner_ids": partner_id},
                    )
                ],
                observations=[error_msg],
                action_output=error_msg,
                step_number=len(self.work_log.explained_steps) + 1,
            )
            return final_message, [action_step]
        except Exception as e:
            self.push_deterministic_explained_action_step(
                f"Error loading partner data: {str(e)}"
            )
            raise

        self.push_deterministic_explained_action_step(
            "Processing business partner information..."
        )

        # Save the summary data
        save_description = f"Business partner {partner_id} summary"
        data_id = save_tool.forward(
            data=partner_summary,
            description=save_description,
            data_type="partner_summary",
        )

        self.push_deterministic_explained_action_step("Saving summary to repository...")

        # Present the results
        present_result_msg = present_tool.forward(
            data_ids=[data_id],
            dataframe_descriptions=[f"Business Partner {partner_id} summary data"],
        )

        self.push_deterministic_explained_action_step(
            "Formatting results for presentation..."
        )

        # Create the text response with the actual data
        # Format the partner summary into a readable message
        summary_text = self._create_completion_message(partner_id)

        final_message = FlowResponse(data=summary_text)

        # Create synthetic action step for memory
        thought = f"I need to retrieve and summarize information about business partner {partner_id}"
        tool_calls = [
            SyntheticToolCall(
                name="summarize_business_partners",
                arguments={
                    "business_partner_ids": partner_id,
                },
            ),
            SyntheticToolCall(
                name="save_data",
                arguments={
                    "data": partner_summary.to_dict()
                    if hasattr(partner_summary, "to_dict")
                    else str(partner_summary),
                    "description": save_description,
                    "data_type": "partner_summary",
                },
            ),
            SyntheticToolCall(
                name="present_results",
                arguments={
                    "data_ids": [data_id],
                    "dataframe_descriptions": [
                        f"Business Partner {partner_id} summary data"
                    ],
                },
            ),
        ]
        observations = [
            f"Retrieved business partner {partner_id} summary from data",
            f"Tool call 'summarize_business_partners' returned partner data",
            f"Tool call 'save_data' returned: '{data_id}'",
            "Tool call 'present_results' returned a message object.",
        ]
        action_output = summary_text

        action_step = self.create_synthetic_action_step(
            start_time=start_time,
            thought=thought,
            tool_calls=tool_calls,
            observations=observations,
            action_output=action_output,
            step_number=len(self.work_log.explained_steps) + 1,
        )

        return final_message, [action_step]

    def _create_completion_message(self, partner_id: str) -> str:
        """Create a simple completion message for the business partner summary."""
        return f"Business partner {partner_id} summary completed successfully. See detailed information in the table below."
