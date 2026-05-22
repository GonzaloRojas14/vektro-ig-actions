"""
Render orchestrator: picks the right template based on entry['type'].
"""

import logging
from pathlib import Path

log = logging.getLogger(__name__)

_REGISTRY: dict[str, str] = {
    "tech_tip":     "generator.templates.tech_tip",
    "service_promo":"generator.templates.service_promo",
    "quote":        "generator.templates.quote",
    "data_viz":     "generator.templates.data_viz",
}


def render(entry: dict) -> Path:
    entry_type = entry.get("type", "").lower()
    module_path = _REGISTRY.get(entry_type)

    if not module_path:
        known = ", ".join(_REGISTRY.keys())
        raise ValueError(
            f"Unknown story type '{entry_type}'. Known types: {known}"
        )

    import importlib
    module = importlib.import_module(module_path)
    log.info("Rendering template '%s'", entry_type)
    return module.render(entry)
