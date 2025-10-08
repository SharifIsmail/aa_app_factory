# Pharia Application

For detailed instructions on running each part of the Application for development, refer to the respective README files:
- [Service](service/README.md)
- [UI](ui/README.md)
- [Skills](skills/README.md) - If applicable

> [!WARNING]
> **Beta Release Notice:** This beta version is intended for development and testing purposes only. It may not be suitable for production use.

## Getting Started

Before using any pharia-ai-cli command, make sure all necessary environment variables are configured correctly. These are specified in the following files:
- Root directory: [`.env`](.env)
- UI directory: [ui/.env](ui/.env)
- Service directory: [service/.env](service/.env)
- Skills directory: [skills/.env](skills/.env) (if applicable)

### Previewing an Application in Pharia Assistant

Preview your application within the Pharia Assistant by navigating to your application’s root directory and executing:
```shell
pharia-ai-cli preview
```
This command starts the application locally, and enables you to preview the application directly in PhariaAssistant via [dev mode](/products/pharia-assistant/how-to/dev-mode).

### Publishing an Application

To publish your application to a container registry, navigate to the root directory of your application and execute:
```shell
pharia-ai-cli publish
```
Publishing prepares your application for deployment by packaging it into a container image.

### Deploying an Application

To deploy your published application, navigate to the root directory and execute:
```shell
pharia-ai-cli deploy
```
Once deployment is complete, open Pharia Assistant to view and interact with your live application.


### Undeploying an Application

To undeploy an application, navigate to the root directory of your application and use the following command:

```shell
pharia-ai-cli undeploy
```

## Manual Deployment

For deploying a specific image version:

1. **Update the image tag** in `service/deployment-config.json`:
   - Images are automatically built by CI on every commit
   - Get the new tag from the CI pipeline output
   - Update the `tag` field in the config file

2. **Set required environment variables** in `supplier_briefing/.env`

3. **Deploy using the deploy script**:
   ```shell
   python service/src/service/deploy.py deploy <usecase-id> --config service/deployment-config.json
   ```

# Structure of conversations and overview of agents

At the highest level we have chat histories between a human and our application. They are called "execution" and are uniquely determined by an `execution_id`.

Each chat-history / execution consists of a multi-turn conversation between a human and the application and is visualized in the frontend.

The agent-turns of this conversation are counted in the `MultiTurnCounter` class. 

When the application receives a user message, the smolagents agent(s) generates sequences of steps.
There are currently two agents:

* First there is a CodeAgent with name `query_agent` that interacts with the user.
* This agent is able to use a second CodeAgent with name `data_analysis_agent` that is wrapped in the tool `DataAnalysisAgentTool`.

Steps of both agents are finally explained and the explanations are shown to the user.
In order to identify steps of both agents, the `StepIdentity` class is used that holds references to the `multi_turn_counter`, `agent_name` and `step_number`.

| Actor                            | multi_turn_counter | agent_name          | step_number |
|----------------------------------|--------------------|---------------------|-------------|
| User asks question               |                    |                     |             |
| Query Agent 1st step             | 0                  | query_agent         | 0           |
| Query Agent 2nd step             | 0                  | query_agent         | 1           |
| Data Analysis Agent 1st step     | 0                  | data_analysis_agent | 0           |
| Data Analysis Agent final answer | 0                  | data_analysis_agent | 1           |
| Query Agent final answer         | 0                  | query_agent         | 2           |
| User asks for clarification      |                    |                     |             |
| Query Agent 1st step             | 1                  | query_agent         | 0           |
| Query Agent final answer         | 1                  | query_agent         | 1           |
