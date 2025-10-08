import type {
  LineagesResponse,
  ExecutionConfig,
  Lineage,
  ProcessedLineage,
  TeamRelevancy,
  LawRelevancyInput,
  LawRelevancyOutput,
  ClassificationMetrics
} from '../types/api.types'

export class LawRelevancyApiService {
  private baseUrl: string

  constructor() {
    // Use proxy in development, direct URL in production
    const isDev = import.meta.env.DEV
    const envApiUrl = import.meta.env.VITE_API_BASE_URL || 'https://api.customer.pharia.com'

    // Option to bypass proxy for debugging - set VITE_BYPASS_PROXY=true in .env.local
    const bypassProxy = import.meta.env.VITE_BYPASS_PROXY === 'true'

    if (bypassProxy || !isDev) {
      this.baseUrl = envApiUrl.endsWith('/') ? envApiUrl : envApiUrl + '/'
    } else {
      this.baseUrl = '/api/'
    }

    console.log('API Service initialized with baseUrl:', this.baseUrl)
    console.log('isDev:', isDev, 'bypassProxy:', bypassProxy)
  }

  async fetchLineages(
    config: ExecutionConfig,
    bearerToken: string,
    page = 1,
    size = 100
  ): Promise<LineagesResponse> {
    const url = `${this.baseUrl}v1/studio/projects/${config.project}/evaluation/benchmarks/${config.benchmark}/executions/${config.execution}/lineages?page=${page}&size=${size}`

    console.log('Fetching executions from URL:', url)
    console.log('Base URL:', this.baseUrl)
    console.log('Config:', config)

    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${bearerToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        mode: 'cors'
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Response error text:', errorText)

        if (response.status === 401) {
          throw new Error('Authentication failed! Check your bearer token')
        }
        if (response.status === 404) {
          throw new Error('Execution not found. Check your project, benchmark, and execution IDs')
        }
        if (response.status === 403) {
          throw new Error('Access forbidden. Check your permissions for this project/benchmark')
        }
        throw new Error(`Failed to fetch executions: ${response.status} ${response.statusText}${errorText ? ` - ${errorText}` : ''}`)
      }

      const data = await response.json()
      console.log('Successfully fetched lineages data:', data)
      console.log('Number of lineages:', data.items?.length || 0)
      console.log('Response structure:', {
        total: data.total,
        page: data.page,
        size: data.size,
        num_pages: data.num_pages,
        items_length: data.items?.length || 0
      })
      if (data.items?.length > 0) {
        console.log('Sample lineage:', data.items[0])
        console.log('Sample lineage keys:', Object.keys(data.items[0]))
      } else {
        console.warn('No lineages found in response. Full response:', data)
      }
      return data
    } catch (error) {
      console.error('Fetch error:', error)
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to connect to Pharia Studio API. Check your internet connection and API URL.')
      }
      throw error
    }
  }

  async fetchAllLineages(
    config: ExecutionConfig,
    bearerToken: string
  ): Promise<ProcessedLineage[]> {
    console.log('Starting to fetch all lineages for config:', config)

    const firstPage = await this.fetchLineages(config, bearerToken, 1, 100)
    console.log('First page response:', {
      total: firstPage.total,
      num_pages: firstPage.num_pages,
      items_count: firstPage.items.length
    })

    let allItems = [...firstPage.items]

    // Fetch all pages if there are more
    if (firstPage.num_pages > 1) {
      console.log(`Fetching additional ${firstPage.num_pages - 1} pages...`)
      for (let page = 2; page <= firstPage.num_pages; page++) {
        const pageData = await this.fetchLineages(config, bearerToken, page, 100)
        allItems.push(...pageData.items)
        console.log(`Fetched page ${page}, total items now: ${allItems.length}`)
      }
    }

    console.log(`Total lineages fetched: ${allItems.length}`)

    // Process lineages to extract law relevancy data
    const processedLineages = allItems.map(lineage => this.processLineage(lineage))
    console.log(`Processed lineages: ${processedLineages.length}`)

    return processedLineages
  }

  private processLineage(lineage: Lineage): ProcessedLineage {
    const processed: ProcessedLineage = { ...lineage }

    console.log('Processing lineage:', lineage.id)
    console.log('Lineage input:', lineage.input)
    console.log('Lineage output:', lineage.output)
    console.log('Lineage output type:', typeof lineage.output)
    console.log('Lineage output keys:', lineage.output ? Object.keys(lineage.output) : 'none')
    console.log('Lineage task_spans:', lineage.task_spans?.length || 0)

    try {
      // Try to parse the input data
      if (lineage.input) {
        processed.parsed_input = this.parseLawRelevancyInput(lineage.input)
        processed.law_title = processed.parsed_input?.law_title || 'Unknown Law'
        console.log('Parsed input law_title:', processed.law_title)
      }

      // Try to parse the output data (task results)
      if (lineage.output) {
        processed.parsed_output = this.parseLawRelevancyOutput(lineage.output)
        processed.team_relevancies = processed.parsed_output?.team_relevancies || []
        console.log('Parsed output team_relevancies:', processed.team_relevancies?.length || 0)
        if (processed.team_relevancies && processed.team_relevancies.length > 0) {
          console.log('Sample team relevancy:', processed.team_relevancies[0])
          console.log('Sample team has chunk_relevancies:', !!processed.team_relevancies[0].chunk_relevancies)
          if (processed.team_relevancies[0].chunk_relevancies) {
            console.log('Number of chunks in first team:', processed.team_relevancies[0].chunk_relevancies.length)
          }
        }
      }

      // Try to parse expected output
      if (lineage.expected_output) {
        processed.parsed_expected_output = this.parseLawRelevancyOutput(lineage.expected_output)
        console.log('Parsed expected output')
      }

      // Calculate classification metrics
      processed.classification_metrics = this.calculateClassificationMetrics(processed)

      console.log('Final processed lineage:', processed.id, 'with', processed.team_relevancies?.length || 0, 'teams')
    } catch (error) {
      console.error('Error processing lineage:', lineage.id, error)
    }

    return processed
  }

  private parseLawRelevancyInput(input: any): LawRelevancyInput | undefined {
    try {
      // Handle different possible input structures
      if (input.law_text && input.law_title) {
        return input as LawRelevancyInput
      }

      // Check if it's nested
      if (input.input && input.input.law_text) {
        return input.input as LawRelevancyInput
      }

      // Try to extract from different structure
      if (typeof input === 'string') {
        const parsed = JSON.parse(input)
        return this.parseLawRelevancyInput(parsed)
      }

      return undefined
    } catch (error) {
      console.warn('Could not parse law relevancy input:', error)
      return undefined
    }
  }

  private transformTeamRelevancies(teamRelevancies: any[]): TeamRelevancy[] {
    return teamRelevancies.map(team => {
      // If chunk_relevancies is a dict, transform it to list format
      if (team.chunk_relevancies && typeof team.chunk_relevancies === 'object' && !Array.isArray(team.chunk_relevancies)) {
        console.log('Transforming chunk_relevancies from dict to list format for team:', team.team_name)
        const chunkRelevanciesList = Object.entries(team.chunk_relevancies).map(([chunk, relevancy]) => ({
          chunk,
          relevancy
        }))
        return {
          ...team,
          chunk_relevancies: chunkRelevanciesList
        }
      }

      // Handle new DocumentChunksGroup format - extract the text content for display
      if (team.chunk_relevancies && Array.isArray(team.chunk_relevancies)) {
        const transformedChunkRelevancies = team.chunk_relevancies.map((chunkRelevancy: any) => {
          // If chunk is a DocumentChunksGroup object, extract the concatenated content
          if (chunkRelevancy.chunk && typeof chunkRelevancy.chunk === 'object' && chunkRelevancy.chunk.concatenation_of_chunk_contents) {
            console.log('Converting DocumentChunksGroup to string for display for team:', team.team_name)
            return {
              chunk: chunkRelevancy.chunk.concatenation_of_chunk_contents,
              relevancy: chunkRelevancy.relevancy
            }
          }
          // If chunk is already a string, keep as-is
          if (typeof chunkRelevancy.chunk === 'string') {
            return chunkRelevancy
          }
          // If chunk is a DocumentChunk object with content, extract it
          if (chunkRelevancy.chunk && typeof chunkRelevancy.chunk === 'object' && chunkRelevancy.chunk.content) {
            console.log('Converting DocumentChunk to string for display for team:', team.team_name)
            return {
              chunk: chunkRelevancy.chunk.content,
              relevancy: chunkRelevancy.relevancy
            }
          }
          // Fallback - convert to string
          return {
            chunk: String(chunkRelevancy.chunk || ''),
            relevancy: chunkRelevancy.relevancy
          }
        })

        return {
          ...team,
          chunk_relevancies: transformedChunkRelevancies
        }
      }

      // If it's already in the correct format, return as-is
      return team
    })
  }

  private parseLawRelevancyOutput(output: any): LawRelevancyOutput | undefined {
    try {
      console.log('Parsing law relevancy output:', output)
      console.log('Output type:', typeof output)
      console.log('Output is array:', Array.isArray(output))
      console.log('Output keys:', typeof output === 'object' && output ? Object.keys(output) : 'none')

      // Direct team relevancies array
      if (Array.isArray(output)) {
        console.log('Found direct array of team relevancies')
        return { team_relevancies: this.transformTeamRelevancies(output) }
      }

      // Wrapped in team_relevancies property
      if (output.team_relevancies && Array.isArray(output.team_relevancies)) {
        console.log('Found team_relevancies property with array')
        return { team_relevancies: this.transformTeamRelevancies(output.team_relevancies) }
      }

      // Handle string JSON
      if (typeof output === 'string') {
        console.log('Parsing string JSON output')
        const parsed = JSON.parse(output)
        return this.parseLawRelevancyOutput(parsed)
      }

      // Check for nested structure
      if (output.output) {
        console.log('Found nested output structure')
        return this.parseLawRelevancyOutput(output.output)
      }

      // Check if it's a flat object that might contain team data
      if (typeof output === 'object' && output !== null) {
        console.log('Checking object for team relevancy patterns...')
        // Look for any property that might contain team data
        for (const [key, value] of Object.entries(output)) {
          if (Array.isArray(value) && value.length > 0) {
            // Check if this array contains team-like objects
            const firstItem = value[0] as any
            if (firstItem && typeof firstItem === 'object' &&
                (firstItem.team_name || firstItem.team_id || firstItem.is_relevant !== undefined)) {
              console.log(`Found team relevancies in property: ${key}`)
              return { team_relevancies: this.transformTeamRelevancies(value) }
            }
          }
        }
      }

      console.warn('Could not identify team relevancy structure in output')
      return undefined
    } catch (error) {
      console.warn('Could not parse law relevancy output:', error)
      return undefined
    }
  }

  async fetchBenchmarkInfo(
    config: Pick<ExecutionConfig, 'project' | 'benchmark'>,
    bearerToken: string
  ): Promise<{ name: string; description: string; task_type: string }> {
    const url = `${this.baseUrl}v1/studio/projects/${config.project}/evaluation/benchmarks/${config.benchmark}`

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${bearerToken}`,
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication failed! Check your bearer token')
      }
      throw new Error(`Failed to fetch benchmark info: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  }

  async fetchExecutionMetadata(
    config: ExecutionConfig,
    bearerToken: string
  ): Promise<{ name: string; status: string; created_at: string; created_by: string }> {
    const url = `${this.baseUrl}v1/studio/projects/${config.project}/evaluation/benchmarks/${config.benchmark}/executions/${config.execution}`

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${bearerToken}`,
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication failed! Check your bearer token')
      }
      throw new Error(`Failed to fetch execution metadata: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  }

  private calculateClassificationMetrics(processed: ProcessedLineage): ClassificationMetrics {
    // Default values
    const defaultMetrics: ClassificationMetrics = {
      is_true_positive: false,
      is_false_positive: false,
      is_true_negative: false,
      is_false_negative: false,
      expected_relevant: false,
      actual_relevant: false
    }

    try {
      // Determine if the legal act is expected to be relevant (expected_output = true means relevant for any team)
      let expectedRelevant = false
      if (processed.expected_output && typeof processed.expected_output === 'boolean') {
        expectedRelevant = processed.expected_output
      } else if (processed.parsed_expected_output?.team_relevancies) {
        // If we have team relevancies in expected output, check if any team should find it relevant
        expectedRelevant = processed.parsed_expected_output.team_relevancies.some(team => team.is_relevant)
      }

      // Determine if the legal act is actually classified as relevant (any team found it relevant)
      const actualRelevant = processed.team_relevancies?.some(team => team.is_relevant) || false

      // Calculate classification type
      const isPositive = actualRelevant  // Classified as relevant
      const isNegative = !actualRelevant // Classified as not relevant
      const shouldBeRelevant = expectedRelevant
      const shouldNotBeRelevant = !expectedRelevant

      return {
        expected_relevant: expectedRelevant,
        actual_relevant: actualRelevant,
        is_true_positive: isPositive && shouldBeRelevant,   // Correctly identified as relevant
        is_false_positive: isPositive && shouldNotBeRelevant, // Incorrectly identified as relevant
        is_true_negative: isNegative && shouldNotBeRelevant,  // Correctly identified as not relevant
        is_false_negative: isNegative && shouldBeRelevant     // Incorrectly identified as not relevant
      }
    } catch (error) {
      console.warn('Error calculating classification metrics for lineage:', processed.id, error)
      return defaultMetrics
    }
  }
}
