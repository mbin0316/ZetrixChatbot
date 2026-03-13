import pandas as pd
from langchain_core.documents import Document


def _fmt(value) -> str:
    """Format a number as RM string, or 'N/A' if missing."""
    try:
        return f"RM{int(float(value)):,}"
    except (ValueError, TypeError):
        return "N/A"


def _year(date_str) -> str:
    return str(date_str)[:4]


def _doc(text: str, meta: dict) -> Document:
    return Document(page_content=text, metadata=meta)


# ── One converter per file ────────────────────────────────────────────────────

def convert_national(row) -> Document:
    y = _year(row["date"])
    text = (
        f"In {y}, Malaysia's national mean household income was {_fmt(row['income_mean'])} "
        f"and median was {_fmt(row['income_median'])}. Source: hh_income.csv (DOSM)."
    )
    return _doc(text, {"source": "hh_income.csv", "level": "national",
                        "year": y, "state": "Malaysia", "date": str(row["date"])})


def convert_state(row) -> Document:
    y, state = _year(row["date"]), str(row["state"])
    median = ("median data not available" if pd.isna(row["income_median"])
              else f"median was {_fmt(row['income_median'])}")
    text = (
        f"In {y}, {state}'s mean household income was {_fmt(row['income_mean'])} "
        f"and {median}. Source: hh_income_state.csv (DOSM)."
    )
    return _doc(text, {"source": "hh_income_state.csv", "level": "state",
                        "year": y, "state": state, "date": str(row["date"])})


def convert_district(row) -> Document:
    y, state, district = _year(row["date"]), str(row["state"]), str(row["district"])
    text = (
        f"In {y}, {district} district in {state} had mean {_fmt(row['income_mean'])} "
        f"and median {_fmt(row['income_median'])}. Source: hh_income_district.csv (DOSM)."
    )
    return _doc(text, {"source": "hh_income_district.csv", "level": "district",
                        "year": y, "state": state, "district": district, "date": str(row["date"])})


def convert_parlimen(row) -> Document:
    y, state, parlimen = _year(row["date"]), str(row["state"]), str(row["parlimen"])
    text = (
        f"In {y}, parliamentary constituency {parlimen} ({state}) had mean {_fmt(row['income_mean'])} "
        f"and median {_fmt(row['income_median'])}. Source: hh_income_parlimen.csv (DOSM)."
    )
    return _doc(text, {"source": "hh_income_parlimen.csv", "level": "parlimen",
                        "year": y, "state": state, "parlimen": parlimen, "date": str(row["date"])})


def convert_dun(row) -> Document:
    y, state = _year(row["date"]), str(row["state"])
    parlimen, dun = str(row["parlimen"]), str(row["dun"])
    text = (
        f"In {y}, state constituency {dun} (under {parlimen}, {state}) had mean {_fmt(row['income_mean'])} "
        f"and median {_fmt(row['income_median'])}. Source: hh_income_dun.csv (DOSM)."
    )
    return _doc(text, {"source": "hh_income_dun.csv", "level": "dun",
                        "year": y, "state": state, "parlimen": parlimen, "dun": dun, "date": str(row["date"])})


# ── Registry: filename → converter function ───────────────────────────────────

FILE_CONVERTERS = {
    "hh_income.csv":          convert_national,
    "hh_income_state.csv":    convert_state,
    "hh_income_district.csv": convert_district,
    "hh_income_parlimen.csv": convert_parlimen,
    "hh_income_dun.csv":      convert_dun,
}