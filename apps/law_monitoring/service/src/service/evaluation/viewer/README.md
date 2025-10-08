# Law Relevancy Benchmark Viewer

A Vue.js application for viewing and analyzing benchmark execution results from the LawRelevancyTask in Pharia Studio.

## Overview

This application provides a comprehensive interface for:

- **Single Execution Analysis**: View detailed results from individual benchmark executions
- **Execution Comparison**: Compare results between two different executions to identify performance differences
- **Team Relevancy Visualization**: Analyze how different teams are classified for relevancy to specific laws
- **Performance Metrics**: Track accuracy, F1 score, precision, recall, latency, and token usage

## Features

### 🔧 Configuration
- Easy URL-based configuration by pasting Pharia Studio execution URLs
- Secure bearer token authentication with show/hide functionality
- Automatic parsing of project, benchmark, and execution IDs

### 📊 Single Execution Analysis
- **Execution List**: Browse all executions with key metrics and sorting
- **Detailed View**: Deep dive into individual execution results
- **Team Analysis**: See relevancy classifications, scores, and reasoning for each team
- **Performance Metrics**: View latency, token usage, and evaluation scores
- **Error Handling**: Identify and highlight teams with classification errors

### 🔍 Execution Comparison
- **Side-by-Side Comparison**: Compare metrics between two executions
- **Team-by-Team Analysis**: See which teams have different classifications
- **Difference Highlighting**: Easily spot mismatches and score differences
- **Performance Comparison**: Compare latency, token usage, and accuracy metrics

### 📈 Visual Indicators
- Color-coded accuracy scores (green = high, yellow = medium, red = low)
- Relevancy badges for easy identification
- Match/mismatch indicators for comparisons
- Error highlighting for failed classifications

## Technology Stack

- **Vue 3** with Composition API
- **TypeScript** for type safety
- **Vite** for fast development and building
- **Pinia** for state management
- **Vue Router** for navigation

## Getting Started

### Prerequisites

- Node.js 20.19.0 or higher
- Access to Pharia Studio with a valid bearer token

### Installation

1. Navigate to the viewer directory:
   ```bash
   cd service/src/service/evaluation/viewer
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser to `http://localhost:5173`

### Configuration

1. **Get your Bearer Token**:
   - Log into Pharia Studio
   - Generate or copy your API bearer token

2. **Get Execution URLs**:
   - Navigate to a benchmark execution in Pharia Studio
   - Copy the full URL (should include `/executions/{id}`)

3. **Use the Application**:
   - Paste your bearer token in the configuration section
   - Paste execution URL(s) depending on whether you want single analysis or comparison
   - Click "Load Executions" or "Compare Executions"

## Usage Examples

### Single Execution Analysis

1. Enter your bearer token
2. Paste an execution URL like:
   ```
   https://pharia-studio.customer.pharia.com/projects/abc123/benchmarks/def456/executions/ghi789
   ```
3. Click "Load Executions"
4. Select an execution from the list to view details

### Execution Comparison

1. Switch to the "Compare Executions" tab
2. Enter your bearer token
3. Paste two different execution URLs
4. Click "Compare Executions"
5. Select a law from the comparison list to see detailed team-by-team differences

## API Integration

The application integrates with Pharia Studio's API endpoints:

- `GET /v1/studio/projects/{project}/evaluation/benchmarks/{benchmark}/executions/{execution}/lineages` - Fetch execution results
- `GET /v1/studio/projects/{project}/evaluation/benchmarks/{benchmark}` - Fetch benchmark metadata
- `GET /v1/studio/projects/{project}/evaluation/benchmarks/{benchmark}/executions/{execution}` - Fetch execution metadata

## Data Models

### LawRelevancyTask Input
```typescript
{
  law_text: string
  law_title: string
  metadata: {
    expression_url: string
    law_id?: string
  }
}
```

### LawRelevancyTask Output
```typescript
{
  team_relevancies: Array<{
    team_id: string
    team_name: string
    is_relevant: boolean
    relevancy_score: number
    reasoning: string
    error?: string
  }>
  subject_matter_summary?: string
}
```

### Evaluation Metrics
```typescript
{
  is_correct: boolean
  accuracy_score: number
  overall_f1_score: number
  precision: number
  recall: number
  team_matches: Array<{
    team_id: string
    expected_relevant: boolean
    actual_relevant: boolean
    matches: boolean
  }>
}
```

## Development

### Project Structure

```
src/
├── components/
│   ├── BenchmarkViewer.vue      # Main application component
│   ├── ExecutionsList.vue       # List of executions
│   ├── ExecutionDetails.vue     # Detailed execution view
│   └── ExecutionComparison.vue  # Execution comparison view
├── services/
│   └── api.service.ts           # API integration
├── types/
│   └── api.types.ts             # TypeScript type definitions
├── App.vue                      # Root application component
└── main.ts                      # Application entry point
```

### Building for Production

```bash
npm run build
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**: 
   - Verify your bearer token is correct and hasn't expired
   - Check that you have access to the specified project/benchmark

2. **URL Parsing Errors**:
   - Ensure you're copying the complete execution URL
   - URL must include `/executions/{id}` at the end

3. **No Data Found**:
   - Verify the execution exists and has completed
   - Check that the benchmark contains LawRelevancyTask executions

4. **CORS Issues**:
   - In development, the app uses a proxy to handle CORS
   - For production deployment, ensure proper CORS configuration

### Performance Considerations

- Large executions with many teams may take longer to load
- The application automatically paginates API requests to handle large datasets
- Consider filtering or limiting the number of executions displayed for better performance

## Contributing

When contributing to this viewer:

1. Follow the existing code style and TypeScript patterns
2. Add proper type definitions for new features
3. Test with real Pharia Studio data
4. Update this README if adding new features
5. Consider responsive design for different screen sizes

## License

This viewer is part of the law monitoring system and follows the same licensing as the parent project.
