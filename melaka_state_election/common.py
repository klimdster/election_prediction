"""Shared paths and helpers for the Melaka SE-16 model."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
INPUT = ROOT / "data" / "input"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

LAKE = "https://lake.electiondata.my"
SOURCES = {
    "headline_ballots_state_mlk.csv": f"{LAKE}/results_headline/headline_ballots_state_mlk.csv",
    "headline_stats_state_mlk.csv": f"{LAKE}/results_headline/headline_stats_state_mlk.csv",
    "headline_ballots_state_jhr.csv": f"{LAKE}/results_headline/headline_ballots_state_jhr.csv",
    "peninsular_2018_dun.geojson": f"{LAKE}/maps/delimitations/peninsular_2018_dun.geojson",
}

SEAT_RE = r"N\.?\s*0*(\d+)"


def seat_no(series: pd.Series) -> pd.Series:
    """'N.01 Kuala Linggi' / 'N01' / 'N.1' -> 1"""
    return series.str.extract(SEAT_RE, expand=False).astype(int)


def seat_name(series: pd.Series) -> pd.Series:
    return series.str.replace(r"^N\.?\s*\d+\s*", "", regex=True).str.strip()


def load_ballots(state: str = "mlk") -> pd.DataFrame:
    b = pd.read_csv(RAW / f"headline_ballots_state_{state}.csv")
    b["n"] = seat_no(b.seat)
    b["seat_name"] = seat_name(b.seat)
    return b


def load_stats() -> pd.DataFrame:
    s = pd.read_csv(RAW / "headline_stats_state_mlk.csv")
    s["n"] = seat_no(s.seat)
    return s


def load_ethnic() -> pd.DataFrame:
    """Electorate ethnic mix (fractions), index = seat number 1..28."""
    e = json.load(open(INPUT / "ethnic_mix_2026.json"))
    E = pd.DataFrame({int(k[1:]): v for k, v in e.items()}).T
    return E[["Malay", "Chinese", "Indian", "Other"]].astype(float) / 100


# Party -> 2026 bloc. Bersatu ran alone in 2026, so it is its own bloc.
BLOC_2026 = {
    "UMNO": "BNPN", "MCA": "BNPN", "MIC": "BNPN",
    "PAS": "BNPN", "WAWASAN": "BNPN", "GERAKAN": "BNPN",
    "PKR": "PH", "DAP": "PH", "AMANAH": "PH",
    "BERSATU": "BERSATU", "BERSAMA": "BERSAMA",
}


def bloc_of(party: str) -> str:
    return BLOC_2026.get(party, "OTH")
