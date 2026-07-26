"""Deterministic local-demo procurement catalog.

This catalog is intentionally scoped to the Telegram demo bridge. It contains
only explicit demo item metadata and aliases. It does not contain prices, stock,
delivery promises, supplier credentials, provider payloads, or real customer
data.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

CATALOG_VERSION = "demo-catalog-v1"
OFFICE_365_ADDON_ID = "office_365"


@dataclass(frozen=True)
class CatalogAddon:
    addon_id: str
    display_name: str
    aliases_en: tuple[str, ...]
    aliases_vi: tuple[str, ...]
    demo_only: bool = True

    @property
    def normalized_aliases(self) -> tuple[str, ...]:
        return tuple(normalize_for_catalog_match(alias) for alias in self.aliases)

    @property
    def aliases(self) -> tuple[str, ...]:
        return self.aliases_en + self.aliases_vi


@dataclass(frozen=True)
class CatalogItem:
    item_id: str
    display_name: str
    normalized_item_name: str
    item_family: str
    aliases_en: tuple[str, ...]
    aliases_vi: tuple[str, ...]
    supported_addons: tuple[str, ...]
    unit: str
    domain: str = "it_equipment"
    demo_only: bool = True

    @property
    def aliases(self) -> tuple[str, ...]:
        return self.aliases_en + self.aliases_vi

    @property
    def normalized_aliases(self) -> tuple[str, ...]:
        return tuple(normalize_for_catalog_match(alias) for alias in self.aliases)

    @property
    def workflow_metadata(self) -> dict[str, object]:
        return {
            "catalog_version": CATALOG_VERSION,
            "item_id": self.item_id,
            "display_name": self.display_name,
            "normalized_item_name": self.normalized_item_name,
            "item_family": self.item_family,
            "unit": self.unit,
            "demo_only": self.demo_only,
        }


OFFICE_365_ADDON = CatalogAddon(
    addon_id=OFFICE_365_ADDON_ID,
    display_name="Office 365",
    aliases_en=(
        "office 365",
        "microsoft 365",
        "m365",
    ),
    aliases_vi=(
        "cai office",
        "cai san office",
        "cai san office 365",
        "kem office",
        "ban quyen office",
        "co office",
        "co cai office",
    ),
)

CATALOG_ITEMS: tuple[CatalogItem, ...] = (
    CatalogItem(
        item_id="standard_business_laptop",
        display_name="Standard business laptop",
        normalized_item_name="Standard business laptop",
        item_family="business_laptop",
        aliases_en=(
            "laptop",
            "laptops",
            "business laptop",
            "business laptops",
            "standard business laptop",
            "standard business laptops",
            "notebook",
            "notebooks",
        ),
        aliases_vi=(
            "may tinh xach tay",
            "may tinh xach tay doanh nhan",
            "may tinh xach tay tieu chuan",
            "laptop doanh nhan",
            "laptop van phong",
            "may laptop van phong",
        ),
        supported_addons=(OFFICE_365_ADDON_ID,),
        unit="unit",
    ),
    CatalogItem(
        item_id="business_desktop_pc",
        display_name="Business desktop PC",
        normalized_item_name="Business desktop PC",
        item_family="business_desktop_pc",
        aliases_en=(
            "desktop",
            "desktops",
            "desktop pc",
            "desktop pcs",
            "business desktop",
            "business desktops",
            "business desktop pc",
            "business desktop pcs",
            "office desktop",
            "office desktops",
        ),
        aliases_vi=(
            "may tinh ban",
            "may tinh de ban",
            "may bo van phong",
        ),
        supported_addons=(OFFICE_365_ADDON_ID,),
        unit="unit",
    ),
    CatalogItem(
        item_id="office_monitor",
        display_name="Office monitor",
        normalized_item_name="Office monitor",
        item_family="office_monitor",
        aliases_en=(
            "monitor",
            "monitors",
            "office monitor",
            "office monitors",
            "display monitor",
            "display monitors",
        ),
        aliases_vi=(
            "man hinh",
            "man hinh van phong",
        ),
        supported_addons=(),
        unit="unit",
    ),
    CatalogItem(
        item_id="office_printer",
        display_name="Office printer",
        normalized_item_name="Office printer",
        item_family="office_printer",
        aliases_en=(
            "printer",
            "printers",
            "office printer",
            "office printers",
            "hp printer",
            "hp printers",
        ),
        aliases_vi=(
            "may in",
            "may in van phong",
            "may in hp",
        ),
        supported_addons=(),
        unit="unit",
    ),
    CatalogItem(
        item_id="wireless_keyboard_mouse_combo",
        display_name="Wireless keyboard and mouse combo",
        normalized_item_name="Wireless keyboard and mouse combo",
        item_family="keyboard_mouse_combo",
        aliases_en=(
            "keyboard mouse combo",
            "keyboard mouse combos",
            "wireless keyboard and mouse",
            "wireless keyboard and mouse combo",
            "wireless keyboard and mouse combos",
            "keyboard and mouse",
        ),
        aliases_vi=(
            "bo ban phim chuot",
            "ban phim chuot khong day",
            "combo phim chuot",
        ),
        supported_addons=(),
        unit="set",
    ),
)

CATALOG_ADDONS: tuple[CatalogAddon, ...] = (OFFICE_365_ADDON,)


def normalize_for_catalog_match(value: str) -> str:
    ascii_text = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    ascii_text = ascii_text.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def supported_item_families() -> tuple[str, ...]:
    return tuple(item.normalized_item_name for item in CATALOG_ITEMS)


def get_catalog_item_by_name(value: str) -> CatalogItem | None:
    normalized = normalize_for_catalog_match(value)
    for item in CATALOG_ITEMS:
        if normalized == normalize_for_catalog_match(item.normalized_item_name):
            return item
        if normalized == normalize_for_catalog_match(item.display_name):
            return item
    return None


def find_catalog_item(value: str) -> CatalogItem | None:
    normalized = normalize_for_catalog_match(value)
    for item in CATALOG_ITEMS:
        if alias_matches(normalized, item):
            return item
    return None


def alias_matches(normalized_value: str, item: CatalogItem) -> bool:
    for alias in sorted(item.normalized_aliases, key=len, reverse=True):
        if re.search(alias_regex(alias), normalized_value):
            return True
    return False


def alias_regex(alias: str) -> str:
    return r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"


def detect_requested_addons(value: str) -> tuple[str, ...]:
    normalized = normalize_for_catalog_match(value)
    found: list[str] = []
    for addon in CATALOG_ADDONS:
        if any(re.search(alias_regex(alias), normalized) for alias in addon.normalized_aliases):
            found.append(addon.addon_id)
    return tuple(dict.fromkeys(found))


def addon_display_label(addon_id: str) -> str:
    for addon in CATALOG_ADDONS:
        if addon.addon_id == addon_id:
            return addon.display_name
    return addon_id.replace("_", " ").title()


def compatible_addons(item: CatalogItem, addons: tuple[str, ...]) -> bool:
    return all(addon in item.supported_addons for addon in addons)
