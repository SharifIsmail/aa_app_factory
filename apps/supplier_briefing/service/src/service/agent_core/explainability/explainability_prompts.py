SUMMARY_EXPLAINABILITY_PROMPT = """Analyze the Python code after the `Code` keyword and the tool execution logs after the `Tool Logs` keyword.
List only the operations that were executed and which received, manipulated, or augmented data from pandas DataFrames.
Use both the code and the tool logs to understand what data operations were actually performed.

# Guidelines:
Focus on operations that load, filter, transform, aggregate, or analyze data from the risk analysis system.
Ignore any (tool) calls to `present_results`, `final_answer`, or `final_result`.
Ignore print statements.
Ignore simple assignments that do not handle or transform data.
If there were no operations on the data and no relevant tool log calls, answer with {no_data_operations_string}.
If there are relevant tool calls, you should always explain what they did and never answer with {no_data_operations_string}.
If the data analysis agent is invoked, simply state that it handed over to that agent. 

# Output Format:
Present your answer as a bulleted list with no additional text or prefixes.
The answer should be understandable for a non-technical user who only knows the original datasets which are the Excel files
listed below.
Do not use technical phrases from python code. For example, do not refer to `DataFrames` but to `Tables` instead.
Take into account how the retrieved data relates to the original dataset (not the derived ones).

# How the original datasets relate to the data used in the tools:
{file_creation_map}

# Examples:

**Example 1:**
Code:
```python
# Get branch risk data for retail sector
branch_data = get_branch_risk_matrix('Lebensmitteleinzelhandel', 'Brutto', 'T0')
# Inspect the retrieved data
inspection_result = inspect_data(dataframe=branch_data)
# Save results for further analysis
saved_id = save_data(branch_data, "Branch risk analysis for retail sector", "analysis_result")
present_results(data_ids=[saved_id])
```

Tool Logs:
Tool 1: get_branch_risk_matrix
Description: This tool retrieves risk matrix data for a specific branch (industry sector). It returns a pandas.DataFrame or pandas.Series containing the risk information.
Data source: risk_per_branch.parquet
Result: Retrieved risk matrix data for Lebensmitteleinzelhandel with Brutto risk type and T0 tier

Tool 2: inspect_data
Description: Inspects a DataFrame or Series by showing complete data for small datasets or schema information for large ones. Provide either data_id (for stored data) or dataframe object directly.
Result: Displayed schema information for DataFrame with 15 rows × 12 columns

Tool 3: save_data
Description: Saves a pandas DataFrame or Series to the repository and returns a unique ID. Use the returned ID in present_results tool to include this data in the final report.
Result: Saved DataFrame with unique ID: data_abc12345

Expected output:
• Retrieved risk matrix data for the retail food sector (Lebensmitteleinzelhandel) filtered by Brutto risk type and T0 supplier tier. The risk matrix data was extracted from the Brutto_Datei.xlsx and the Konkrete_Risiken.xlsx to create a risk overview per industry branch and country.
• Inspected the structure and content of the retrieved risk data

**Example 2:**
Code:
```python
# Get resource risk profiles for multiple materials
resource_risks = get_resource_risk_profile(['HOLZ', 'HOLZPRODUKTE'], limit_results=20)
# Get business partner summary
partner_info = summarize_business_partner('10000')
# Inspect both datasets
inspect_data(dataframe=resource_risks)
present_results(data_ids=["data_456"])
```

Tool Logs:
Tool 1: get_resource_risk_profile
Description: This tool retrieves risk profiles for specific resources (raw materials) by exact name match.
Data source: resource_risks_processed.parquet
Result: Retrieved risk profiles for 2 resources with all risk columns, returning 2 matching records

Tool 2: summarize_business_partner
Description: This tool summarizes business partner data from a specified file
Data source: business_partners.parquet
Result: Generated business partner summary for ID: 10000 with metadata and risk summaries

Tool 3: inspect_data
Description: Inspects a DataFrame or Series by showing complete data for small datasets or schema information for large ones
Result: Displayed complete DataFrame (2 rows × 8 columns) with resource risk data

Expected output:
• Retrieved risk profiles for wood-based resources (HOLZ, HOLZPRODUKTE) including country origins and risk assessments across legal positions. The data comes from the resource_risks.xlsx.
• Retrieved comprehensive business partner summary including metadata and maximum concrete risks across supplier tiers. The business partner summary data was extracted from the Brutto_Datei.xlsx and the Konkrete_Risiken.xlsx to create a long-format risk table per partner.
• Inspected the complete resource risk dataset showing all risk columns and country origin information

**Example 3:**
Code:
```python
# Set analysis parameters
analysis_type = "comprehensive"
threshold = 3.0
print(f"Starting {{analysis_type}} analysis with threshold {{threshold}}")
present_results(data_ids=[])
```

Tool Logs:
No tool executions recorded

Expected output:
{no_data_operations_string}

**Example 4:**
Code:
```python
result = invoke_data_analysis_agent("Find the riskiest resource for each country")
```

Tool Logs:
Tool 1: invoke_data_analysis_agent
Description: Invokes the data analysis agent to perform pandas data manipulations and analytics. 
        The agent has access to all data files and can perform sophisticated data analysis tasks. 
        Use this tool for data analytics tasks that go beyond the capabilities of more specialized tools.
        Use this tool always in a separate python code block. Do not build complex logic around this tool call.
        Returns a string of with the result of the agents solution. The answer will contain information about the saved dataframes that you can then use.

Result: New Data saved by the Data Analysis Agent with data_id xyz + preview info

Expected output:
* Query was handed over to the data analysis agent

Now analyze this:
Code:
{step_model_output}

Tool Logs:
{tool_logs_string}

Formulate your output in {output_language}
"""
