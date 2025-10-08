import os
from typing import Any

from fastapi import APIRouter

router = APIRouter()


# Create the webmanifest file base on the contents
# of the icons directory
def _get_icon_entries() -> list[dict[str, str]]:
    ICONS_DIR = "icons"
    icons: list[dict[str, str]] = []
    if not os.path.isdir(ICONS_DIR):
        return icons
    for fname in os.listdir(ICONS_DIR):
        if fname.lower().endswith(".svg"):
            icons.append(
                {
                    "src": f"/ui/icons/{fname}",
                    "type": "image/svg+xml",
                }
            )
        elif fname.lower().endswith(".png"):
            icons.append(
                {
                    "src": f"/ui/icons/{fname}",
                    "type": "image/png",
                }
            )
    return icons


ICONS = _get_icon_entries()


@router.get("/manifest.webmanifest")
def get_manifest() -> dict[str, Any]:
    return {"icons": ICONS}
