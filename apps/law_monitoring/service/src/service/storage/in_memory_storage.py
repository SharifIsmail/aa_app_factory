import json
from datetime import datetime
from typing import Any

from loguru import logger

from service.storage.data_storage import DataStorage


class InMemoryStorage(DataStorage):
    def define_repo(self, repo_key: str) -> bool:
        if repo_key not in self.repositories:
            self.repositories[repo_key] = {}
            return True
        return False

    def store_to_repo(self, repo_key: str, data_key: str, data_item: Any) -> None:
        if isinstance(data_item, str):
            data_item = {"data": data_item}
        data_item = self._preprocess_data_for_storage(data_item)
        logger.debug(
            f"Storing data in repo '{repo_key}' with key '{data_key}': {type(data_item).__name__}"
        )
        self.repositories[repo_key][data_key] = data_item

    def _preprocess_data_for_storage(self, data_item: Any) -> Any:
        if isinstance(data_item, datetime):
            return data_item.isoformat()
        elif isinstance(data_item, dict):
            return {
                k: self._preprocess_data_for_storage(v) for k, v in data_item.items()
            }
        elif isinstance(data_item, list):
            return [self._preprocess_data_for_storage(item) for item in data_item]
        else:
            return data_item

    def retrieve_all_from_repo(self, repo_key: str) -> dict[str, Any]:
        return self.repositories.get(repo_key, {})

    def clear_repo(self, repo_key: str) -> None:
        self.repositories[repo_key] = {}

    def repo_length(self, repo_key: str) -> int:
        return len(self.repositories[repo_key])

    def to_json(self) -> str:
        return json.dumps(self.repositories, indent=2)

    def from_json(self, json_str: str) -> None:
        self.repositories = {}
        try:
            repositories = json.loads(json_str)
            if not isinstance(repositories, dict):
                raise ValueError(
                    f"Invalid JSON format: expected dictionary but got {type(repositories).__name__}"
                )
            for repo_key, repo_data in repositories.items():
                if isinstance(repo_data, dict):
                    self.define_repo(repo_key)
                    for data_key, data_item in repo_data.items():
                        self.store_to_repo(repo_key, data_key, data_item)
        except Exception as e:
            logger.error(f"Error loading JSON data: {str(e)}")
            raise
