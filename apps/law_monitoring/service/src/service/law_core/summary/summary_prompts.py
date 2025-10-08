EXTRACT_SUBJECT_MATTER_PROMPT = """
You are a senior legal expert specializing in EU legislation compliance for businesses.
Focus on translating legal language into clear business implications.

Focus specifically on the scope, subject matter and key stakeholder roles without including timeline information.
Extract and summarize what this legal act covers and why it matters for businesses.

Your output must strictly follow the structure below. Use 10 signs of equality `==========` to mark the beginning and end of your output.
Do not output anything else!

==========
=Key Stakeholder Roles=
...list 4-6 main roles with compliance obligations - focus on business roles like retailers, manufacturers, importers, distributors, platforms, service providers...
=Revenue-Based Penalties=
YES or NO — this must indicate clearly whether any penalties are expressed as a percentage of revenue, turnover, or profit. Only one of these two values is allowed: YES or NO.
=Scope & Subject Matter Summary=
...2-3 sentences explaining the core subject matter in business terms - what activities, products, services, or processes are regulated...
==========

Example output:
==========
=Key Stakeholder Roles=
Retailers, manufacturers, importers, distributors, platforms, service providers
=Revenue-Based Penalties=
NO
=Scope & Subject Matter=
This legal act covers the budget and staffing regulations of the European Union Agency for the Space Programme (EUSPA), specifically focusing on the estimation of contract staff and seconded national experts.
The subject matter regulates the personnel and financial aspects of the agency, including the establishment plan and budget allocation.
It impacts retail businesses indirectly, as it relates to the overall EU budget and resource allocation, which can have broader implications for businesses operating within the EU regulatory environment.
==========

Here is the legal act, examine it carefully and extract the subject matter and scope information:
{law_text}
"""

EXTRACT_TIMELINE_PROMPT = """
You are a senior legal expert specializing in EU legislation compliance for businesses.
Focus on extracting all relevant dates, deadlines, and compliance timelines from the legal act.

Extract timeline and compliance information that helps business operations plan for compliance requirements.

Your output must strictly follow the structure below. Use 10 signs of equality `==========` to mark the beginning and end of your output.
Do not output anything else!

==========
=Timeline for Compliance=
...key dates and deadlines that business operations must meet - prioritize actionable deadlines...
=Entry Into Force=
...when the legal act becomes legally effective...
=Application Deadlines=
...specific dates by which compliance must be achieved...
=Transitional Periods=
...any grace periods or phased implementation schedules...
=Reporting Deadlines=
...any recurring reporting or notification requirements...
=Review Dates=
...dates when the law will be reviewed or updated...
==========

Example output:
==========
=Timeline for Compliance=
- 6 weeks from the date of listing in Annex IV: report funds or economic resources within the jurisdiction of a Member State belonging to, owned, held or controlled by listed natural and legal persons, entities, and bodies.
=Entry Into Force=
- 27.5.2024: Council Decision (CFSP) 2024/1484 and Council Regulation (EU) 2024/1485 entered into force.
- 27.5.2025: Council Decision (CFSP) 2025/1070 and Council Implementing Regulation (EU) 2025/1081 entered into force.
=Application Deadlines=
- 6 weeks from the date of listing: compliance with reporting obligations under Article 13(2) of Regulation (EU) 2024/1485.
=Transitional Periods=
- No explicit transitional periods mentioned.
=Reporting Deadlines=
- Within 6 weeks from the date of listing in Annex IV: recurring reporting requirement for listed natural and legal persons, entities, and bodies.
=Review Dates=
- No specific review dates mentioned.
==========

Here is the legal act, examine it carefully and extract the timeline information:
{law_text}
"""


EXTRACT_DEFINITIONS_PROMPT = """
You are a legal expert AI specializing in EU legislation compliance for businesses.
Extract and summarize the definitions section from the EU legal act (typically article 3 or after subject matter/scope).
Focus on key terms that are used throughout the text and their precise legal meanings.

Your output must strictly follow the structure below. Use 10 signs of equality `==========` to mark the beginning and end of your output.
Do not output anything else!

==========
=Definitions=
...list of definitions as text...
==========


Here is the legal act, examine it carefully and extract the definitions:
{law_text}
"""


