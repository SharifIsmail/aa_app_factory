# Hybrid Flow Architecture: Deterministic and AI-Driven Execution

## Executive Summary

This document describes the Hybrid Flow Architecture implemented in the Supplier Briefing service. This architecture allows the system to execute both AI-driven (agent-based) and deterministic (pre-programmed) workflows within the same conversation context, providing optimal performance for routine operations while maintaining flexibility for complex queries.

## Why This Feature Exists

### The Problem
Our traditional agent system, built on [smolagents](https://github.com/huggingface/smolagents), uses LLM reasoning for every query. While powerful for complex, open-ended questions, this approach has limitations:

- **Inefficiency**: Simple queries like "summarize business partner X" don't need AI reasoning
- **Cost**: Every operation consumes LLM tokens (expensive at scale)
- **Latency**: LLM inference adds 2-5 seconds to every operation
- **Predictability**: Same query might take different paths on different runs
- **User Experience**: Common operations require typing full queries instead of one-click actions

### The Solution
The Hybrid Flow Architecture introduces **deterministic flows** - pre-programmed execution paths for specific operations that bypass LLM reasoning while maintaining compatibility with the agent system.

## Architecture Overview

```
        User Interaction
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐      ┌──────────────┐
│  Chat   │      │ Quick Actions│
│  Input  │      │   Buttons    │
└────┬────┘      └──────┬───────┘
     │                  │
     │                  │ (flow_name + params)
     │                  │
     ▼                  ▼
┌─────────────────────────────────┐
│      HybridFlowAgent            │
│  ┌───────────────────────────┐  │
│  │ if mode == AGENT:         │  │
│  │   → _run_agent()          │  │
│  │ elif mode == DETERMINISTIC│  │
│  │   → _run_deterministic()  │  │
│  └───────────────────────────┘  │
└────────┬───────────┬────────────┘
         │           │
  AGENT  │           │  DETERMINISTIC
         ▼           ▼
┌─────────────┐ ┌─────────────────┐
│ CodeAgent   │ │ Flow Registry   │
│ (smolagents)│ │ DETERMINISTIC_  │
│             │ │ FLOWS[name]     │
└──────┬──────┘ └────────┬────────┘
       │                 │
       ▼                 ▼
┌─────────────┐ ┌─────────────────┐
│ LLM decides │ │ Flow executes   │
│ tool order  │ │ predefined      │
│ & params    │ │ tool sequence   │
└──────┬──────┘ └────────┬────────┘
       │                 │
       └────────┬────────┘
                │
                ▼
        ┌──────────────┐
        │ Shared Tools │
        │  - save_data │
        │  - present_  │
        │    results   │
        │  - summarize_│
        │    partners  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ Agent Memory │
        │ (steps list) │
        │              │
        │ • Real steps │
        │   (AGENT)    │
        │ • Synthetic  │
        │   steps      │
        │   (DETERM.)  │
        └──────────────┘
               │
               ▼
        ┌──────────────┐
        │ WorkLog &    │
        │ Repositories │
        │ • PANDAS_    │
        │   OBJECTS    │
        │ • RESULTS    │
        │ • AGENT_     │
        │   RESPONSE   │
        └──────────────┘
```

## Core Components

### 1. HybridFlowAgent (The Wrapper)

**Location**: `service/src/service/agent_core/hybrid_flow_agent.py`

This class wraps the original smolagents CodeAgent and adds deterministic flow capability:

```python
class HybridFlowAgent:
    def __init__(self, code_agent: CodeAgent, tools: dict[str, Tool], work_log: WorkLog):
        self._code_agent = code_agent  # Original AI agent
        self.tools = tools              # Shared tools
        self.work_log = work_log        # Execution tracking

    def run(self, query=None, mode=AgentMode.AGENT, flow_name=None, flow_params=None):
        if mode == AgentMode.AGENT:
            return self._run_agent(query)
        elif mode == AgentMode.DETERMINISTIC:
            return self._run_deterministic(flow_name, flow_params)
```

**Key Features**:
- Maintains same interface as original CodeAgent
- Routes execution based on mode
- Shares tools between both modes
- Handles memory injection for deterministic flows

### 2. Flow Registry Pattern

**Location**: `service/src/service/agent_core/deterministic_flows/__init__.py`

```python
DETERMINISTIC_FLOWS: Dict[str, Type[BaseDeterministicFlow]] = {
    "summarize_business_partner": SummarizeBusinessPartnerFlow,
    "business_partner_risks": BusinessPartnerRisksFlow,  # Future
    "compare_branch_risks": CompareBranchRisksFlow,      # Future
}
```


### 3. Base Flow Abstraction

**Location**: `service/src/service/agent_core/deterministic_flows/base.py`

Every deterministic flow inherits from this base class:

```python
class BaseDeterministicFlow(ABC):
    def __init__(self, tools: Dict[str, Tool], work_log: WorkLog):
        self.tools = tools
        self.work_log = work_log

    def push_deterministic_explained_action_step(self, text: str) -> None:
        """Records explainability for progressive UI updates"""
        explained_step = ExplainedActionStep(
            explanation=text,
            time_start=time.time(),
            agent_name="deterministic_flow"
        )
        self.work_log.explained_steps.append(explained_step)

    def create_synthetic_action_step(self, ...) -> ActionStep:
        """Creates fake agent memory entries"""
        # Builds ActionStep that looks like agent executed tools

    @abstractmethod
    def run(self, flow_params: Dict) -> Tuple[Any, Sequence[ActionStep]]:
        """Execute the deterministic flow"""
        pass
```

### 4. Memory Injection System

Deterministic results are injected into agent memory as if the agent performed them:

```python
def _inject_deterministic_run_into_memory(self, flow_name, synthetic_steps):
    # Create initial task description
    task_step = TaskStep(task=f"Deterministic flow '{flow_name}' triggered")

    # Inject into agent's conversation history
    self._code_agent.memory.steps.append(task_step)
    self._code_agent.memory.steps.extend(synthetic_steps)
```

This enables:
- Agent can reference deterministic results
- Users can ask follow-up questions
- Conversation maintains continuity

## Implementation Example: SummarizeBusinessPartnerFlow

**Location**: `service/src/service/agent_core/deterministic_flows/summarize_business_partner_flow.py`

```python
class SummarizeBusinessPartnerFlow(BaseDeterministicFlow):
    def run(self, flow_params: dict) -> tuple[Any, Sequence[ActionStep]]:
        partner_id = flow_params.get("business_partner_id")

        # Step 1: Explain what we're doing (for UI)
        self.push_step(f"Loading data for partner {partner_id}...")

        # Step 2: Use actual tools (same as agent would)
        summarize_tool = self.tools["summarize_business_partners"]
        partner_summary = summarize_tool.forward(partner_id)

        # Step 3: Save data (for later reference)
        save_tool = self.tools["save_data"]
        data_id = save_tool.forward(
            data=partner_summary,
            description=f"Partner {partner_id} summary",
            data_type="partner_summary"
        )

        # Step 4: Present results
        present_tool = self.tools["present_results"]
        present_tool.forward(
            data_ids=[data_id],
            dataframe_descriptions=[f"Partner {partner_id} data"]
        )

        # Step 5: Format response
        final_message = {"data": self._format_partner_summary(partner_id, partner_summary)}

        # Step 6: Create synthetic memory
        synthetic_step = self.create_synthetic_action_step(
            thought="Executing flow to summarize business partner",
            tool_calls=[
                {"name": "summarize_business_partners", "arguments": {"business_partner_ids": partner_id}},
                {"name": "save_data", "arguments": {...}},
                {"name": "present_results", "arguments": {...}}
            ],
            observations=["Retrieved partner data", "Saved to repository", "Presented results"],
            action_output=summary_text
        )

        return final_message, [synthetic_step]
```

## UI Integration: Quick Actions

**Location**: `ui/src/components/QuickActions/`

Frontend components trigger deterministic flows:

```vue
<template>
  <AaButton @click="toggleOpen">Summarize Business Partner</AaButton>

  <div v-if="isOpen">
    <!-- Partner selection dropdown -->
    <select v-model="selectedPartnerId">
      <option v-for="partner in partners" :value="partner.id">
        {{ partner.name }}
      </option>
    </select>
  </div>
</template>

<script setup>
const handlePartnerSelected = (partnerId) => {
  // Triggers deterministic flow
  startResearch(
    "Summarize the selected business partner.",
    onSuccess,
    onFailure,
    undefined,  // executionId
    {
      flow_name: "summarize_business_partner",
      params: { business_partner_id: partnerId }
    }
  );
};
</script>
```

## Explainability Pipeline

Both execution modes maintain full explainability:

### Agent Mode
- Records actual LLM reasoning
- Captures tool call decisions
- Shows thought process

### Deterministic Mode
- Records each step via `push_step()`
- Creates `ExplainedActionStep` objects
- Shows progression through fixed flow

Both produce identical UI representation, ensuring consistent user experience.

## Technical Design Decisions

### Why Inject Into Memory?
Rather than maintaining separate conversation histories, injection ensures the agent can reference and build upon deterministic results. This enables natural follow-up questions.

### Why Use Same Tools?
Code reuse and consistency - deterministic flows orchestrate existing tools rather than reimplementing logic. This ensures both modes produce compatible results.

### Why Synthetic Steps?
The agent's memory system and UI expect this format. Creating synthetic steps maintains compatibility with existing infrastructure.

## Benefits Achieved

1. **Performance**: 5-10x faster for routine operations (no LLM latency)
2. **Cost Reduction**: Zero LLM tokens for deterministic flows
3. **Predictability**: Same input → same execution path
4. **User Experience**: One-click operations for common tasks
5. **Maintainability**: Flows are Python code - testable, debuggable, version-controlled
6. **Flexibility**: Can mix modes in single conversation
7. **Consistency**: Both modes use same tools and data formats

## Adding New Deterministic Flows

### Step 1: Create Flow Class

```python
# service/src/service/agent_core/deterministic_flows/my_new_flow.py
from .base import BaseDeterministicFlow

class MyNewFlow(BaseDeterministicFlow):
    def run(self, flow_params: dict) -> tuple[Any, Sequence[ActionStep]]:
        # 1. Extract parameters
        param = flow_params.get("my_param")

        # 2. Push explainability steps
        self.push_step("Starting my flow...")

        # 3. Execute tools
        result = self.tools["my_tool"].forward(param)

        # 4. Create response
        final_message = {"data": f"Result: {result}"}

        # 5. Create synthetic memory
        synthetic_step = self.create_synthetic_action_step(...)

        return final_message, [synthetic_step]
```

### Step 2: Register Flow

```python
# service/src/service/agent_core/deterministic_flows/__init__.py
DETERMINISTIC_FLOWS = {
    "my_new_flow": MyNewFlow,
    # ... other flows
}
```

### Step 3: Create UI Component

```vue
<!-- ui/src/components/QuickActions/QuickActionMyFlow.vue -->
<template>
  <AaButton @click="triggerFlow">My Quick Action</AaButton>
</template>

<script setup>
const triggerFlow = () => {
  startResearch(
    "Description for UI",
    onSuccess,
    onFailure,
    undefined,
    {
      flow_name: "my_new_flow",
      params: { my_param: "value" }
    }
  );
};
</script>
```

## Testing Deterministic Flows

```python
def test_my_flow():
    # Setup
    tools = {"my_tool": MockTool()}
    work_log = WorkLog()

    # Execute
    flow = MyNewFlow(tools, work_log)
    result, steps = flow.run({"my_param": "test"})

    # Assert
    assert result["data"] == "Expected result"
    assert len(steps) == 1
    assert steps[0].tool_calls[0].name == "my_tool"
```

## Conclusion

The Hybrid Flow Architecture successfully bridges the gap between AI flexibility and deterministic efficiency. By allowing both modes to coexist within the same conversation context, we provide users with the best of both worlds: quick, predictable execution for routine tasks and intelligent reasoning for complex queries.

The implementation prioritizes:
- Code reuse (shared tools)
- Consistency (unified memory)
- Maintainability (clear abstractions)
- User experience (quick actions)

This architecture serves as a foundation for building increasingly sophisticated deterministic operations while maintaining the power of AI-driven exploration when needed.