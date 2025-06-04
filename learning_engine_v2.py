# learning_engine_v2.py – Association‑Rule Miner (KB‑ready, DB/CSV flexible)
# --------------------------------------------------------------




from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from pathlib import Path
import json    
import itertools  # YENİ: döngüsel pencere için

CHUNK_SIZE = 250           # her seferde işlenecek kayıt sayısı
STATE_FILE = ".rule_miner_state.json"   # son offset burada tutulur

try:
    import pyodbc
except ImportError:  # DB bağlantısı şart değil
    pyodbc = None

# --------------------------------------------------------------
# Logging
# --------------------------------------------------------------
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------
# Döngüsel pencere için yardımcılar
# --------------------------------------------------------------
def _load_miner_state() -> int:
    """STATE_FILE'dan son offset'i oku, yoksa 0 döner."""
    if not Path(STATE_FILE).exists():
        return 0
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("offset", 0)
    except Exception:
        return 0

def _save_miner_state(offset: int) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"offset": offset}, f)



# --------------------------------------------------------------
# Veri kaynakları
# --------------------------------------------------------------

def sql_connect(conn_str: str | None = None):
    """ODBC connection helper. conn_str None → env → default."""
    if not pyodbc:
        raise RuntimeError("pyodbc is not installed – install or use --csv path instead.")

    conn_str = (
        conn_str
        or os.getenv("SQLSERVER_CONN")
        or r"DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-7GK6MUOG\\SQLEXPRESS;DATABASE=Smart_Plant_Recomandation_System;Trusted_Connection=yes;"
    )
    logger.info("ODBC connecting → %s", conn_str.split("SERVER=")[1].split(";")[0])
    return pyodbc.connect(conn_str, timeout=5)


def fetch_feedback_from_db() -> pd.DataFrame:
    """DB'den CHUNK_SIZE kayıt getirir; offset STATE_FILE'da döngülü ilerler."""
    offset = _load_miner_state()
    conn = sql_connect()

    # id yerine tablonuzdaki birincil anahtar adını (PK) kullanın
    query = f"""
        SELECT *
        FROM (
            SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS rn
            FROM Feedback
        ) AS t
        WHERE rn > {offset} AND rn <= {offset + CHUNK_SIZE}
    """

    df = pd.read_sql(query, conn)

    # Toplam satır sayısını bul, offset'i güncelle
    total_rows = pd.read_sql("SELECT COUNT(*) AS cnt FROM Feedback", conn).iloc[0, 0]
    conn.close()

    new_offset = offset + CHUNK_SIZE
    if new_offset >= total_rows:         # sona geldiysek başa sar
        new_offset = 0
    _save_miner_state(new_offset)

    logger.info(" Chunk [%d – %d] arası %d kayıt çekildi.", offset, offset + CHUNK_SIZE, len(df))
    return df


# --------------------------------------------------------------
# Canonical kategorik sütunlar
# --------------------------------------------------------------
CAT_COLS = [ "area_size", "sunlight_need", "environment_type", "climate_type",
            "watering_frequency", "fertilizer_frequency", "pesticide_frequency", "has_pet", "has_child"]

# EKLEYİN  (yeni satır)
ITEM_COLS = CAT_COLS + ["suggested_plant"]   # One-hot’a girecek tüm sütunlar

# --------------------------------------------------------------
# Yardımcı fonksiyonlar
# --------------------------------------------------------------

def _split_item(item: str, cat_cols: List[str]) -> Tuple[str, str]:
    for col in cat_cols:
        prefix = f"{col}_"
        if item.startswith(prefix):
            return col, item[len(prefix) :].replace("_", " ")
    idx = item.find("_")
    return item[:idx], item[idx + 1 :].replace("_", " ")


def _parse_rules(rules_df: pd.DataFrame, feedback_flag: int) -> List[Dict]:
    parsed: List[Dict] = []
    for _, row in rules_df.iterrows():
        conds: Dict[str, List[str]] = {}
        for item in row["antecedents"]:
            col, val = _split_item(str(item), CAT_COLS)
            conds.setdefault(col, []).append(val)
        plant_item = next(x for x in row["consequents"] if str(x).startswith("suggested_plant_"))
        _, plant_name = _split_item(str(plant_item), ["suggested_plant"])
        parsed.append(
            {
                "conditions": conds,
                "suggested_plant": plant_name,
                "feedback": feedback_flag,
                "support": float(row["support"]),
                "confidence": float(row["confidence"]),
                "lift": float(row["lift"]),
            }
        )
    return parsed

# --------------------------------------------------------------
# Ana madencilik rutini
# --------------------------------------------------------------

def mine_association_rules(
    df: pd.DataFrame,
    *,
    min_support: float = 0.005,
    min_confidence: float = 0.1,
    output_path: str = "parsed_rules.json",
) -> None:
    parsed: List[Dict] = []

    def _mine(df_sub: pd.DataFrame, flag: int):
        if df_sub.empty:
            logger.info("No records for feedback=%d", flag)
            return
        
        trans = pd.get_dummies(df_sub[ITEM_COLS].astype(str))
          
        freq = fpgrowth(
            trans,
            min_support=min_support,
            use_colnames=True,
        )

     
        rules = association_rules(
            freq,
            metric="confidence",
            min_threshold=min_confidence
        )

       

        rules = rules[
            rules["consequents"].apply(lambda idx: any(str(x).startswith("suggested_plant_") for x in idx))
        ]
        rules["rule_key"] = rules.apply(lambda row: (
            frozenset(row["antecedents"]),
            frozenset(row["consequents"])
        ), axis=1)
        rules = rules.drop_duplicates(subset=["rule_key"])

         # Lift’e göre sırala, ilk 20 kuralı tut
        rules = rules.sort_values("lift", ascending=False).head(20)
        unique_keys = set()
        filtered_rules = []

        for rule in _parse_rules(rules, flag):
            try:
                rule_key = (
                    frozenset((k, tuple(v)) for k, v in rule["conditions"].items()),
                    rule["suggested_plant"],
                    rule["feedback"]
                )
                if rule_key not in unique_keys:
                    filtered_rules.append(rule)
                    unique_keys.add(rule_key)
            except Exception as e:
                logger.warning("Rule parse error: %s", e)


        logger.info("feedback=%d → %d rules after filter", flag, len(rules))
        parsed.extend(_parse_rules(rules, flag))

    _mine(df[df["user_feedback"] == 1], 1)
    _mine(df[df["user_feedback"] == 0], 0)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d parsed rules → %s", len(parsed), output_path)

# --------------------------------------------------------------
# CLI
# --------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mine association rules for KB")
    parser.add_argument("--csv", help="Optional CSV path instead of DB query")
    parser.add_argument("--min-support", type=float, default=0.01)
    parser.add_argument("--min-confidence", type=float, default=0.3)
    parser.add_argument("--output", default="parsed_rules.json")
    args = parser.parse_args()

    if args.csv:
        df_feedback = pd.read_csv(args.csv)
        logger.info("Loaded %d records from CSV %s", len(df_feedback), args.csv)
    else:
        try:
            df_feedback = fetch_feedback_from_db()
        except Exception as exc:
            logger.error("DB connection failed (%s). Tip: set SQLSERVER_CONN env or use --csv.", exc)
            raise SystemExit(1)

    mine_association_rules(
        df_feedback,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        output_path=args.output,
    )
