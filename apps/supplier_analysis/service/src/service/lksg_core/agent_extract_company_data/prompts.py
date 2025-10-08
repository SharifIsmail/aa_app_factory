EXTRACT_COMPANY_DATA_PROMPT = """
### Task: Gather & Verify Initial Supplier Data for a company

Your task is to gather and verify initial supplier data for the company	{company_name}.  

This is part of a supplier due diligence process, and the goal is to confirm the identity, locations, industry classification, and ownership details before proceeding to risk assessment.  

### Objective:
- Ensure we are assessing the correct supplier before moving forward.  
- Identify company name, locations, industry classification, and ownership structure.  
- Do NOT assess risks, certifications, or compliance at this stage. That will be covered in a later step.  

---

### Validation & Cross-Checking Requirements: 

-  Each piece of data must be validated from at least two independent sources before being considered reliable.  
- Significant effort must be put into cross-checking information — for example:  
   - If data is found in an official registry, check it against search engine results or another business directory.  
   - If data is retrieved from a Google search, verify it within official databases or industry reports.  
- Any inconsistencies, contradictions, or unverifiable information must be flagged for human review. 
- If a critical data point remains inconclusive despite multiple verification attempts, explicitly mention what is missing and possible reasons.  

---

### Key Data Points to Collect (With Full Justification for Each)  

For each of the following categories, present the data individually, along with:  
- Sources used for verification (at least two required) WITH FULL SOURCE URLs.  
- Reasoning behind why the data is considered reliable or uncertain.  
- How cross-checking was performed (e.g., searched for confirmation, found discrepancies, etc.).  
- Any inconsistencies or flags for human review. 
- MANDATORY: The exact result provided by each data source.

---

#### Company Identity & General Information  
- Full legal name and any alternative names (subsidiaries, former names).  
- Official business registration details (e.g., registration number, government database entry).  
- Headquarters location (city, country).  

####  Locations & Operations  
- Factory or office locations and verification from industry sources or government listings.  
- Presence in industry-specific directories or trade organizations.  

#### Industry & Business Sector  
- Industry classification (e.g., Manufacturing, Oil & Gas, Banking, etc.).  
- Main products or services (validated via company filings, directories, or supplier databases).  

#### Ownership & Business Structure  
- Parent company, shareholders, or ultimate beneficial owners  
- Key directors or executives (verified through company records, directories, and secondary sources).  

#### Financial Information  
- Market value, revenue, or other financial metrics (if available)
- Stock information (if publicly traded)
- Financial performance indicators
- Recent major financial events (acquisitions, mergers, etc.)

---

### Handling Conflicting or Missing Data  
- If sources provide conflicting information, highlight the discrepancies and the likely cause.  
- If there is too little evidence to confirm a data point, indicate what is missing and potential follow-up steps.  
- If multiple names or addresses appear across sources, document any alias or subsidiary issues.  
- If financial or ownership records are outdated or incomplete, flag them for additional verification.  


### Approach to follow:

1. Initial Data Retrieval: Start by invoking the `google_search_tool` tool to figure out the company website domain.
2. Use `company_data_by_domain` tool to gather initial company data based on the company website domain (remove www. from the domain if present).
3.  Verification and Enrichment:
    *   Use the `google_search_tool` to verify the data obtained in the previous step.
    *   Employ multiple searches to cross-validate information from diverse sources.
    *   Focus on enriching the data with details about locations, industry classifications, and ownership structures.
    *   Use the `visit_webpage` tool to visit company websites and also open the pages returned via google search to gather more information.
4.  Iterative Refinement: Repeat the verification and enrichment process as many times as necessary to resolve inconsistencies, fill in missing information, and ensure data reliability.
5. Don't be shy about invoking the tools for as many times as needed. Time and cost are not an issue.

Important Considerations:

*   Prioritize official sources such as government registries, industry reports, and the company's official website.
*   When discrepancies arise, investigate the potential causes and document them in the final output.
*   Ensure that all data points are validated by at least two independent and reliable sources.

---

### Final Output Format  
- Each piece of information is presented separately, not in a table. 

### IMPORRTANT:
It is mandatory to provide as much information as possible for the human reviewer so that he/she can fully trust the findings before moving forward.

- For each data point, include:  
  1. The raw data (e.g., "Company name: ABC Manufacturing Ltd.").  
  2. Sources checked (MUST include complete URLs or database references for all sources).  
  3. Verification process (how the data was validated, methods used).
  4. Cross-check results (whether the data matched across sources).  
  5. Any issues or uncertainties (contradictions, missing details, potential alias concerns).  
  6. MANDATORY: The exact verbatim result provided by each data source for this specific data point.

  
**** IMPORTANT ****

1. At each step, in the 'Thought:' sequence, besides the reasoning, also include:

# DATA I HAVE GATHERED SO FAR:
 - what data you have gathered so far (actually list all the data with all the details so that you don't forget it!); 

 Some sample data to use as a template: 
- Company name: [Company A](SOURCE URL: https://companyinfo123.com/company-a)  
- RC number: [XXXXXX](SOURCE URL: https://regcheck456.net/rc-number)  

NOTICE THAT EACH DATA POINT MUST HAVE A SOURCE URL in paranthesis!
 
# DATA I STILL NEED TO GATHER:
 - what data is still missing
 

- When writing Python code keep in mind that the authorized imports are only these: ['collections', 'random', 'queue', 'time', 'stat', 'unicodedata', 'math', 'datetime', 're', 'statistics', 'itertools']. Do NOT use any other imports!

- When using the final_answer tool, make sure to include the all the data you have gathered with all the details AND source URL for each data point!
"""


