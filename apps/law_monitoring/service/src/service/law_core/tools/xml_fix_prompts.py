FIX_XML_PROMPT = """
You are an expert XML formatter and debugger. You will receive a string that is supposed to be XML, but it might be malformed.
Your task is to fix it and return a valid XML string through a structured three-stage approach:

Stage 1: Analysis
- Carefully examine the XML string and identify all potential issues
- Look for unclosed tags, mismatched tags, invalid nesting, missing declarations, improper escaping, etc.
- Document each issue you find with specific details about what's wrong and where
- Be extremely thorough in your analysis, considering both syntax and structural problems

Stage 2: Solution Planning
- For each issue identified in Stage 1, develop a specific solution
- Explain your reasoning for each fix you plan to implement
- Consider multiple approaches when appropriate and justify your chosen solution
- Describe how your fixes will maintain the original intent of the XML

Stage 3: Implementation
- Apply all your planned fixes to create a valid XML structure
- Verify that all tags are properly closed and nested
- Ensure the overall structure follows XML standards
- Present the complete fixed XML

Please be as verbose as possible throughout all stages, showing your detailed reasoning process and chain of thought.

After completing all three stages, provide the final fixed XML string in a code block with the xml language identifier, like this:
```xml
<your_fixed_xml_here>
```

Here is the XML string you need to fix:
{xml_string}
"""
