"""
Default company configuration for law monitoring system.

This module provides default configurations that can be used as fallbacks
when no custom configuration is available. It includes the default company
description and team configurations that were previously stored in static files.

These defaults ensure the system remains functional even after redeployment
when dynamic configuration may be lost.
"""

from typing import List

from loguru import logger

from service.models import CompanyConfig, TeamDescription


def get_default_company_description() -> str:
    """
    Get the default company description.

    Returns:
        Default company description string
    """
    return """Our company is one of Europe's largest discount supermarket chains, operating over 10,000 stores across 30+ countries with more than 300,000 employees. As a major retail group, we focus on providing high-quality products at competitive prices through efficient operations and strong private label offerings.

The company operates across multiple business segments including retail stores, e-commerce platforms, supply chain and logistics, real estate development, and digital services. We source products globally through complex supply chains, with a significant emphasis on private label products that represent the majority of our offerings.

As a data-driven organization, we leverage technology for customer engagement through mobile apps, loyalty programs, and digital marketing. The company also maintains significant real estate portfolios for stores and logistics facilities, while continuously expanding into new markets and product categories.

Our business model relies heavily on regulatory compliance across diverse jurisdictions, from food safety and product quality to labor standards, environmental regulations, packaging requirements, and digital privacy laws. The company's operations touch virtually every aspect of retail commerce, making it subject to a wide range of legal and regulatory frameworks across European and international markets."""