# """

# ## IMPORTANT CODE GENERATION GUIDELINES:

# - USE MINIMAL CODE: Generate only the essential code needed to invoke tools - avoid complex data structures, loops, or algorithmic approaches
# - DIRECT TOOL INVOCATION : Call tools directly with the required parameters - do not write lots of preprocessing or postprocessing logic! It's OK to do preprocessing and postprocessing, but limit it to only what is necessary.
# - ONE TASK, ONE (or few) TOOL CALL: don't invoke ten tools in sequence in a single step.
# - AVOID CODE COMPLEXITY.
# - SEQUENTIAL EXECUTION: Generate code as a series of simple, sequential tool invocations"""

PROCESS_IN_MEMORY_DATA_PROMPT = """
# Task: Process Raw Company Data into Structured Company Profile

Your task is to analyze the raw data collected about a company and organize it into a comprehensive company profile. Each piece of information must include ALL source attributions with ACTUAL URLs whenever possible.

## Input
You will receive:
1. A JSON array containing raw data elements collected from various sources about a company
2. The company name that was initially searched for

## Processing Requirements
- Extract and organize all relevant company information into clear categories
- Include ALL ACTUAL SOURCE URLs for EVERY piece of information whenever possible
- Count and display the number of sources for each data point
- Present ALL versions of data when contradictions exist, without attempting to resolve them
- Flag contradictory information explicitly
- Maintain all variations of data points rather than selecting a "correct" version

## Required Output Categories
For each of the following categories, include ALL available information with source URLs:

### 1. Company Identity
- Legal name (including all variations found)
- Registration number
- Registration date
- Company status 
- Business entity type (PLC, LTD, etc.)

### 2. Locations
- All addresses found (headquarters, branches, registered address)
- State/City information

### 3. Industry & Business
- Industry classification
- Main products/services
- Any certifications or memberships

### 4. Contact Information
- Email addresses
- Phone numbers
- Website
- Social media profiles

### 5. Ownership & Management
- Parent company (if applicable)
- Key executives
- Shareholders information (if available)

### 6. Financial Information
- Any available metrics (market value, revenue, etc.)
- Stock information if publicly traded

## IMPORTANT: SOURCE URL REQUIREMENTS
- EVERY data point should have actual web URLs as its sources (e.g., https://cac.gov.ng, https://example.com)
- Include a count of sources for each data point (e.g., "Sources: 3")
- Avoid using generic phrases like "Provided company data" as sources
- If a URL appears in the raw JSON data (source_url field), use that specific URL
- If the same data appears in multiple sources, list ALL those sources, not just one or two
- For data without a proper URL source, note "No URL source" but still include the information

## Example Output Format:

# Company Profile: XYZ Manufacturing Ltd

## Company Identity
* **Legal Name**: XYZ Manufacturing Ltd
  * Sources: 3
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Source: https://postapp.cac.gov.ng/search?rc=123456
  * Source: https://businessinfo.gov.ng/directory/xyz

* **Legal Name**: XYZ Manufacturing Limited
  * Sources: 2
  * Source: https://xyz-manufacturing.com/about
  * Source: https://linkedin.com/company/xyz-manufacturing
  * Note: Contradicts information from https://searchapp.cac.gov.ng/company/123456

* **Registration Number**: RC123456
  * Sources: 4
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Source: https://postapp.cac.gov.ng/search?rc=123456
  * Source: https://businessinfo.gov.ng/directory/xyz
  * Source: https://xyz-manufacturing.com/about

* **Registration Date**: 2010-05-12
  * Sources: 2
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Source: https://postapp.cac.gov.ng/search?rc=123456

* **Company Status**: Active
  * Sources: 1
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Note: Single source information

## Locations
* **Headquarters Address**: 15 Industrial Way, Lagos, Nigeria
  * Sources: 3
  * Source: https://xyz-manufacturing.com/contact
  * Source: https://linkedin.com/company/xyz-manufacturing
  * Source: https://businessinfo.gov.ng/directory/xyz

* **Factory Location**: Plot 27, Industrial Estate, Ogun State
  * Sources: 1
  * Source: https://xyz-manufacturing.com/locations
  * Note: Single source information

## Contact Information
* **Email**: info@xyz-manufacturing.com
  * Sources: 2
  * Source: https://xyz-manufacturing.com/contact
  * Source: https://businessdirectory.com/xyz-manufacturing

* **Phone**: +234 801 234 5678
  * Sources: 2
  * Source: https://xyz-manufacturing.com/contact
  * Source: https://linkedin.com/company/xyz-manufacturing

* **Website**: https://xyz-manufacturing.com
  * Sources: 3
  * Source: https://linkedin.com/company/xyz-manufacturing
  * Source: https://businessdirectory.com/xyz-manufacturing
  * Source: https://businessinfo.gov.ng/directory/xyz

## Output Format
Provide the information in a structured markdown format:

# Company Profile: [COMPANY NAME]

## Company Identity
* **[Data Point]**: [Value]
  * Sources: [NUMBER OF SOURCES]
  * Source: [URL1]
  * Source: [URL2]
  * [Additional sources as needed]

* **[Same Data Point - Contradictory Value]**: [Different Value]
  * Sources: [NUMBER OF SOURCES]
  * Source: [URL3]
  * Source: [URL4]
  * Note: Contradicts information from [URL1]

## Locations
* **[Data Point]**: [Value]
  * Sources: [NUMBER OF SOURCES]
  * Source: [URL1]
  * Source: [URL2]

[Continue for each section]

## Important requirements:
1. EVERY piece of information should include URLs of its sources whenever possible
2. When contradictory information exists, present ALL versions with their respective sources
3. Flag explicitly when contradictions exist using a "Note: Contradicts information from [other source]" line
4. If information appears in only one source, note it as "Single source information"
5. Do not fabricate or infer information that is not explicitly present in the input data
6. Do not attempt to determine which source is more reliable - present all data equally
7. For data without a proper URL source, indicate "No URL source" but still include the valuable information

Here's the company data: {company_data}.

Here's the complete log of the data research process: {in_memory_data}.
"""

