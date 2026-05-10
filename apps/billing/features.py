"""
Feature catalog.

Features are declared in `settings.BILLING_FEATURES`. Each entry is a plain
dict; entries are normalized into `Feature` dataclasses. Mirrors the
`apps.notifications.categories` pattern.

Example:
    BILLING_FEATURES = [
        {
            "key": "max_team_count",
            "label": "Teams",
            "description": "Number of teams you can create.",
            "type": "limit",      # "bool" | "limit"
            "default": 1,         # value when no plan / billing disabled
        },
        {
            "key": "advanced_reporting",
            "label": "Advanced reporting",
            "description": "PDF exports and scheduled reports.",
            "type": "bool",
            "default": False,
        },
    ]

The catalog drives the pricing-page comparison table and supplies fallback
values when an org has no active subscription.

"""

from dataclasses import dataclass
from typing import Any, Literal

from django.conf import settings

FeatureType = Literal["bool", "limit"]


@dataclass(frozen=True)
class Feature:
    key: str
    label: str
    description: str
    type: FeatureType
    default: Any


def _normalize(entry: dict) -> Feature:
    return Feature(
        key=entry["key"],
        label=entry.get("label", entry["key"]),
        description=entry.get("description", ""),
        type=entry.get("type", "bool"),
        default=entry.get("default", False),
    )


def get_feature(key: str) -> Feature | None:
    for entry in settings.BILLING_FEATURES:
        if entry.get("key") == key:
            return _normalize(entry)
    return None


def get_features() -> list[Feature]:
    return [_normalize(e) for e in settings.BILLING_FEATURES]
