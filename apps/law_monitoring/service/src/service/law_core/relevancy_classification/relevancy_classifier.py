from abc import ABC, abstractmethod

from service.models import (
    RelevancyClassifierLegalActInput,
    TeamRelevancy,
)


class RelevancyClassifier(ABC):
    @abstractmethod
    def classify(
        self, legal_act: RelevancyClassifierLegalActInput
    ) -> list[TeamRelevancy]:
        pass