PROVIDE_FEEDBACK_COMPANY_DATA_PROMPT = """### Task: Validate & Guide the Verification of Supplier Data for a company

Your task is to analyze the collected supplier data for {company_name} and provide detailed feedback ONLY on issues that require correction or further investigation.

The collected data is as follows:
{company_data}

---

### Objective:
- Only focus on data points that lack proper validation or contain inconsistencies
- Provide clear, actionable instructions for resolving each issue
- Ignore data points that are already properly validated (with at least two independent sources)
- Structure your response with detailed reasoning followed by concise action items

---

### Validation & Deep Cross-Checking Requirements

For each data point, silently check:
- Has it been verified from at least two independent sources?
- Are the sources trustworthy and official (government databases, financial records, etc.)?
- Is the data up-to-date and consistent across sources?
- Is any critical information missing?

Only report on items that fail these checks.

---

### Response Format

Your response must have two clearly separated sections:

1. **Reasoning Section** - Start with "====REASONING===="
   - Provide detailed analysis of each problematic data point
   - Explain why each item needs further verification
   - Include thorough chain-of-thought reasoning
   - Discuss potential concerns or inconsistencies

2. **Tasks Section** - Start with "====TASKS===="
   - List only specific, actionable tasks to resolve each issue
   - Format each task between "---" separators
   - Be direct and concise with instructions (no explanations needed)
   - Phrase tasks as clear directives (e.g., "Verify company registration number with X source")
   - Do NOT mention here data points that are already properly verified with multiple sources
   - Do NOT provide here general advice or theoretical information about validation
   - Do NOT include preambles, summaries, or conclusions in the this section
   - Do NOT use vague language in the tasks section (e.g., "look into this further")
   - Do NOT include the word "Shareholders" in the tasks section.

---

### Handling Special Cases

⚠️ Conflicting Information
- In the reasoning section: Analyze the nature and significance of the contradiction
- In the tasks section: Provide clear steps to resolve the conflict

⚠️ Missing Data
- In the reasoning section: Explain why this data point is critical
- In the tasks section: List specific sources to check for this information

⚠️ Possible Red Flags
- In the reasoning section: Detail why something appears suspicious
- In the tasks section: Provide specific verification steps

---

### Example Response Structure:

====REASONING====
The company's registration number 123456 is problematic for several reasons. First, it appears in only a single source (the company website) without independent verification. Second, the format is inconsistent with standard Nigerian registration numbers, which typically include...

[Additional detailed reasoning for other problematic data points...]

====TASKS====
---
Verify company registration number 123456 through CAC portal and at least one additional government database
---
Confirm the current CEO's name through official company filings and an independent business directory
---
[Additional specific tasks...]
"""


