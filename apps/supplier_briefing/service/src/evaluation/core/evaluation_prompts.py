TEXT_COMPARISON_PROMPT = """Compare these two responses and determine if they have the same meaning (same facts).

## Golden Response:
{golden_text}

## Current Response:
{current_text}

## Task:
Do these responses convey the same facts? Ignore style, wording, or formatting differences.

## Important Guidelines:
- Focus on factual content, not presentation format

Respond with this JSON format:
{{
    "reasoning": "Brief explanation"
    "is_match": true/false,
}}

is_match = true if both responses contain the same facts
is_match = false if facts differ"""


DATAFRAME_VIBE_PROMPT = """You are judging how similar two sets of pandas dataframes/series are in terms of factual content.

Research question:
{research_question}

Golden dataframes (reference):
{golden_json}

Current dataframes (evaluated):
{current_json}

Scoring rules (0.0 to 1.0):
- ~0.9–1.0: Same factual content even if the format, ordering, or minor column naming differs. 
   Golden content matches one of the current dataframes almost completely (i.e. there are simply more data objects in the current dataframes).
- ~0.6–0.9: Large factual overlap (most rows/columns or facts align).
- ~0.3-0.6: Little factual overlap (many more/less rows/columns in the data objects). Data object does not answer the question well.
- ~0.1-0.3: Generally considered a wrong answer to the research question, but contains sub-parts that are correct.
- ~0.0: No meaningful factual/content overlap.

Important Guidelines:
- Ignore purely stylistic/ordering differences. Focus on whether the same facts are present.
- Consider both the presence of the same rows/values and alignment of columns/fields.
- If multiple dataframes exist, reason at the set level: whether golden dataframes are covered/contained by current.

Respond ONLY with this JSON (no markdown or extra text):
{{
  "score": <float between 0 and 1>,
  "reasoning": "brief explanation of overlap, containment, or differences"
}}"""