EXTRACT_ROLES_RESPONSIBILITIES_PENALTIES_PROMPT = """
You are a legal expert AI specializing in EU legislation compliance for businesses.
Extract and create a comprehensive compliance table that links roles, responsibilities, and penalties from the EU legal act.

This creates a unified view of WHO must do WHAT and WHAT PENALTIES they face for non-compliance.

Your output must strictly follow the structure below. Use 10 signs of equality `==========` to mark the beginning and end of your output.
Do not output anything else!


==========
=GENERAL PENALTIES NOT ROLE-SPECIFIC=
List all penalties that apply broadly across roles or are not tied to specific roles. Include:
- General fines and their amounts or calculation methods
- Administrative penalties that apply to any violator
- Cross-cutting enforcement measures
- Default penalties for non-compliance
- Penalties for systemic violations
If no general penalties exist, write "No general penalties identified"

=Revenue-Based Penalties=
YES or NO — this must indicate clearly whether any penalties are expressed as a percentage of revenue, turnover, or profit. Only one of these two values is allowed: YES or NO.

=Penalty Severity Assessment=
...2-3 sentences explaining the severity of the penalties...

=COMPLIANCE MATRIX=
Instructions:
- Each distinct role and all its associated information (responsibilities, penalties) should be on a single line.
- Consolidate all responsibilities for the *same role* onto that role's single line, separating individual responsibilities with <br>. Do not list the same role multiple times.
- Use | as separator between Role, Responsibilities, and Penalties columns (3 columns total).
- Use <br> to separate multiple items (e.g., multiple responsibilities or multiple penalty types) within the same cell of a row.
- Link penalties directly to the roles that can incur them.
- If no specific penalties apply to a role, write "No specific penalties identified" in the penalties column for that role.
- Keep role names business-friendly (avoid pure legal jargon).
- Responsibilities should be actionable (what they must DO).
- Include specific penalty amounts, percentages, or consequences where stated.
- MANDATORY: The "GENERAL PENALTIES NOT ROLE-SPECIFIC" section must contain specific penalty information from the law, not be left empty.
- Pay special attention to penalties that are subject to local law, require future definition, have complex implementation requirements, include specific monetary amounts or timeframes, or are expressed as percentage of revenue/turnover/profit.
- CRITICAL: Do NOT include any markdown table headers (e.g., "Role | Responsibilities | Penalties") or separator lines (e.g., "---|---|---") in your output for this section. The first line immediately following the "=COMPLIANCE MATRIX=" marker must be the first role's data, formatted as Role|Responsibilities|Penalties.

Role 1|Responsibility 1.1<br>Responsibility 1.2<br>Responsibility 1.3|Administrative fines: [amount/percentage]<br>Criminal penalties: [description]<br>Remedial measures: [description]
Role 2|Responsibility 2.1<br>Responsibility 2.2|Administrative fines: [amount/percentage]<br>Operational consequences: [description]
Role 3|Responsibility 3.1<br>Responsibility 3.2|No specific penalties identified

==========


Example output (don't copy this output, it's just here as formatting illustration. Make sure to create your own output based on the law text provided with precision):
==========
=GENERAL PENALTIES NOT ROLE-SPECIFIC=
Administrative fines of up to EUR 1 million or 1% of annual turnover for non-compliance with entry 78 of Annex XVII to Regulation (EC) No 1907/2006

=Revenue-Based Penalties=
YES

=Penalty Severity Assessment=
HIGH RISK: Non-compliance with the restriction on placing synthetic polymer microparticles on the market, resulting in administrative fines of up to EUR 1 million or 1% of annual turnover
MEDIUM RISK: Failure to provide instructions for use and disposal, resulting in administrative fines of up to EUR 500,000 or 0.5% of revenue.
LOW RISK: Minor non-compliance with reporting requirements, resulting in administrative fines of up to EUR 100,000 .

=COMPLIANCE MATRIX=
Company formed in accordance with the law of a Member State|Conduct risk-based human rights and environmental due diligence<br>Integrate due diligence into policies and risk management systems<br>Identify and assess actual and potential adverse impacts<br>Prevent and mitigate potential adverse impacts<br>Bring actual adverse impacts to an end<br>and provide remediation|Pecuniary penalties of up to 5% of net worldwide turnover<br>Public statement indicating the company responsible and the nature of the infringement
Parent company|Fulfil due diligence obligations on behalf of subsidiaries<br>Ensure subsidiaries comply with due diligence obligations|Joint and several liability with subsidiaries for failure to comply with due diligence obligations
Subsidiary|Comply with due diligence obligations<br>Provide information to parent company|Joint and several liability with parent company for failure to comply with due diligence obligations
Business partner|Comply with contractual assurances<br>Provide information to company|No specific penalties identified
Regulated financial undertaking|Conduct due diligence on upstream business partners<br>Provide information to company|No specific penalties identified
Third-country company|Designate an authorised representative<br>Provide information to supervisory authority|Pecuniary penalties of up to 5% of net worldwide turnover<br>Public statement indicating the company responsible and the nature of the infringement
Authorised representative|Receive communications from supervisory authorities<br>Cooperate with supervisory authorities|No specific penalties identified
Supervisory authority|Supervise compliance with due diligence obligations<br>Impose penalties|No specific penalties identified
==========

Here is the legal act, examine it carefully and extract the roles, responsibilities, and penalties. Create your output based on the law text provided with precision. Do not make up any information, only use the information provided in the law text:
{law_text}
"""