ADDRESS_FEEDBACK_PROMPT = """

### Task: Address Reviewer Feedback & Fix Supplier Data Issues

Your task is to review and fix the highlighted issues in the previously gathered supplier data for {company_name}, based on human reviewer feedback. 

This is a critical step in the supplier due diligence process to ensure the accuracy, completeness, and reliability of company data before moving forward with risk assessment.  

---

### Objective:
- Address all inconsistencies, missing data, and verification gaps highlighted by the human reviewer.  
- Ensure that all corrections are well-documented, with sources and reasoning explicitly stated.  

---

---

### MANDATORY SOURCE URL REQUIREMENTS:

- EVERY single data point MUST have at least one source URL - no exceptions
- URLs must be actual web addresses (e.g., https://cac.gov.ng/search?rc=123456)
- Generic references like "company website" are NOT acceptable - use the full URL
- Count the number of source URLs for each data point (e.g., "Sources: 2")
- When using a search tool, include the full search URL with query parameters
- When using the visit_webpage tool, include the exact URL visited
- If information appears in multiple places on the same site, list each specific page URL

---
### Final Output Format  
- Each fixed data point must be presented separately, not in a table.  
- Sample outputs:
   "The updated key executives are: John Doe and Jane Smith. The source URL for this data is: https://xyz-manufacturing.com/about"
   "The updated registration number is: RC123456. The source URL for this data is: https://searchapp.cac.gov.ng/company/123456"
   "The updated industry classification is: Manufacturing - Industrial Equipment. The source URL for this data is: https://manufacturersassociation.org.ng/members/axiom-industries"
- Notice there is ALWAYS a source URL for each data point!
- Notice that the output describes the data point that was updated.

**** IMPORTANT!!!!!! *****
- Only invoke a single tool per iteration!
- Python code must be minimal and to the point!
- Do not use Python code for anything other than tool invocations!

---

Here's the human reviewer's feedback:
{feedback}

The original company data is:
{original_company_data}

"""


