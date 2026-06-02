"""
Split schedules.json into 3 chunks for GitHub upload.

Run this LOCALLY before pushing to GitHub:
    python split_schedules.py

Output: data/schedules_1.json, schedules_2.json, schedules_3.json
After splitting, delete or .gitignore the original schedules.json
"""

import json
import os

DATA_DIR  = "data"
INPUT     = os.path.join(DATA_DIR, "schedules.json")
CHUNK_SIZE = 175000  # records per file — keeps each file ~30MB

print(f"Reading {INPUT} ...")
with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

total  = len(data)
chunks = [data[i : i + CHUNK_SIZE] for i in range(0, total, CHUNK_SIZE)]

print(f"Total records : {total:,}")
print(f"Chunks        : {len(chunks)}")

for idx, chunk in enumerate(chunks, start=1):
    out_path = os.path.join(DATA_DIR, f"schedules_{idx}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunk, f)
    size_mb = os.path.getsize(out_path) / 1_000_000
    print(f"  ✓ {out_path}  —  {len(chunk):,} records  —  {size_mb:.1f} MB")

print("\nDone. You can now push data/ to GitHub.")
print("Add the original schedules.json to .gitignore:")
print("  echo 'data/schedules.json' >> .gitignore")
