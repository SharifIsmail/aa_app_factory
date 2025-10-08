# Law Monitoring & Analysis System

A comprehensive multi-agent system for automated German law text. This application provides intelligent extraction, analysis, and reporting capabilities for German legal documents.

## 🎯 Overview

The Law Monitoring system automatically:
- Extracts law content from German legal websites
- Analyzes law structure and key components using AI
- Generates comprehensive HTML reports
- Offers structured data extraction (headers, subject matter, penalties, roles)

## 🏗️ Architecture

### Frontend (`/ui`)
- **Vue.js 3** with TypeScript
- Real-time progress tracking interface
- Law URL input and validation
- Interactive report viewing and downloading

### Backend (`/service`)
- **FastAPI** Python service with async support
- Background task execution with cancellation
- Comprehensive work log management
- Data persistence and caching

### AI Agents (`/service/src/service/law_core`)
- **Summary Agent**: Law text analysis and extraction
- **Web Scraping Tools**: Content extraction from legal websites
- **LLM Integration**: Intelligent text processing and analysis

## 🚀 Quick Start

For detailed instructions on running each part of the application for development, refer to the respective README files:
- [Service](service/README.md) - Backend API and AI agents
- [UI](ui/README.md) - Frontend Vue.js application
- [Skills](skills/README.md) - If applicable

> [!WARNING]
> **Beta Release Notice:** This beta version is intended for development and testing purposes only. It may not be suitable for production use.

## 🔧 Getting Started

Before using any pharia-ai-cli command, make sure all necessary environment variables are configured correctly. These are specified in the following files:
- Root directory: [`.env`](.env)
- UI directory: [ui/.env](ui/.env)
- Service directory: [service/.env](service/.env)
- Skills directory: [skills/.env](skills/.env) (if applicable)

### Previewing an Application in Pharia Assistant

Preview your application within the Pharia Assistant by navigating to your application's root directory and executing:
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

## 🛠️ Development

The application follows a multi-agent architecture with clear separation of concerns:

- **Frontend**: Vue.js components for user interaction
- **Backend**: FastAPI service with dependency injection
- **Agents**: Specialized AI agents for law analysis
- **Tools**: Utility tools for web scraping and content processing
- **Storage**: Persistent data storage and caching layer

For development setup and detailed instructions, see the individual README files in the `service/` and `ui/` directories.

