# Project Architecture Overview

## Core Architecture

### Central Component: WorkLog
- `WorkLog` serves as the execution context and shared state manager (`service/agent_core/models.py:237`)
- Contains `DataStorage` for shared data between all components
- Tracks execution status, tasks, and tool usage logs
- Managed globally by singleton `WorkLogManager` (`service/work_log_manager.py:11`)

### Agent System: smolagents Integration
- Uses `CodeAgent` from smolagents library (`service/agent_core/research_agent/model_tools_manager.py:213`)
- Agent writes and executes Python code to solve data analysis problems
- Configured with custom LLM provider (Aleph Alpha) and 10-step limit
- Maintains conversation history across multiple user interactions

### Tool Architecture
- All tools inherit from smolagents `Tool` base class
- Each tool receives shared `WorkLog` instance for data persistence
- Tools store results in different repositories within `WorkLog.data_storage`:
  - `REPO_EXECUTE_SQL`: Raw data from tools
  - `REPO_INSIGHTS`: Intermediate analysis results  
  - `REPO_AGENT_RESPONSE`: Final agent responses
  - `REPO_RESULTS`: Structured output for users

## Key Concepts

### Shared Data Storage Pattern
- `DataStorage` acts as multi-repository system (`service/agent_core/models.py:11`)
- Tools can persist/retrieve data using repository keys
- Enables data flow between agent execution steps and tools

### Tool Ecosystem
- Domain-specific tools (e.g., `PandasDataFrameTool`, `BusinessPartnerRiskTool`)
- Each tool is WorkLog-aware and can store execution artifacts
- Tools provide rich descriptions with data schemas to guide agent behavior

### Execution Flow
1. `WorkLogManager` creates/retrieves `WorkLog` for execution ID
2. Agent and tools initialized with shared `WorkLog` reference
3. Agent uses tools to analyze data, storing results in shared storage
4. Post-processing extracts and summarizes results using LLM
5. Final results stored in dedicated repository for user presentation

### Persistence & State Management
- Agent instances persist across conversations (`service/agent_core/persistence/agent_instance_store.py`)
- Work logs maintain execution state and can be reset for new conversations
- Tracing system provides observability across the entire execution pipeline

## Key Files

### Core Models
- `service/agent_core/models.py` - Core data structures (WorkLog, DataStorage, TaskStatus)
- `service/work_log_manager.py` - Singleton manager for WorkLog instances

### Agent Implementation
- `service/agent_core/research_agent/research_agent.py` - Main research orchestration
- `service/agent_core/research_agent/model_tools_manager.py` - Agent and tool initialization

### Tool Implementations
- `service/agent_core/tools/` - Directory containing all domain-specific tools
- `service/agent_core/tools/pandas_dataframe_tool.py` - Primary data access tool
- `service/agent_core/tools/present_results_tool.py` - Results presentation tool

### Persistence
- `service/agent_core/persistence/` - Agent state persistence components

## Architecture Benefits

The architecture enables a collaborative environment where the AI agent and specialized tools share state through WorkLog, allowing complex multi-step data analysis workflows with full auditability and observability.