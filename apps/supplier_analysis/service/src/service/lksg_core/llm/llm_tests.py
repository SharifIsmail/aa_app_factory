import litellm
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

from service.lksg_core.llm.aleph_alpha_llm_provider import AALLMProvider

aa_llm_provider = AALLMProvider()
litellm.custom_provider_map = [
    {"provider": "aleph-alpha", "custom_handler": aa_llm_provider}
]

# response = completion(
#   model="aleph-alpha/llama-3.3-70b-instruct",
#   messages=[{ "content": "Hello, how are you?","role": "user"}],
#   stream=False,
# )
# print(response)


custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

model = LiteLLMModel(
    model_id="aleph-alpha/llama-3.3-70b-instruct",
    max_completion_tokens=8192,
    custom_role_conversions=custom_role_conversions,
)

# model_id="openai/gpt-4o"
# custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

# model = LiteLLMModel(
#         model_id,
#         custom_role_conversions=custom_role_conversions,
#         max_completion_tokens=8192,
#     )


agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model, max_steps=2)
# agent = ToolCallingAgent(tools=[DuckDuckGoSearchTool()], model=model)
agent.run(
    "How many seconds would it take for a leopard at full speed to run through Pont des Arts?"
)
