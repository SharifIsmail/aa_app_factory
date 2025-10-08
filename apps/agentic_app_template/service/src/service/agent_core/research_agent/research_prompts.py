RESEARCH_AGENT_PROMPT = """
### Task: Perform Basic Research on a Given Topic

Your task is to use the available tools to perform basic research on the topic: "{topic}".

You should gather as much relevant information as you can find using tools like `google_search_tool`, `visit_webpage`, and others provided.

---

### Your Goals:

- Find useful, factual, or interesting information about the topic.
- Use the tools to search, browse, and extract relevant content.
- Focus on collecting a wide range of information, not verifying it.
- Include exact quotes or snippets from the pages you visit.
- For each piece of information, always include the **full source URL**.

---

### Output Format:

For each finding, include:
DATA:
Extensive data about the finding.
SOURCE:
The link to the page where the info was found.

"""


RESEARCH_AGENT_PROMPT_PREVIOUS_DATA = """


You already found these data:
{old_incident_queue}
No need to research about these topics again, focus on other new research directions in this iteration!


"""


EXTRACT_STRUCTURED_DATA_PROMPT = """
You are tasked with transforming structured JSON data from a research agent into a detailed XML report. The JSON contains user queries, search engine results, parsed web content, and synthesized insights. Your job is to process **all** available data and express it as an XML document in the required structure.

The topic of the original user query can be from **any field** (e.g., arts, science, cities, technologies), so your output must remain **domain-agnostic** and abstract. Do **not** use topic-specific labels like "Geography", "History", or "Technology". Instead, generate abstract, transferable language that reflects structure, interaction, evolution, influence, uncertainty, etc.

---

### Input Data

USER_QUERY:
{user_query}

RESEARCH_RESULTS__COMPUTED_SO_FAR:
{research_results_computed_so_far}

RAW_DATA_BASED_ON_GOOGLE_SEARCH:
{raw_data_based_on_google_search}

RAW_DATA_BASED_ON_WEBPAGES:
{raw_data_based_on_webpages}

---

### Instructions

1. Your primary goal is to directly answer the user query using all available input data.
2. For each piece of information in your response, include the source URL whenever possible.
3. If a source URL is not available, explicitly state that the information is synthesized from multiple sources.
4. Ensure all insights and findings are directly relevant to answering the user query.
5. Maintain high accuracy and avoid speculation - if information is uncertain, clearly indicate this.

---

###  XML STRUCTURE (Required Output Format)

<AgenticReport>

  <Summary>
    <Text>
      Provide a fluent, integrated explanation addressing the original request.
      - Synthesize all relevant data across tools and sources.
      - Reflect multiple conceptual angles, emergent contradictions, and significant latent patterns.
      - Do **not** use bullet points or lists.
      - Do not refer to the original question explicitly.
      - Make the text readable and logically connected.
      - Include source URLs for key claims and information.
    </Text>
  </Summary>

  <KeyInsights>
    Provide compact, self-contained statements that highlight atomic insights.
    #IMPORTANT: Be verbose! Extract as many insights as necessary for the user query!

    For each, create:
    <Insight category="[abstract category]" source="[URL if available]">[insight statement]</Insight>

    Guidelines:
    - Each insight must be short, declarative, and able to stand on its own.
    - The `category` must reflect an abstract dimension (e.g., "Tensions", "Interpretations", "Behaviors", "Frameworks", "Patterns", "Dependencies").
    - Avoid repetition. Group related facts under one insight.
    - Include source URLs whenever possible.
  </KeyInsights>

  <DetailedFindings>
    Break down deeper findings into thematic sections.
    #IMPORTANT: Be verbose! Extract as many findings as necessary for the user query!

    Each section has:
    <Section title="[abstract theme]">
      <Paragraph source="[URL if available]">Text paragraph 1...</Paragraph>
      <Paragraph source="[URL if available]">Text paragraph 2 (if needed)...</Paragraph>
    </Section>

    Guidelines:
    - Use abstract, conceptual section titles (e.g., "Underlying Processes", "Emergence", "Cross-Influences", "Stability Factors", "Representational Layers").
    - Paragraphs must integrate and explain — not just rephrase facts.
    - Use coherent and flowing language, no lists or fragments.
    - Include source URLs for each paragraph when available.
  </DetailedFindings>

  <ResearchQuality>
    <ConfidenceScore>[0.0 to 1.0]</ConfidenceScore>
    <Reasoning>
      Explain how complete and reliable the research output is.
      Consider:
      - Depth and variety of input sources
      - Cross-source agreement or contradiction
      - Clarity, gaps, or uncertainty in source content
      - Agent tool behavior or limitations
    </Reasoning>
  </ResearchQuality>

</AgenticReport>
"""
