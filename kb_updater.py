# kb_updater.py – Knowledge‑base maintenance utility
# --------------------------------------------------------------
# • Reads freshly parsed rules (JSON) that include a `feedback` flag
# • Normalises condition keys/values so they match UI / RuleEngine schema
# • Merges the rules into knowledge_base.json → positive_rules / negative_rules
# • Designed so that `pytest` tests (e.g. test_update_kb_rules_split) pass by
#   exposing *update_knowledge_base(parsed_path, kb_path)*
# --------------------------------------------------------------

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# --------------------------------------------------------------
# 🔑 Key mapping – raw → canonical
# --------------------------------------------------------------
KEY_MAP = {
    "sunlight": "sunlight_need",
    "area": "area_size",
    "environment": "environment_type",
    "climate": "climate_type",
    "fertilizer": "fertilizer_frequency",
    "pesticide": "pesticide_frequency",
}

_PREFIXES = (
    "need ",
    "size ",
    "type ",
    "frequency ",
    "pet ",
    "child ",
)

# --------------------------------------------------------------
# 🧹 Helpers
# --------------------------------------------------------------

def _clean_value(val: str) -> str:
    """Remove known textual prefixes & surrounding whitespace."""
    for pre in _PREFIXES:
        if val.startswith(pre):
            val = val[len(pre) :]
            break
    return val.strip()


def _normalise_conditions(raw: Dict[str, List[str] | str]) -> Dict[str, str]:
    """Convert raw condition dict into canonical key/value map compatible with RuleEngine."""
    norm: Dict[str, str] = {}

    for key, raw_val in raw.items():
        # Always treat value as list for uniform processing
        values: List[str]
        if isinstance(raw_val, list):
            values = raw_val
        else:
            values = [raw_val]

        if key == "has":
            # Expect patterns like "pet Yes" or "child No" etc.
            for token in values:
                try:
                    subkey, subval = token.split(" ", 1)
                except ValueError:
                    logger.warning("Cannot split 'has' token %s – skipping", token)
                    continue
                canon_key = f"has_{subkey}"
                norm[canon_key] = _clean_value(subval)
            continue

        canon_key = KEY_MAP.get(key, key)
        # For now assume single‑valued condition after cleaning
        norm[canon_key] = _clean_value(values[0])

    return norm



# --------------------------------------------------------------
#  Public API – used by tests & CLI
# --------------------------------------------------------------

def update_knowledge_base(parsed_path: str | Path, kb_path: str | Path) -> None:
    """
    Merge parsed rules into knowledge_base.json after normalising keys/values.

    Parameters
    ----------
    parsed_path : str | Path
        Path to JSON file produced by rule parser / learning engine. Expected format:
        [{"conditions": {...}, "suggested_plant": "...", "feedback": 1}, ...]
    kb_path : str | Path
        Existing knowledge_base.json. Will be overwritten in-place after merge.
    """
    parsed_path = Path(parsed_path)
    kb_path = Path(kb_path)

    # --- JSON dosyalarını oku ------------------------------------------------
    with parsed_path.open("r", encoding="utf-8") as f:
        parsed_rules = json.load(f)

    with kb_path.open("r", encoding="utf-8") as f:
        kb = json.load(f)

    # --- Hedef listelerin varlığını garanti et ------------------------------
    kb.setdefault("positive_rules", [])
    kb.setdefault("negative_rules", [])

    # --- Hash yardımı: koşullardaki list → tuple, böylece hashlenebilir -------
    def rule_hash(r: dict) -> tuple:
        cond = tuple(
    sorted(
        (k, tuple(v) if isinstance(v, list) else v)   # ← list → tuple
        for k, v in r["conditions"].items()
    )
)
        

        return (cond, r["suggested_plant"])

    existing_pos = {rule_hash(r) for r in kb["positive_rules"]}
    existing_neg = {rule_hash(r) for r in kb["negative_rules"]}

    added_pos = added_neg = 0

    # --- Yeni kuralları ekle -------------------------------------------------
    for raw in parsed_rules:
        plant = raw.get("suggested_plant")
        feedback = int(raw.get("feedback", 1))       # default = positive
        norm_conditions = _normalise_conditions(raw.get("conditions", {}))

        rule_dict = {
            "conditions": norm_conditions,
            "suggested_plant": plant,
            "feedback": feedback,
        }
        rule_id = rule_hash(rule_dict)

        if feedback == 1:                            # --- pozitif kural
            if rule_id not in existing_pos:
                kb["positive_rules"].append(rule_dict)
                existing_pos.add(rule_id)
                added_pos += 1
        else:                                        # --- negatif kural
            if rule_id not in existing_neg:
                kb["negative_rules"].append(rule_dict)
                existing_neg.add(rule_id)
                added_neg += 1
        def cond_key(rule): return tuple(sorted(rule["conditions"].items()))
    pos_map = {cond_key(r): r for r in kb["positive_rules"]}
    neg_map = {cond_key(r): r for r in kb["negative_rules"]}
    conflicts = set(pos_map.keys()) & set(neg_map.keys())

    for key in conflicts:
        pos_lift = pos_map[key].get("lift", 1.0)
        neg_lift = neg_map[key].get("lift", 1.0)
        if pos_lift >= neg_lift:
            del neg_map[key]
        else:
            del pos_map[key]

    seen_plants = set()
    unique_positive = []
    for rule in pos_map.values():
        plant = rule["suggested_plant"]
        if plant not in seen_plants:
            unique_positive.append(rule)
            seen_plants.add(plant)
    kb["positive_rules"] = unique_positive

    # --- Negatifler isteğe bağlı olarak sadeleştirilebilir
    kb["negative_rules"] = list(neg_map.values())
    # --- Dosyaya yaz ---------------------------------------------------------
    with kb_path.open("w", encoding="utf-8") as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)

    logger.info(
        "KB updated → +%d positive, +%d negative (total: %d pos, %d neg)",
        added_pos,
        added_neg,
        len(kb['positive_rules']),
        len(kb['negative_rules']),
    )


# --------------------------------------------------------------
#  Optional CLI usage: python kb_updater.py --parsed parsed_rules.json --kb knowledge_base.json
# --------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Merge parsed rules into knowledge_base.json")
    parser.add_argument("--parsed", required=True, help="Path to parsed_rules.json")
    parser.add_argument("--kb", required=True, help="Path to knowledge_base.json to update")
    args = parser.parse_args()

    update_knowledge_base(args.parsed, args.kb)