def get_default_teams() -> List[TeamDescription]:
    """
    Get the default team configurations.

    Returns:
        List of default TeamDescription objects
    """
    return [
        TeamDescription(
            name="Sustainability – Product & Packaging Team",
            department="Sustainability",
            description="This team focuses on minimizing the environmental impact of our private-label product packaging across all EU markets. Their mission is to ensure that packaging design, material selection, and labeling align with our internal sustainability goals, customer expectations, and applicable regulations. They are involved from concept to final delivery, including supplier collaboration, design iteration, and post-market environmental assessments.",
            daily_processes=[
                "Reviewing and revising packaging designs to reduce plastic usage and improve recyclability or compostability",
                "Evaluating alternative materials (e.g. bioplastics, FSC-certified paper, mono-materials) and advising product teams",
                "Collaborating with suppliers to gather technical data on materials and support LCA (Life Cycle Assessment) studies",
                "Conducting internal audits on packaging used across product lines to ensure sustainability KPIs are met",
                "Drafting technical guidelines and checklists for use by procurement and design teams when selecting packaging",
                "Assessing packaging for compliance with internal 'green packaging' standards",
                "Creating internal reports on packaging reduction and circular economy contributions for corporate ESG reporting",
                "Providing support for marketing and legal teams when preparing claims like 'recyclable', 'biodegradable', or 'plastic-free'",
                "Benchmarking our packaging against competitors or national strategies (e.g. France's plastic bans, Germany's DSD requirements)",
                "Participating in cross-functional meetings with Product Development, Legal, and CSR teams to track packaging changes",
            ],
            relevant_laws_or_topics="Any regulation or legal proposal related to packaging materials, recyclability claims, extended producer responsibility, design for recycling, single-use packaging restrictions, eco-labeling criteria, or material traceability. This includes emerging guidance on how to define 'sustainable packaging', requirements for plastic reduction targets, or obligations for producer reporting and recyclability labeling.",
        ),
        TeamDescription(
            name="Legal – Environmental Compliance – Packaging Subteam",
            department="Legal",
            description="This subteam ensures that all product packaging — especially private label and imported goods — complies with environmental and waste-related regulations in every country where we operate. They serve as the legal checkpoint for all packaging-related claims, materials, labeling, and reporting obligations. Their role is to interpret and operationalize the law, collaborating with product, sustainability, and procurement teams to ensure compliance and mitigate legal risk.",
            daily_processes=[
                "Monitoring legislation, directives, and regulatory guidance related to packaging materials, EPR (Extended Producer Responsibility), and labeling across all EU markets",
                "Mapping national and EU-level requirements to our packaging formats and identifying risks or conflicts",
                "Advising product teams on permissible claims (e.g. 'compostable', 'biodegradable', 'recyclable') and when such claims require evidence or third-party certification",
                "Reviewing packaging materials and specifications provided by suppliers or the Sustainability team for legal consistency",
                "Creating and maintaining a legal checklist for packaging compliance, which product and procurement teams use during onboarding",
                "Responding to internal inquiries about legal obligations in niche areas, such as decorative packaging, seasonal promo bundles, or imported packaging from third countries",
                "Supporting legal risk assessments for packaging across different jurisdictions with a focus on product recalls, non-compliance fines, or bans",
                "Coordinating with local legal teams or external law firms to interpret unclear or changing requirements (e.g., French Triman logo, German VerpackG obligations)",
                "Drafting responses and providing documentation during audits or regulatory inspections by environmental authorities",
                "Participating in internal policy drafting around packaging compliance, including document retention rules, labeling procedures, and risk escalation paths",
            ],
            relevant_laws_or_topics="Any legal framework that sets rules for what packaging can be used, how it must be labeled, how our company must report or register packaging data nationally, or how environmental claims must be substantiated. This includes rules on plastics, labeling symbols, recycled content, take-back obligations, or mandatory registrations in national packaging registers.",
        ),
        TeamDescription(
            name="Retail Operations – Fresh Food Waste Monitoring",
            department="Retail Operations",
            description="This team is responsible for tracking, analyzing, and reducing food waste from our stores, particularly focusing on highly perishable categories like fresh produce, bakery, meat, dairy, and chilled products. Their primary mission is to ensure that we meet internal waste-reduction goals while complying with any national or EU-level expectations for food waste prevention, transparency, or redistribution. They work closely with store managers, logistics teams, and sustainability reporting functions.",
            daily_processes=[
                "Collecting daily waste reports from individual stores through internal reporting systems",
                "Analyzing patterns of spoilage and overstocking, with a focus on category-level trends",
                "Setting internal waste thresholds and identifying stores or regions exceeding expected limits",
                "Coordinating with logistics and forecasting teams to adjust delivery frequencies and volumes for perishable goods",
                "Piloting new operational strategies like dynamic pricing, 'too good to go' bags, or shorter display windows for certain products",
                "Identifying stock nearing its expiration and coordinating redistribution to food banks or donation partners, where available",
                "Maintaining dashboards for store- and region-level KPIs related to waste",
                "Feeding data into our corporate sustainability and ESG reporting framework",
                "Supporting cross-functional initiatives such as packaging innovations that extend shelf life or optimized store layouts that reduce spoilage",
            ],
            relevant_laws_or_topics="Any regulation, voluntary framework, or national obligation relating to food waste reduction, transparency in food loss data, expiration date handling, donation protocols, or mandatory redistribution of unsold food. This may include soft law (EU strategies), fiscal incentives, or reporting mandates introduced by local governments.",
        ),
        TeamDescription(
            name="Procurement – Ethical Sourcing & Supplier Audits",
            department="Procurement",
            description="This team ensures that our company's suppliers, especially those outside the EU, meet strict ethical, labor, and environmental standards. They are the operational arm of our responsible sourcing strategy, managing audits, supplier assessments, and follow-ups on non-compliance. The team plays a critical role in identifying risks in the supply chain and preparing the company for new legal frameworks such as corporate due diligence, human rights mandates, and environmental oversight obligations.",
            daily_processes=[
                "Distributing and collecting supplier self-assessment questionnaires covering labor conditions, wages, environmental practices, and safety",
                "Scheduling independent third-party audits in high-risk geographies or product categories (e.g. textiles, seafood, seasonal agriculture)",
                "Reviewing audit reports and issuing non-compliance notices with corrective action requirements",
                "Monitoring the remediation timeline and verifying closure of audit findings through follow-up documentation or re-inspections",
                "Maintaining a centralized supplier compliance database integrated with procurement systems",
                "Collaborating with the Legal and CSR teams to assess supplier risks based on region, product, or historical behavior",
                "Training internal buyers and category managers on ethical sourcing standards and red flags",
                "Preparing data and evidence for ESG reports and external stakeholder disclosures (e.g. NGOs, watchdog groups)",
                "Responding to incidents (e.g. whistleblower alerts, media claims, or supplier factory incidents) with rapid investigation and escalation",
            ],
            relevant_laws_or_topics="Any law or regulation that requires corporate due diligence in global supply chains, particularly related to human rights, fair labor practices, forced labor prevention, environmental degradation, or conflict minerals. Also includes emerging national legislation that mandates disclosure, auditing, or legal liability for supplier behavior abroad.",
        ),
        TeamDescription(
            name="Quality Assurance – Food Additives Review",
            department="Quality Assurance",
            description="This team is responsible for verifying that all food additives used in our company's private-label products are compliant with applicable food safety legislation and internal policies. They maintain our internal database of authorized additives, assess regulatory limits by category and market, and flag any substances that are restricted or banned. They ensure that all ingredient lists and product labeling reflect the correct legal status and dosage of additives — including allergens, preservatives, flavor enhancers, or colorants. Their work supports legal compliance, consumer trust, and market-specific product eligibility.",
            daily_processes=[
                "Reviewing technical sheets and formulation data submitted by suppliers for each new or reformulated product",
                "Cross-checking ingredients and additives against EU and national positive/negative lists for food categories",
                "Ensuring that additive concentrations fall within allowed maximum limits per country and product type",
                "Tracking changes in food additive regulations across EU member states and updating internal databases accordingly",
                "Reviewing label drafts to confirm additive disclosures, allergen statements, and functional roles (e.g. preservative, antioxidant)",
                "Maintaining a watchlist of controversial additives that may be legally permitted but are discouraged under our internal standards",
                "Collaborating with R&D and Legal teams when novel ingredients are proposed or new regulations are anticipated",
                "Coordinating with packaging and marketing to prevent misleading claims regarding 'free from additives' or 'natural' status",
                "Participating in product recall drills or incident responses involving additive or contaminant issues",
                "Supporting audit preparation by documenting ingredient control measures and legal compliance evidence",
            ],
            relevant_laws_or_topics="Any regulation that sets rules for the use, limits, labeling, and approval of food additives — including allergens, E-numbers, colorants, preservatives, emulsifiers, and sweeteners. Also includes food safety alerts, banned substance lists, and country-specific variations in permitted use.",
        ),
        # Including only the first 5 teams to keep this manageable - you can add more as needed
    ]


