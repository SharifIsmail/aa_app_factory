import os
from pathlib import Path

from service.dependencies import with_settings
from service.pharia_data_storage_backend import PhariaDataStorageBackend


class RawDataSyncer:
    def __init__(self) -> None:
        self._local_base_directory_raw_data = Path("data")
        self._settings = with_settings()
        self._pharia_data_url = self._settings.pharia_data_url
        self._pharia_data_stage_name = "raw_data"
        self._pharia_data_folder_raw_data = "raw_data"
        self._pharia_data_storage_backend = PhariaDataStorageBackend(
            base_url=self._pharia_data_url,
            token=os.environ.get("SERVICE_AUTHENTICATION_TOKEN"),
            stage_name=self._pharia_data_stage_name,
        )

    def retrieve_data_from_pharia_data(self, filename: str) -> None:
        file_content = self._pharia_data_storage_backend.load_file(
            folder=self._pharia_data_folder_raw_data, filename=filename
        )
        with open(self._local_base_directory_raw_data / filename, "wb") as f:
            f.write(file_content)

    def store_data_in_pharia_data(self, filename: str) -> None:
        file_content = open(self._local_base_directory_raw_data / filename, "rb").read()
        self._pharia_data_storage_backend.save_file(
            folder=self._pharia_data_folder_raw_data,
            filename=filename,
            content=file_content,
        )
