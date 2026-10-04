"""Freeze the exact dated CSV slices used by the FRVP release gate.

Run this only when deliberately adding or replacing a reviewed fixture.  The
release attestation hashes every generated file, so an accidental fixture
change invalidates the validated release.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


FIXTURE_DIR = Path(__file__).with_name("fixtures") / "frvp"

# output name -> (reviewed source export, exchange-date slice)
FIXTURES = {
    "amod_2026-10-02_11a4e.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_AMOD, 1_11a4e.csv", "2026-10-02"
    ),
    "apus_2026-09-24_47305.csv": (
        "/Users/ayaffe/Downloads/AMEX_APUS, 1_47305.csv", "2026-09-24"
    ),
    "apus_2026-09-25_a4f2d.csv": (
        "/Users/ayaffe/Downloads/AMEX_APUS, 1_a4f2d.csv", "2026-09-25"
    ),
    "boxl_2026-08-12_fe518.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_BOXL, 1_fe518.csv", "2026-08-12"
    ),
    "cmct_2026-09-30_69205.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_CMCT, 1_69205.csv", "2026-09-30"
    ),
    "elpw_2026-09-25_de341.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_ELPW, 1_de341.csv", "2026-09-25"
    ),
    "knrx_2026-09-28_d348a.csv": (
        "/Users/ayaffe/Downloads/AMEX_KNRX, 1_d348a.csv", "2026-09-28"
    ),
    "lghl_2026-09-30_504a7.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_LGHL, 1_504a7.csv", "2026-09-30"
    ),
    "nxl_2026-10-01_840ce.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_NXL, 1_840ce.csv", "2026-10-01"
    ),
    "sdot_2026-06-26_45c94.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_SDOT, 1_45c94.csv", "2026-06-26"
    ),
    "sdev_2026-09-29_51b3f.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_51b3f.csv", "2026-09-29"
    ),
    "sdev_2026-09-29_138e9.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_138e9.csv", "2026-09-29"
    ),
    "sdev_2026-09-29_6c7b8.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_6c7b8.csv", "2026-09-29"
    ),
    "sdev_2026-09-30_7a5bd.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_7a5bd.csv", "2026-09-30"
    ),
    "sdev_2026-09-30_a770d.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_a770d.csv", "2026-09-30"
    ),
    "sdev_2026-10-01_7a5bd.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_7a5bd.csv", "2026-10-01"
    ),
    "sdev_2026-10-02_138e9.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_138e9.csv", "2026-10-02"
    ),
    "sdev_2026-10-02_7a5bd.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_7a5bd.csv", "2026-10-02"
    ),
    "sdev_2026-10-02_9f6d3.csv": (
        "/Users/ayaffe/Downloads/AMEX_SDEV, 1_9f6d3.csv", "2026-10-02"
    ),
    "ssm_2026-10-01_7b6c2.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_SSM, 1_7b6c2.csv", "2026-10-01"
    ),
    "veee_2026-07-13_dc82b.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_VEEE, 1_dc82b.csv", "2026-07-13"
    ),
    "weto_2026-08-17_ec6ab.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_WETO, 1_ec6ab.csv", "2026-08-17"
    ),
    "wff_2026-08-17_05f96.csv": (
        "/Users/ayaffe/Downloads/NASDAQ_WFF, 1_05f96.csv", "2026-08-17"
    ),
}


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for output_name, (source_name, date) in FIXTURES.items():
        source = Path(source_name)
        if not source.exists():
            raise FileNotFoundError(source)
        data = pd.read_csv(source)
        timestamps = pd.to_datetime(data["time"])
        dated = data[timestamps.dt.strftime("%Y-%m-%d") == date].copy()
        if dated.empty:
            raise RuntimeError(f"{source} contains no rows for {date}")
        output = FIXTURE_DIR / output_name
        dated.to_csv(output, index=False)
        print(f"{output.name}: {len(dated)} rows")


if __name__ == "__main__":
    main()