FINALIZE_CORRECTED_COMPANY_DATA_PROMPT = """
# Task: Generate Final Corrected Company Profile Based on Original Data, Feedback, and Fixes

Your task is to analyze and integrate three sets of information about {company_name}:
1. The original extracted company data
2. The feedback provided by reviewers
3. The fixes applied to address the feedback

You must produce a final, comprehensive company profile that properly consolidates all information with proper source attribution.

## Processing Requirements
- Combine all correct data from the original extraction with confirmed fixes
- Include ALL SOURCE URLs for EVERY piece of information
- Count and display the number of sources for each data point
- Present ALL versions of data when contradictions remain, without attempting to resolve them
- Maintain all variations of data points rather than selecting a "correct" version
- Identify where fixes have resolved issues raised in the feedback

## Required Output Categories
For each of the following categories, include ALL available information with source URLs:

### 1. Company Identity
- Legal name (including all variations found)
- Registration number
- Registration date
- Company status 
- Business entity type (PLC, LTD, etc.)

### 2. Locations
- All addresses found (headquarters, branches, registered address)
- State/City information

### 3. Industry & Business
- Industry classification
- Main products/services
- Any certifications or memberships

### 4. Contact Information
- Email addresses
- Phone numbers
- Website
- Social media profiles

### 5. Ownership & Management
- Parent company (if applicable)
- Key executives
- Shareholders information (if available)

### 6. Financial Information
- Any available metrics (market value, revenue, etc.)
- Stock information if publicly traded

## IMPORTANT: SOURCE URL REQUIREMENTS
- EVERY data point should have actual web URLs as its sources (e.g., https://cac.gov.ng, https://example.com)
- Include a count of sources for each data point (e.g., "Sources: 3")
- Avoid using generic phrases like "Provided company data" as sources
- If a URL appears in the data, use that specific URL
- If the same data appears in multiple sources, list ALL those sources, not just one or two
- For data without a proper URL source, note "No URL source" but still include the information

## Example Output Format:

# Company Profile: XYZ Manufacturing Ltd

## Company Identity
* **Legal Name**: XYZ Manufacturing Ltd
  * Sources: 3
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Source: https://postapp.cac.gov.ng/search?rc=123456
  * Source: https://businessinfo.gov.ng/directory/xyz

* **Legal Name**: XYZ Manufacturing Limited
  * Sources: 2
  * Source: https://xyz-manufacturing.com/about
  * Source: https://linkedin.com/company/xyz-manufacturing
  * Note: Contradicts information from https://searchapp.cac.gov.ng/company/123456

* **Registration Number**: RC123456
  * Sources: 4
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Source: https://postapp.cac.gov.ng/search?rc=123456
  * Source: https://businessinfo.gov.ng/directory/xyz
  * Source: https://xyz-manufacturing.com/about

* **Registration Date**: 2010-05-12
  * Sources: 2
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Source: https://postapp.cac.gov.ng/search?rc=123456

* **Company Status**: Active
  * Sources: 1
  * Source: https://searchapp.cac.gov.ng/company/123456
  * Note: Single source information

## Locations
* **Headquarters Address**: 15 Industrial Way, Lagos, Nigeria
  * Sources: 3
  * Source: https://xyz-manufacturing.com/contact
  * Source: https://linkedin.com/company/xyz-manufacturing
  * Source: https://businessinfo.gov.ng/directory/xyz

* **Factory Location**: Plot 27, Industrial Estate, Ogun State
  * Sources: 1
  * Source: https://xyz-manufacturing.com/locations
  * Note: Single source information

## Contact Information
* **Email**: info@xyz-manufacturing.com
  * Sources: 2
  * Source: https://xyz-manufacturing.com/contact
  * Source: https://businessdirectory.com/xyz-manufacturing

* **Phone**: +234 801 234 5678
  * Sources: 2
  * Source: https://xyz-manufacturing.com/contact
  * Source: https://linkedin.com/company/xyz-manufacturing

* **Website**: https://xyz-manufacturing.com
  * Sources: 3
  * Source: https://linkedin.com/company/xyz-manufacturing
  * Source: https://businessdirectory.com/xyz-manufacturing
  * Source: https://businessinfo.gov.ng/directory/xyz

## Additional Information from Feedback and Fixes
* **Feedback Addressed**: [Brief explanation of how feedback was addressed with the fixes]
* **Remaining Issues**: [Any issues that couldn't be resolved by the fixes]

## Important requirements:
1. EVERY piece of information should include URLs of its sources whenever possible
2. When contradictory information exists, present ALL versions with their respective sources
3. Flag explicitly when contradictions exist using a "Note: Contradicts information from [other source]" line
4. If information appears in only one source, note it as "Single source information"
5. Do not fabricate or infer information that is not explicitly present in the input data
6. Do not attempt to determine which source is more reliable - present all data equally
7. For data without a proper URL source, indicate "No URL source" but still include the valuable information

Here's the company data: {company_name}
Original company data: {original_company_data}
Feedback: {feedback}
Fixes: {fixes}
"""

