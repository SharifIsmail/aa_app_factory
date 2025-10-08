from evaluation.golden_dataset_creation.branch_comparison import (
    create_branch_comparison_examples,
)
from evaluation.golden_dataset_creation.business_partner_distribution import (
    create_business_partner_distribution_examples,
)
from evaluation.golden_dataset_creation.business_partner_numbers import (
    create_business_partner_numbers_examples,
)
from evaluation.golden_dataset_creation.business_partner_priority_information import (
    create_business_partner_priority_examples,
)
from evaluation.golden_dataset_creation.business_partner_risk_information import (
    create_business_partner_risk_information_examples,
)
from evaluation.golden_dataset_creation.business_partner_search import (
    create_business_partner_search_examples,
)
from evaluation.golden_dataset_creation.country_origin import (
    create_country_origin_examples,
)
from evaluation.golden_dataset_creation.country_risk_information import (
    create_country_risk_information_examples,
)
from evaluation.golden_dataset_creation.feedback_2025_08_28 import (
    create_feedback_2025_08_28_examples,
)
from evaluation.golden_dataset_creation.feedback_2025_09_09 import (
    create_feedback_2025_09_08_examples,
)
from evaluation.golden_dataset_creation.feedback_2025_09_11 import (
    create_feedback_2025_09_11_examples,
)
from evaluation.golden_dataset_creation.feedback_2025_09_25 import (
    create_feedback_2025_09_25_examples,
)
from evaluation.golden_dataset_creation.natural_resource_search import (
    create_natural_resource_search_examples,
)


def main() -> None:
    create_business_partner_risk_information_examples()
    create_business_partner_search_examples()
    create_country_origin_examples()
    create_business_partner_priority_examples()
    create_branch_comparison_examples()
    create_business_partner_numbers_examples()
    create_business_partner_distribution_examples()
    create_country_risk_information_examples()
    create_natural_resource_search_examples()
    create_feedback_2025_08_28_examples()
    create_feedback_2025_09_08_examples()
    create_feedback_2025_09_11_examples()
    create_feedback_2025_09_25_examples()


if __name__ == "__main__":
    main()
