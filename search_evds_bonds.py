#!/usr/bin/env python3
"""
Search EVDS for TR 2Y and 10Y Benchmark Bond Yield series codes.
Uses EVDS_API_KEY from .env. Verifies data availability.
Metadata endpoints (categories/datagroups/serieList) return 403 - testing candidates directly.
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")
API_KEY = os.getenv("EVDS_API_KEY")
BASE = "https://evds2.tcmb.gov.tr/service/evds"

if not API_KEY or len(API_KEY) < 5:
    print("ERROR: EVDS_API_KEY not found or invalid in .env")
    sys.exit(1)

HEADERS = {"key": API_KEY}

# Known/plausible EVDS bond series codes to try
# From: FAİZ VE KÂR PAYI (collapse_3), MENKUL KIYMET (collapse_5), DİĞER FİNANSAL (collapse_31)
CANDIDATE_SERIES = [
    "TP.TAHVIL.Y2",
    "TP.TAHVIL.Y10",
    "TP.DK.GSY.G02",
    "TP.DK.GSY.G10",
    "TP.DK.GSY.2Y",
    "TP.DK.GSY.10Y",
    "TP.GOST2.Y",
    "TP.GOST10.Y",
    "TP.DK.GSY.A.2",
    "TP.DK.GSY.A.10",
    "TP.DK.GSY.G2",
    "TP.DK.GSY",
    "TP.FB.TAHVIL.2Y",
    "TP.FB.TAHVIL.10Y",
    "TP.FB.GOST.2Y",
    "TP.FB.GOST.10Y",
    "TP.TAHVIL.G02",
    "TP.TAHVIL.G10",
    "TP.TIG02",
    "TP.TIG10",
    "TP.DK.2Y",
    "TP.DK.10Y",
    "TP.DK.GSY.A02",
    "TP.DK.GSY.A10",
    "TP.DK.GSY.02",
    "TP.DK.GSY.10",
]


def fetch_datagroup(datagroup_code, days=10):
    """Fetch via datagroup API (returns multiple series)."""
    end = datetime.now()
    start = end - timedelta(days=days)
    url = f"{BASE}/datagroup={datagroup_code}"
    params = {
        "startDate": start.strftime("%d-%m-%Y"),
        "endDate": end.strftime("%d-%m-%Y"),
        "type": "json"
    }
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("items", [])
    except Exception as e:
        return None


# Datagroups that may contain bond yields (EVDS datagroup= endpoint)
DATAGROUP_CANDIDATES = ["bie_abtkry", "bie_abtkfaiz", "bie_dkdovytl"]


def fetch_series_data(series_code, days=10):
    """Fetch last N days of data for a series."""
    end = datetime.now()
    start = end - timedelta(days=days)
    url = f"{BASE}/series={series_code}"
    params = {
        "startDate": start.strftime("%d-%m-%Y"),
        "endDate": end.strftime("%d-%m-%Y"),
        "type": "json"
    }
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("items", []) if isinstance(data, dict) else []
    except Exception as e:
        return None


def has_valid_recent_data(series_code):
    """Check if series has non-null recent data."""
    items = fetch_series_data(series_code, days=10)
    if not items:
        return False, "No items / API error"
    col = series_code.replace(".", "_")
    for row in reversed(items):
        val = row.get(col)
        if val is not None and str(val).strip() and str(val).lower() != "nan":
            try:
                f = float(val)
                if f > 0:
                    return True, val
            except (ValueError, TypeError):
                pass
    return False, "All null/empty"


def main():
    print("=" * 60)
    print("EVDS Bond Series Search - TR 2Y & 10Y Benchmark")
    print("=" * 60)
    print("\nTesting candidate series (last 10 days)...")

    verified_2y = []
    verified_10y = []
    verified_other = []

    # Try datagroups first
    for dg in DATAGROUP_CANDIDATES:
        items = fetch_datagroup(dg, days=10)
        if items and len(items) > 0:
            cols = [k for k in items[0].keys() if k not in ("Tarih", "UNIXTIME", "YEARWEEK") and "_" in k]
            bond_cols = [c for c in cols if any(x in c.upper() for x in ["TAHVIL", "GSY", "2", "10", "DK"])]
            if bond_cols:
                for c in bond_cols[:4]:
                    last = items[-1].get(c)
                    if last and str(last).replace(".", "").isdigit():
                        verified_other.append((f"{dg}::{c}", last))
                        print(f"  OK (datagroup): {dg} -> col {c} = {last}")

    for code in CANDIDATE_SERIES:
        ok, val = has_valid_recent_data(code)
        if ok:
            code_upper = code.upper()
            if any(x in code_upper for x in ["Y2", "2Y", ".2.", "G02", "G2", "A02", ".02"]):
                verified_2y.append((code, val))
                print(f"  OK 2Y: {code} -> {val}")
            elif any(x in code_upper for x in ["Y10", "10Y", ".10.", "G10", "A10"]):
                verified_10y.append((code, val))
                print(f"  OK 10Y: {code} -> {val}")
            else:
                verified_other.append((code, val))
                print(f"  OK (other): {code} -> {val}")

    print("\n" + "=" * 60)
    print("VERIFIED SERIES CODES")
    print("=" * 60)

    print("\n--- TR 2-Year Benchmark Bond Yield ---")
    if verified_2y:
        for code, val in verified_2y:
            print(f"  Code: {code}")
            print(f"  Latest value: {val}")
    else:
        print("  (none found with recent data)")

    print("\n--- TR 10-Year Benchmark Bond Yield ---")
    if verified_10y:
        for code, val in verified_10y:
            print(f"  Code: {code}")
            print(f"  Latest value: {val}")
    else:
        print("  (none found with recent data)")

    print("\n--- For config.json ---")
    tr_2y = verified_2y[0][0] if verified_2y else "TP.TAHVIL.Y2"
    tr_10y = verified_10y[0][0] if verified_10y else "TP.TAHVIL.Y10"
    print(f'  "tr_2y": "{tr_2y}",')
    print(f'  "tr_10y": "{tr_10y}"')


if __name__ == "__main__":
    main()