GENERATE_XML_COMPANY_DATA_PROMPT = """
### Task: Convert Final Corrected Supplier Data into XML Format

Your task is to convert the provided company data for {company_name} into a well-structured XML document while preserving the original content exactly.  
DO NOT modify, summarize, or omit any information. Every detail must remain identical to the input.  

---

### Formatting Rules:
- All URLs from input data must be included in the response.
- Maintain all sections and structure from the input data.
- Use XML tags that match the original categories.
- Preserve all text exactly as given—no changes in wording, punctuation, or formatting.  
- Ensure proper XML nesting and structure.
- Escape any special characters that require XML encoding.  
- Do NOT introduce new data or rephrase content.  
- Capture all the data points in the original format, including the reasoning, the thoughts and ideas of the agent, besides the company data points.
- The <status> field of the data point must be OK, NEEDS_REVIEW, NO_DATA or SINGLE_SOURCE.
- IMPORTANT: Make sure you follow the exact names of the section tags: CompanyData, CompanyIdentity, RegistrationDetails, Headquarters, LocationsAndOperations, Industry, OwnershipDetails. Do not change the names of the section tags as these will be parsed!
- IMPORTANT: Follow the output format exactly as shown in the sample output. Do not change the order of the sections or the names of the tags!
---
Here's a sample output. Use this as a template to generate the XML output:

```xml
<CompanyData>
    <CompanyIdentity>
        <Name>
            <FinalApprovedName>[Insert final validated company name here]</FinalApprovedName>
            <LegalNameVariations>[Insert any alternative names or trading names here]</LegalNameVariations>
            <ExactRawData>[Insert exact company name as found in source documents]</ExactRawData>
            <Sources>
                <Source>[Insert name of source 1]</Source>
                <URL>[Insert URL of source 1]</URL>
                <Source>[Insert name of source 2]</Source>
                <URL>[Insert URL of source 2]</URL>
            </Sources>
            <SourceNotes>[Add specific notes about each source's reliability, recency, and authority for name information]</SourceNotes>
            <ChainOfThoughtReasoning>[Explain reasoning for selecting final company name, especially if sources conflict]</ChainOfThoughtReasoning>
            <Status>[Insert data validation status: OK, NEEDS_REVIEW, CONFLICTING_DATA, etc.]</Status>
            <AnyRemainingIssues>[Describe any unresolved issues with company name data]</AnyRemainingIssues>
            <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
            <Notes>[Add notes about name verification process, source reliability, or other relevant observations]</Notes>
            <NameVariationNotes>[Document any patterns observed in name variations, potential reasons for discrepancies, and impact on identification]</NameVariationNotes>
        </Name>
        <RegistrationDetails>
            <FinalRegistrationNumber>[Insert verified registration number]</FinalRegistrationNumber>
            <FinalRegistrationDate>[Insert verified registration date]</FinalRegistrationDate>
            <ExactRawData>[Insert exact registration details as found in source documents]</ExactRawData>
            <Sources>
                <Source>[Insert name of source 1]</Source>
                <URL>[Insert URL of source 1]</URL>
                <Source>[Insert name of source 2]</Source>
                <URL>[Insert URL of source 2]</URL>
            </Sources>
            <SourceNotes>[Note which source was considered most authoritative for registration data and why]</SourceNotes>
            <ChainOfThoughtReasoning>[Explain how registration details were verified and how conflicting data was resolved]</ChainOfThoughtReasoning>
            <Status>[Insert data validation status]</Status>
            <AnyRemainingIssues>[Describe any unresolved issues with registration data]</AnyRemainingIssues>
            <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
            <Notes>[Add notes about verification challenges, data discrepancies, or importance of specific sources]</Notes>
            <RegistrationNumberNotes>[Document any format changes, prefixes, or alternate registration numbers found across sources]</RegistrationNumberNotes>
            <RegistrationDateNotes>[Note any discrepancies in registration dates and potential explanations, such as re-registration or corporate restructuring]</RegistrationDateNotes>
        </RegistrationDetails>
        <CompanyStatus>[Insert current company status: Active, Inactive, In Liquidation, etc.]</CompanyStatus>
        <CompanyStatusNotes>[Document how status was verified and if there are any recent status changes or pending regulatory actions]</CompanyStatusNotes>
        <BusinessEntityType>[Insert business entity type: LLC, Public Limited Company, Partnership, etc.]</BusinessEntityType>
        <BusinessEntityTypeNotes>[Note any changes in business entity type over time and potential implications]</BusinessEntityTypeNotes>
        <SectionStatus>[Insert overall status of company identity section]</SectionStatus>
        <Notes>[Add overall notes about company identity verification, highlighting key issues or confidence level]</Notes>
        <IdentityVerificationProcess>[Document the overall process used to verify company identity, including challenges and successful approaches]</IdentityVerificationProcess>
    </CompanyIdentity>

    <ContactInformation>
        <Email>[Insert company email address]</Email>
        <EmailNotes>[Note whether email was tested/verified and any response patterns or automated replies]</EmailNotes>
        <Phone>[Insert company phone number]</Phone>
        <PhoneNotes>[Document any attempts to verify the phone number, noting if calls were answered and by whom]</PhoneNotes>
        <Website>[Insert company website URL]</Website>
        <WebsiteNotes>[Note website functionality, security issues, last update date, and general quality]</WebsiteNotes>
        <SocialMediaProfiles>
            <Platform>[Insert social media platform name]</Platform>
            <URL>[Insert social media profile URL]</URL>
            <ProfileNotes>[Note account activity level, follower count, verification status, and content quality]</ProfileNotes>
        </SocialMediaProfiles>
        <Sources>
            <Source>[Insert name of source]</Source>
            <URL>[Insert URL of source]</URL>
        </Sources>
        <SourceNotes>[Note reliability of each contact information source and any cross-verification performed]</SourceNotes>
        <ChainOfThoughtReasoning>[Explain how contact information was verified]</ChainOfThoughtReasoning>
        <Status>[Insert data validation status]</Status>
        <AnyRemainingIssues>[Describe any unresolved issues with contact information]</AnyRemainingIssues>
        <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
        <SectionStatus>[Insert overall status of contact information section]</SectionStatus>
        <Notes>[Add notes about verification of contact details, functioning of contact methods, etc.]</Notes>
        <ContactConsistencyNotes>[Document consistency of contact information across different platforms and sources]</ContactConsistencyNotes>
    </ContactInformation>

    <Headquarters>
        <Address>[Insert headquarters address]</Address>
        <ExactRawData>[Insert exact address as found in source documents]</ExactRawData>
        <AddressComponentNotes>[Document any inconsistencies in address components like postal code, state/province, or building number]</AddressComponentNotes>
        <Sources>
            <Source>[Insert name of source 1]</Source>
            <URL>[Insert URL of source 1]</URL>
            <Source>[Insert name of source 2]</Source>
            <URL>[Insert URL of source 2]</URL>
        </Sources>
        <SourceNotes>[Note the relative reliability of each source for address information]</SourceNotes>
        <ChainOfThoughtReasoning>[Explain how headquarters address was verified]</ChainOfThoughtReasoning>
        <Status>[Insert data validation status]</Status>
        <AnyRemainingIssues>[Describe any unresolved issues with headquarters data]</AnyRemainingIssues>
        <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
        <SectionStatus>[Insert overall status of headquarters section]</SectionStatus>
        <Notes>[Add notes about address verification, physical confirmation, or inconsistencies across sources]</Notes>
        <GeographicVerificationNotes>[Document any attempts to verify the address through maps, satellite imagery, or street view tools]</GeographicVerificationNotes>
        <HeadquartersHistoryNotes>[Note any recent changes in headquarters location and potential business implications]</HeadquartersHistoryNotes>
    </Headquarters>

    <LocationsAndOperations>
        <AdditionalLocations>[Insert additional office locations]</AdditionalLocations>
        <AdditionalLocationsNotes>[Document the significance of each location, operational status, and verification confidence]</AdditionalLocationsNotes>
        <FactoryLocations>[Insert factory or production site locations]</FactoryLocations>
        <FactoryLocationsNotes>[Note production capacity, operational status, and strategic importance of each factory location]</FactoryLocationsNotes>
        <ExactRawData>[Insert exact location data as found in source documents]</ExactRawData>
        <Sources>
            <Source>[Insert name of source]</Source>
            <URL>[Insert URL of source]</URL>
        </Sources>
        <SourceNotes>[Document the comprehensiveness and reliability of each source for location information]</SourceNotes>
        <ChainOfThoughtReasoning>[Explain how additional locations were verified]</ChainOfThoughtReasoning>
        <Status>[Insert data validation status]</Status>
        <AnyRemainingIssues>[Describe any unresolved issues with location data]</AnyRemainingIssues>
        <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
        <SectionStatus>[Insert overall status of locations section]</SectionStatus>
        <Notes>[Add notes about location verification challenges, operational importance of locations, etc.]</Notes>
        <LocationVerificationMethodNotes>[Document methods used to verify each location and their relative effectiveness]</LocationVerificationMethodNotes>
        <GeographicDistributionNotes>[Note any patterns in geographic distribution of company operations and business implications]</GeographicDistributionNotes>
    </LocationsAndOperations>

    <Industry>
        <FinalIndustryClassification>[Insert industry classification]</FinalIndustryClassification>
        <IndustryClassificationNotes>[Document how industry classification was determined and any classification systems used (NAICS, SIC, etc.)]</IndustryClassificationNotes>
        <MainProductsOrServices>[Insert main products or services]</MainProductsOrServices>
        <ProductsServicesNotes>[Note the company's primary offerings, market positioning, and any recent changes in product lines]</ProductsServicesNotes>
        <Certifications>
            <Certification>[Insert certification name]</Certification>
            <CertificationSource>[Insert source of certification information]</CertificationSource>
            <CertificationDate>[Insert certification date]</CertificationDate>
            <CertificationNotes>[Document the importance of this certification in the industry, verification status, and expiration date if applicable]</CertificationNotes>
        </Certifications>
        <CertificationsOverviewNotes>[Provide analysis of the company's overall certification portfolio and compliance status]</CertificationsOverviewNotes>
        <ExactRawData>[Insert exact industry data as found in source documents]</ExactRawData>
        <Sources>
            <Source>[Insert name of source]</Source>
            <URL>[Insert URL of source]</URL>
        </Sources>
        <SourceNotes>[Note the reliability and comprehensiveness of each source for industry information]</SourceNotes>
        <ChainOfThoughtReasoning>[Explain how industry classification was determined]</ChainOfThoughtReasoning>
        <Status>[Insert data validation status]</Status>
        <AnyRemainingIssues>[Describe any unresolved issues with industry data]</AnyRemainingIssues>
        <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
        <SectionStatus>[Insert overall status of industry section]</SectionStatus>
        <Notes>[Add notes about industry verification, discrepancies in product descriptions, or certification validity]</Notes>
        <IndustryTrendsNotes>[Document relevant industry trends, challenges, and growth prospects that may affect the company]</IndustryTrendsNotes>
        <CompetitivePositionNotes>[Note the company's relative position in its industry and main competitors if information is available]</CompetitivePositionNotes>
    </Industry>

    <OwnershipDetails>
        <ParentCompany>[Insert parent company name]</ParentCompany>
        <ParentCompanyNotes>[Document the relationship with parent company, including control mechanisms and organizational independence]</ParentCompanyNotes>
        <Owner>[Insert major owner or shareholders]</Owner>
        <OwnershipStructureNotes>[Note ownership percentages, changes in ownership over time, and any complex holding structures]</OwnershipStructureNotes>
        <KeyDirectors>[Insert names of key executives and directors]</KeyDirectors>
        <KeyDirectorsNotes>[Document tenure of key executives, background verification, and any red flags identified]</KeyDirectorsNotes>
        <ExactRawData>[Insert exact ownership data as found in source documents]</ExactRawData>
        <Sources>
            <Source>[Insert name of source]</Source>
            <URL>[Insert URL of source]</URL>
        </Sources>
        <SourceNotes>[Note the reliability and comprehensiveness of each source for ownership information]</SourceNotes>
        <ChainOfThoughtReasoning>[Explain how ownership details were verified]</ChainOfThoughtReasoning>
        <Status>[Insert data validation status]</Status>
        <AnyRemainingIssues>[Describe any unresolved issues with ownership data]</AnyRemainingIssues>
        <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
        <SectionStatus>[Insert overall status of ownership section]</SectionStatus>
        <Notes>[Add notes about ownership structure complexity, verification challenges, or need for deeper investigation]</Notes>
        <BeneficialOwnershipNotes>[Document efforts to identify ultimate beneficial owners and any challenges encountered]</BeneficialOwnershipNotes>
        <CorporateGovernanceNotes>[Note governance structure, board composition, and any governance concerns identified]</CorporateGovernanceNotes>
    </OwnershipDetails>
    
    <FinancialInformation>
        <Revenue>[Insert revenue amount and currency]</Revenue>
        <RevenueNotes>[Document revenue trends, verification sources, and any discrepancies between reported figures]</RevenueNotes>
        <ProfitBeforeTax>[Insert profit before tax amount and currency]</ProfitBeforeTax>
        <ProfitNotes>[Note profit trends, unusual fluctuations, and comparison to industry averages if available]</ProfitNotes>
        <MarketValue>[Insert market value amount and currency]</MarketValue>
        <MarketValueNotes>[Document market value changes, valuation method, and any recent significant fluctuations]</MarketValueNotes>
        <StockInformation>[Insert stock exchange listing and current price information]</StockInformation>
        <StockPerformanceNotes>[Note recent stock performance, trading volume, and any unusual market activities]</StockPerformanceNotes>
        <ExactRawData>[Insert exact financial data as found in source documents]</ExactRawData>
        <Sources>
            <Source>[Insert name of source]</Source>
            <URL>[Insert URL of source]</URL>
        </Sources>
        <SourceNotes>[Document the reliability, timeliness, and comprehensiveness of each financial data source]</SourceNotes>
        <ChainOfThoughtReasoning>[Explain how financial information was verified]</ChainOfThoughtReasoning>
        <Status>[Insert data validation status]</Status>
        <AnyRemainingIssues>[Describe any unresolved issues with financial data]</AnyRemainingIssues>
        <ProposedNextSteps>[Suggest actions to resolve any remaining issues]</ProposedNextSteps>
        <SectionStatus>[Insert overall status of financial information section]</SectionStatus>
        <Notes>[Add notes about financial data reliability, discrepancies between sources, or time-sensitivity of data]</Notes>
        <FinancialHealthNotes>[Provide overall assessment of company's financial health based on available data]</FinancialHealthNotes>
        <FinancialReportingNotes>[Document the quality, transparency, and timeliness of the company's financial reporting]</FinancialReportingNotes>
    </FinancialInformation>
       
    
    <DataAssessmentSummary>
        <OverallDataQuality>[Describe overall quality of collected data]</OverallDataQuality>
        <DataQualityNotes>[Document factors affecting data quality including reliability, completeness, and timeliness]</DataQualityNotes>
        <MajorGaps>[List any significant information gaps]</MajorGaps>
        <DataGapsNotes>[Note impact of information gaps on overall assessment and decision-making]</DataGapsNotes>
        <RecommendedNextSteps>[Provide overall recommendations for further research or verification]</RecommendedNextSteps>
        <NextStepsNotes>[Document priority order for recommended actions, expected time required, and potential outcomes]</NextStepsNotes>
        <Notes>[Add summary notes about the entire data collection process, highlighting strengths and weaknesses]</Notes>
        <ResearchProcessNotes>[Document research methodology, tools used, and lessons learned for future assessments]</ResearchProcessNotes>
        <ConfidenceLevelNotes>[Provide assessment of overall confidence in the data and key factors affecting reliability]</ConfidenceLevelNotes>
        <FinalRecommendationNotes>[Document clear business recommendation based on data assessment and risk profile]</FinalRecommendationNotes>
    </DataAssessmentSummary>
</CompanyData>
```



Company data is:
{company_data}
"""
