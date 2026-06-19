"""Run once locally: slims the full 75MB StatCan CSV down to just what the map needs."""
import pandas as pd

FULL = "data/health_canada.csv"     # your full 75MB file (keep local, git-ignore it)
SLIM = "data/map_slim.csv"          # the small file you commit + deploy

KEEP = ["REF_DATE", "GEO", "Age group", "Sex", "Indicators", "UOM", "Characteristics", "VALUE", "STATUS"]

df = pd.read_csv(FULL, usecols=KEEP)          # usecols keeps memory low while reading
slim = df[(df["UOM"] == "Percent") & (df["Characteristics"] == "Percent")].copy()

slim.to_csv(SLIM, index=False)
import os
print(f"rows: {len(df):,} -> {len(slim):,}")
print(f"size: {os.path.getsize(FULL)/1e6:.1f} MB -> {os.path.getsize(SLIM)/1e6:.2f} MB")
print(f"wrote {SLIM}")
