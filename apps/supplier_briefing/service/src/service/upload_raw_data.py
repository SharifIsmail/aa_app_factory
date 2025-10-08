from service.data_preparation import (
    BRUTTO_FILE_EXCEL,
    CONCRETE_FILE_EXCEL,
    RESOURCE_RISKS_EXCEL,
)
from service.raw_data_syncer import RawDataSyncer


def upload_raw_data() -> None:
    RawDataSyncer().store_data_in_pharia_data(BRUTTO_FILE_EXCEL)
    RawDataSyncer().store_data_in_pharia_data(CONCRETE_FILE_EXCEL)
    RawDataSyncer().store_data_in_pharia_data(RESOURCE_RISKS_EXCEL)


if __name__ == "__main__":
    upload_raw_data()
