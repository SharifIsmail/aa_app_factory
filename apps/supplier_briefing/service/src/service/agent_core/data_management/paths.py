from pathlib import Path


def get_data_dir() -> Path:
    service_dir = Path(__file__).parent.parent.parent.parent.parent
    return service_dir / "data"