def _validate_default_config(config: CompanyConfig) -> None:
    """
    Validate that the default configuration meets system requirements.

    Args:
        config: CompanyConfig to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if not config.teams:
        raise ValueError("Default configuration must include at least one team")

    if not config.company_description:
        raise ValueError("Default configuration must include company description")

    # Check for duplicate team names
    team_names = [team.name for team in config.teams]
    if len(team_names) != len(set(team_names)):
        raise ValueError("Default configuration contains duplicate team names")

    # Validate each team has required fields
    for team in config.teams:
        if not team.name or not team.department or not team.description:
            raise ValueError(f"Team '{team.name}' missing required fields")
        if not team.daily_processes:
            raise ValueError(f"Team '{team.name}' must have at least one daily process")


def get_default_company_config() -> CompanyConfig:
    """
    Get the complete default company configuration with validation.

    Returns:
        CompanyConfig object with validated default company description and teams

    Raises:
        ValueError: If default configuration is invalid
    """
    try:
        config = CompanyConfig(
            company_description=get_default_company_description(),
            teams=get_default_teams(),
        )
        _validate_default_config(config)
        logger.debug(f"Validated default configuration with {len(config.teams)} teams")
        return config
    except Exception as e:
        logger.error(f"Default configuration validation failed: {e}")
        raise ValueError(f"Invalid default configuration: {e}") from e
