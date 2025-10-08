import os
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from service.lksg_core.persistence_service import persistence_service


def parse_company_data_xml(xml_string: str) -> Dict[str, Any]:
    """
    Parse the XML string into a nested dictionary structure.
    """
    root = ET.fromstring(xml_string)

    def get_text(element, tag):
        """Get text from an XML tag, return an empty string if not found."""
        if element is None:
            return ""  # Avoids calling .find() on NoneType
        child = element.find(tag)
        return child.text.strip() if child is not None and child.text else ""

    def parse_sources_element(element) -> List[Dict[str, str]]:
        """Extract source and URL pairs from Sources element."""
        sources: List[Dict[str, str]] = []
        if element is None:
            return sources

        sources_el = element.find("Sources")
        if sources_el is None:
            return sources

        # Find all source-URL pairs
        source_elements = sources_el.findall("Source")
        url_elements = sources_el.findall("URL")

        # Match sources with URLs if they have the same number
        if len(source_elements) == len(url_elements):
            for src, url in zip(source_elements, url_elements):
                src_text = src.text.strip() if src.text else ""
                url_text = url.text.strip() if url.text else ""
                if src_text:
                    sources.append({"Source": src_text, "URL": url_text})
        else:
            # If mismatched, try to extract what we can
            for src in source_elements:
                if src.text and src.text.strip():
                    sources.append({"Source": src.text.strip(), "URL": ""})
            for url in url_elements:
                if url.text and url.text.strip():
                    sources.append(
                        {"Source": "Unknown Source", "URL": url.text.strip()}
                    )

        return sources

    def get_directors(element):
        """Extract directors from KeyDirectors element."""
        if element is None:
            return []

        key_directors_el = element.find("KeyDirectors")
        if key_directors_el is None:
            # If KeyDirectors exists as a simple text element
            directors_text = get_text(element, "KeyDirectors")
            return [directors_text] if directors_text else []

        # Handle complex KeyDirectors with Director elements
        directors = []
        for director_el in key_directors_el.findall("Director"):
            if director_el is not None and director_el.text:
                directors.append(director_el.text.strip())

        # If no Director elements found but KeyDirectors has text
        if not directors and key_directors_el.text and key_directors_el.text.strip():
            directors.append(key_directors_el.text.strip())

        return directors

    def parse_sources(element):
        """Parses the Sources element and extracts sources and URLs."""
        if element is None:
            return {"Text": "", "Links": []}

        sources_el = element.find("Sources")
        if sources_el is None:
            # Fall back to old format if Sources not found
            return parse_exact_raw_data(element.find("ExactRawData"))

        text = element.find("ExactRawData")
        text = text.text.strip() if text is not None and text.text else ""

        links = []
        for url in sources_el.findall("URL"):
            url_text = url.text.strip() if url.text else ""
            if url_text and not url_text.startswith(("http://", "https://")):
                url_text = "https://" + url_text
            if url_text and url_text != "No URL":
                links.append(url_text)

        # Extract URLs from the text using regex
        urls_from_text = re.findall(r"(https?://\S+)", text)
        links.extend(urls_from_text)

        # Remove duplicate links while preserving order
        unique_links = []
        seen = set()
        for link in links:
            if link not in seen:
                unique_links.append(link)
                seen.add(link)

        return {"Text": text, "Links": unique_links}

    def parse_exact_raw_data(element):
        """Parses the ExactRawData element and extracts text and links."""
        if element is None:
            return {"Text": "", "Links": []}

        text = "".join(element.itertext()).strip() if element.text else ""
        links = []
        for link in element.findall("Link"):
            link_text = link.text.strip() if link.text else ""
            if link_text and not link_text.startswith(("http://", "https://")):
                link_text = "https://" + link_text
            links.append(link_text)
        for url in element.findall("URL"):
            url_text = url.text.strip() if url.text else ""
            if url_text and not url_text.startswith(("http://", "https://")):
                url_text = "https://" + url_text
            links.append(url_text)

        # Extract URLs from the text using regex
        urls_from_text = re.findall(r"(https?://\S+)", text)
        links.extend(urls_from_text)

        # Remove duplicate links while preserving order
        unique_links = []
        seen = set()
        for link in links:
            if link not in seen:
                unique_links.append(link)
                seen.add(link)

        return {"Text": text, "Links": unique_links}

    def parse_social_media_profiles(element) -> List[Dict[str, str]]:
        """Parse social media profiles from ContactInformation."""
        profiles: List[Dict[str, str]] = []
        if element is None:
            return profiles

        social_media_el = element.find("SocialMediaProfiles")
        if social_media_el is None:
            return profiles

        # Handle multiple platforms
        platform_elements = social_media_el.findall("Platform")
        url_elements = social_media_el.findall("URL")
        profile_notes_elements = social_media_el.findall("ProfileNotes")

        # If we have matching elements
        if len(platform_elements) == len(url_elements):
            for i, (platform, url) in enumerate(zip(platform_elements, url_elements)):
                profile = {
                    "Platform": platform.text.strip() if platform.text else "",
                    "URL": url.text.strip() if url.text else "",
                }

                # Add notes if available
                if i < len(profile_notes_elements) and profile_notes_elements[i].text:
                    profile["ProfileNotes"] = profile_notes_elements[i].text.strip()

                profiles.append(profile)
        else:
            # Single platform/URL pair
            platform = get_text(social_media_el, "Platform")
            url = get_text(social_media_el, "URL")
            notes = get_text(social_media_el, "ProfileNotes")

            if platform or url:
                profiles.append(
                    {"Platform": platform, "URL": url, "ProfileNotes": notes}
                )

        return profiles

    def parse_certifications(element) -> List[Dict[str, str]]:
        """Parse certifications from Industry element."""
        certifications: List[Dict[str, str]] = []
        if element is None:
            return certifications

        certs_el = element.find("Certifications")
        if certs_el is None:
            return certifications

        # Handle multiple certifications
        cert_elements = certs_el.findall("Certification")
        source_elements = certs_el.findall("CertificationSource")
        date_elements = certs_el.findall("CertificationDate")
        notes_elements = certs_el.findall("CertificationNotes")

        # If we have certification elements
        if cert_elements:
            for i, cert in enumerate(cert_elements):
                certification = {
                    "Certification": cert.text.strip() if cert.text else ""
                }

                # Add source if available
                if i < len(source_elements) and source_elements[i].text:
                    certification["Source"] = source_elements[i].text.strip()

                # Add date if available
                if i < len(date_elements) and date_elements[i].text:
                    certification["Date"] = date_elements[i].text.strip()

                # Add notes if available
                if i < len(notes_elements) and notes_elements[i].text:
                    certification["Notes"] = notes_elements[i].text.strip()

                certifications.append(certification)
        else:
            # Single certification
            cert = get_text(certs_el, "Certification")
            source = get_text(certs_el, "CertificationSource")
            date = get_text(certs_el, "CertificationDate")
            notes = get_text(certs_el, "CertificationNotes")

            if cert:
                certifications.append(
                    {
                        "Certification": cert,
                        "Source": source,
                        "Date": date,
                        "Notes": notes,
                    }
                )

        return certifications

    # Parse CompanyIdentity section
    company_identity_el = root.find("CompanyData/CompanyIdentity")
    if company_identity_el is None:
        company_identity_el = root.find("CompanyIdentity")  # Fallback to old structure

    name_el = (
        company_identity_el.find("Name") if company_identity_el is not None else None
    )
    registration_el = (
        company_identity_el.find("RegistrationDetails")
        if company_identity_el is not None
        else None
    )

    company_identity_data = {
        "Name": {
            "FinalApprovedName": get_text(name_el, "FinalApprovedName"),
            "LegalNameVariations": get_text(name_el, "LegalNameVariations"),
            "ExactRawData": parse_sources(name_el),
            "Sources": parse_sources_element(name_el),
            "SourceNotes": get_text(name_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(name_el, "ChainOfThoughtReasoning"),
            "AnyRemainingIssues": get_text(name_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(name_el, "ProposedNextSteps"),
            "Status": get_text(name_el, "Status"),
            "Notes": get_text(name_el, "Notes"),
            "NameVariationNotes": get_text(name_el, "NameVariationNotes"),
        },
        "RegistrationDetails": {
            "FinalRegistrationNumber": get_text(
                registration_el, "FinalRegistrationNumber"
            ),
            "FinalRegistrationDate": get_text(registration_el, "FinalRegistrationDate"),
            "ExactRawData": parse_sources(registration_el),
            "Sources": parse_sources_element(registration_el),
            "SourceNotes": get_text(registration_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(
                registration_el, "ChainOfThoughtReasoning"
            ),
            "AnyRemainingIssues": get_text(registration_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(registration_el, "ProposedNextSteps"),
            "Status": get_text(registration_el, "Status"),
            "Notes": get_text(registration_el, "Notes"),
            "RegistrationNumberNotes": get_text(
                registration_el, "RegistrationNumberNotes"
            ),
            "RegistrationDateNotes": get_text(registration_el, "RegistrationDateNotes"),
        },
        "CompanyStatus": get_text(company_identity_el, "CompanyStatus"),
        "CompanyStatusNotes": get_text(company_identity_el, "CompanyStatusNotes"),
        "BusinessEntityType": get_text(company_identity_el, "BusinessEntityType"),
        "BusinessEntityTypeNotes": get_text(
            company_identity_el, "BusinessEntityTypeNotes"
        ),
        "SectionStatus": get_text(company_identity_el, "SectionStatus"),
        "Notes": get_text(company_identity_el, "Notes"),
        "IdentityVerificationProcess": get_text(
            company_identity_el, "IdentityVerificationProcess"
        ),
    }

    # Parse ContactInformation section
    contact_info_el = root.find("CompanyData/ContactInformation")
    if contact_info_el is None:
        contact_info_el = root.find("ContactInformation")  # Fallback

    contact_info_data = None
    if contact_info_el is not None:
        contact_info_data = {
            "Email": get_text(contact_info_el, "Email"),
            "EmailNotes": get_text(contact_info_el, "EmailNotes"),
            "Phone": get_text(contact_info_el, "Phone"),
            "PhoneNotes": get_text(contact_info_el, "PhoneNotes"),
            "Website": get_text(contact_info_el, "Website"),
            "WebsiteNotes": get_text(contact_info_el, "WebsiteNotes"),
            "SocialMediaProfiles": parse_social_media_profiles(contact_info_el),
            "Sources": parse_sources_element(contact_info_el),
            "SourceNotes": get_text(contact_info_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(
                contact_info_el, "ChainOfThoughtReasoning"
            ),
            "Status": get_text(contact_info_el, "Status"),
            "AnyRemainingIssues": get_text(contact_info_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(contact_info_el, "ProposedNextSteps"),
            "SectionStatus": get_text(contact_info_el, "SectionStatus"),
            "Notes": get_text(contact_info_el, "Notes"),
            "ContactConsistencyNotes": get_text(
                contact_info_el, "ContactConsistencyNotes"
            ),
        }

    # Parse Headquarters section
    headquarters_el = root.find("CompanyData/Headquarters")
    if headquarters_el is None:
        headquarters_el = root.find("Headquarters")  # Fallback

    headquarters_data = None
    if headquarters_el is not None:
        headquarters_data = {
            "Address": get_text(headquarters_el, "Address"),
            "ExactRawData": parse_sources(headquarters_el),
            "AddressComponentNotes": get_text(headquarters_el, "AddressComponentNotes"),
            "Sources": parse_sources_element(headquarters_el),
            "SourceNotes": get_text(headquarters_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(
                headquarters_el, "ChainOfThoughtReasoning"
            ),
            "Status": get_text(headquarters_el, "Status"),
            "AnyRemainingIssues": get_text(headquarters_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(headquarters_el, "ProposedNextSteps"),
            "SectionStatus": get_text(headquarters_el, "SectionStatus"),
            "Notes": get_text(headquarters_el, "Notes"),
            "GeographicVerificationNotes": get_text(
                headquarters_el, "GeographicVerificationNotes"
            ),
            "HeadquartersHistoryNotes": get_text(
                headquarters_el, "HeadquartersHistoryNotes"
            ),
        }

    # Parse LocationsAndOperations section
    locations_el = root.find("CompanyData/LocationsAndOperations")
    if locations_el is None:
        locations_el = root.find("LocationsAndOperations")  # Fallback

    locations_data = None
    if locations_el is not None:
        locations_data = {
            "AdditionalLocations": get_text(locations_el, "AdditionalLocations"),
            "AdditionalLocationsNotes": get_text(
                locations_el, "AdditionalLocationsNotes"
            ),
            "FactoryLocations": get_text(locations_el, "FactoryLocations"),
            "FactoryLocationsNotes": get_text(locations_el, "FactoryLocationsNotes"),
            "ExactRawData": parse_sources(locations_el),
            "Sources": parse_sources_element(locations_el),
            "SourceNotes": get_text(locations_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(
                locations_el, "ChainOfThoughtReasoning"
            ),
            "Status": get_text(locations_el, "Status"),
            "AnyRemainingIssues": get_text(locations_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(locations_el, "ProposedNextSteps"),
            "SectionStatus": get_text(locations_el, "SectionStatus"),
            "Notes": get_text(locations_el, "Notes"),
            "LocationVerificationMethodNotes": get_text(
                locations_el, "LocationVerificationMethodNotes"
            ),
            "GeographicDistributionNotes": get_text(
                locations_el, "GeographicDistributionNotes"
            ),
        }

    # Parse Industry section
    industry_el = root.find("CompanyData/Industry")
    if industry_el is None:
        industry_el = root.find("Industry")  # Fallback

    industry_data = {
        "FinalIndustryClassification": get_text(
            industry_el, "FinalIndustryClassification"
        ),
        "IndustryClassificationNotes": get_text(
            industry_el, "IndustryClassificationNotes"
        ),
        "MainProductsOrServices": get_text(industry_el, "MainProductsOrServices"),
        "ProductsServicesNotes": get_text(industry_el, "ProductsServicesNotes"),
        "Certifications": parse_certifications(industry_el),
        "CertificationsOverviewNotes": get_text(
            industry_el, "CertificationsOverviewNotes"
        ),
        "ExactRawData": parse_sources(industry_el),
        "Sources": parse_sources_element(industry_el),
        "SourceNotes": get_text(industry_el, "SourceNotes"),
        "ChainOfThoughtReasoning": get_text(industry_el, "ChainOfThoughtReasoning"),
        "Status": get_text(industry_el, "Status"),
        "AnyRemainingIssues": get_text(industry_el, "AnyRemainingIssues"),
        "ProposedNextSteps": get_text(industry_el, "ProposedNextSteps"),
        "SectionStatus": get_text(industry_el, "SectionStatus"),
        "Notes": get_text(industry_el, "Notes"),
        "IndustryTrendsNotes": get_text(industry_el, "IndustryTrendsNotes"),
        "CompetitivePositionNotes": get_text(industry_el, "CompetitivePositionNotes"),
    }

    # Parse OwnershipDetails section
    ownership_el = root.find("CompanyData/OwnershipDetails")
    if ownership_el is None:
        ownership_el = root.find("OwnershipDetails")  # Fallback

    ownership_data = {
        "ParentCompany": get_text(ownership_el, "ParentCompany"),
        "ParentCompanyNotes": get_text(ownership_el, "ParentCompanyNotes"),
        "Owner": get_text(ownership_el, "Owner"),
        "OwnershipStructureNotes": get_text(ownership_el, "OwnershipStructureNotes"),
        "KeyDirectors": get_text(ownership_el, "KeyDirectors"),
        "KeyDirectorsNotes": get_text(ownership_el, "KeyDirectorsNotes"),
        "ExactRawData": parse_sources(ownership_el),
        "Sources": parse_sources_element(ownership_el),
        "SourceNotes": get_text(ownership_el, "SourceNotes"),
        "ChainOfThoughtReasoning": get_text(ownership_el, "ChainOfThoughtReasoning"),
        "Status": get_text(ownership_el, "Status"),
        "AnyRemainingIssues": get_text(ownership_el, "AnyRemainingIssues"),
        "ProposedNextSteps": get_text(ownership_el, "ProposedNextSteps"),
        "SectionStatus": get_text(ownership_el, "SectionStatus"),
        "Notes": get_text(ownership_el, "Notes"),
        "BeneficialOwnershipNotes": get_text(ownership_el, "BeneficialOwnershipNotes"),
        "CorporateGovernanceNotes": get_text(ownership_el, "CorporateGovernanceNotes"),
    }

    # Parse FinancialInformation section
    financial_el = root.find("CompanyData/FinancialInformation")
    if financial_el is None:
        financial_el = root.find("FinancialInformation")  # Fallback

    financial_data = None
    if financial_el is not None:
        financial_data = {
            "Revenue": get_text(financial_el, "Revenue"),
            "RevenueNotes": get_text(financial_el, "RevenueNotes"),
            "ProfitBeforeTax": get_text(financial_el, "ProfitBeforeTax"),
            "ProfitNotes": get_text(financial_el, "ProfitNotes"),
            "MarketValue": get_text(financial_el, "MarketValue"),
            "MarketValueNotes": get_text(financial_el, "MarketValueNotes"),
            "StockInformation": get_text(financial_el, "StockInformation"),
            "StockPerformanceNotes": get_text(financial_el, "StockPerformanceNotes"),
            "ExactRawData": parse_sources(financial_el),
            "Sources": parse_sources_element(financial_el),
            "SourceNotes": get_text(financial_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(
                financial_el, "ChainOfThoughtReasoning"
            ),
            "Status": get_text(financial_el, "Status"),
            "AnyRemainingIssues": get_text(financial_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(financial_el, "ProposedNextSteps"),
            "SectionStatus": get_text(financial_el, "SectionStatus"),
            "Notes": get_text(financial_el, "Notes"),
            "FinancialHealthNotes": get_text(financial_el, "FinancialHealthNotes"),
            "FinancialReportingNotes": get_text(
                financial_el, "FinancialReportingNotes"
            ),
        }

    # Parse RiskAssessment section
    risk_el = root.find("CompanyData/RiskAssessment")
    if risk_el is None:
        risk_el = root.find("RiskAssessment")  # Fallback

    risk_data = None
    if risk_el is not None:
        risk_data = {
            "ComplianceHistory": get_text(risk_el, "ComplianceHistory"),
            "ComplianceHistoryNotes": get_text(risk_el, "ComplianceHistoryNotes"),
            "LegalProceedings": get_text(risk_el, "LegalProceedings"),
            "LegalProceedingsNotes": get_text(risk_el, "LegalProceedingsNotes"),
            "RegulatoryIssues": get_text(risk_el, "RegulatoryIssues"),
            "RegulatoryIssuesNotes": get_text(risk_el, "RegulatoryIssuesNotes"),
            "Sources": parse_sources_element(risk_el),
            "SourceNotes": get_text(risk_el, "SourceNotes"),
            "ChainOfThoughtReasoning": get_text(risk_el, "ChainOfThoughtReasoning"),
            "Status": get_text(risk_el, "Status"),
            "AnyRemainingIssues": get_text(risk_el, "AnyRemainingIssues"),
            "ProposedNextSteps": get_text(risk_el, "ProposedNextSteps"),
            "SectionStatus": get_text(risk_el, "SectionStatus"),
            "Notes": get_text(risk_el, "Notes"),
            "RiskTrendsNotes": get_text(risk_el, "RiskTrendsNotes"),
            "IndustryComparisonNotes": get_text(risk_el, "IndustryComparisonNotes"),
        }

    # Parse DataAssessmentSummary section
    summary_el = root.find("CompanyData/DataAssessmentSummary")
    if summary_el is None:
        summary_el = root.find("DataAssessmentSummary")  # Fallback

    summary_data = None
    if summary_el is not None:
        summary_data = {
            "OverallDataQuality": get_text(summary_el, "OverallDataQuality"),
            "DataQualityNotes": get_text(summary_el, "DataQualityNotes"),
            "MajorGaps": get_text(summary_el, "MajorGaps"),
            "DataGapsNotes": get_text(summary_el, "DataGapsNotes"),
            "RecommendedNextSteps": get_text(summary_el, "RecommendedNextSteps"),
            "NextStepsNotes": get_text(summary_el, "NextStepsNotes"),
            "Notes": get_text(summary_el, "Notes"),
            "ResearchProcessNotes": get_text(summary_el, "ResearchProcessNotes"),
            "ConfidenceLevelNotes": get_text(summary_el, "ConfidenceLevelNotes"),
            "FinalRecommendationNotes": get_text(
                summary_el, "FinalRecommendationNotes"
            ),
        }

    # Build the complete result dictionary
    result = {
        "CompanyIdentity": company_identity_data,
        "Industry": industry_data,
        "OwnershipDetails": ownership_data,
    }

    if contact_info_data:
        result["ContactInformation"] = contact_info_data
    if headquarters_data:
        result["Headquarters"] = headquarters_data
    if locations_data:
        result["LocationsAndOperations"] = locations_data
    if financial_data:
        result["FinancialInformation"] = financial_data
    if risk_data:
        result["RiskAssessment"] = risk_data
    if summary_data:
        result["DataAssessmentSummary"] = summary_data

    return result


def render_company_data(xml_string: str) -> str:
    """
    Parse XML data and render it using Jinja2 template.
    """
    # 1. Parse the XML into a dictionary
    company_data_dict = parse_company_data_xml(xml_string)

    # 2. Load Jinja2 template from `templates/` folder using an absolute path
    templates_dir = os.path.join(os.path.dirname(__file__), "../templates")
    templates_dir = os.path.abspath(templates_dir)
    # initialized with autoescape to avoid XSS vulnarability
    env = Environment(
        loader=FileSystemLoader(templates_dir), autoescape=select_autoescape()
    )
    template = env.get_template("company_data_template.html")

    # 3. Render template with parsed data
    return template.render(company_data=company_data_dict)


def generate_company_data_artifact(xml_input: str, work_log_id: str) -> str:
    """
    Generates and saves the company data artifact.

    Returns:
        str: The absolute path to the saved file
    """
    # Parse XML to render the HTML
    html_output = render_company_data(xml_input)

    # Try to extract company name from CompanyData/CompanyIdentity/Name/FinalApprovedName first
    root = ET.fromstring(xml_input)
    name_el = root.find("CompanyData/CompanyIdentity/Name/FinalApprovedName")
    if name_el is None:
        # Try fallback path for older XML structure
        name_el = root.find("CompanyIdentity/Name/FinalApprovedName")

    if name_el is not None and name_el.text:
        company_name = name_el.text.strip()
    else:
        # Default name if we can't find it in the XML
        company_name = "unknown_company"  # noqa: F841

    return persistence_service.save_html_report(
        html_output, work_log_id + "_company_data_report"
    )


if __name__ == "__main__":
    pass
