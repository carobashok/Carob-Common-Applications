"""
Indian Railways → Supabase Loader
Runs as a Streamlit app on Streamlit Cloud.

Deploy this as your app temporarily, run the load, then swap back to train_schedule.py.

Supabase credentials go in Streamlit Cloud → App Settings → Secrets:
    [supabase]
    url = "https://xxxxxx.supabase.co"
    key = "your_service_role_key"

STEP 0 — Run this SQL in Supabase SQL Editor BEFORE deploying:

    CREATE TABLE IF NOT EXISTS stations (
        station_code  TEXT PRIMARY KEY,
        station_name  TEXT,
        zone          TEXT,
        state         TEXT,
        address       TEXT,
        latitude      FLOAT,
        longitude     FLOAT
    );

    CREATE TABLE IF NOT EXISTS trains (
        train_number       TEXT PRIMARY KEY,
        train_name         TEXT,
        train_type         TEXT,
        from_station_code  TEXT,
        from_station_name  TEXT,
        to_station_code    TEXT,
        to_station_name    TEXT,
        departure          TEXT,
        arrival            TEXT,
        duration_h         INT,
        duration_m         INT,
        distance_km        INT,
        zone               TEXT,
        classes            TEXT,
        return_train       TEXT
    );

    CREATE TABLE IF NOT EXISTS schedules (
        id             BIGINT PRIMARY KEY,
        train_number   TEXT,
        train_name     TEXT,
        station_code   TEXT,
        station_name   TEXT,
        arrival        TEXT,
        departure      TEXT,
        day            INT
    );

    CREATE INDEX IF NOT EXISTS idx_schedules_station ON schedules(station_code);
    CREATE INDEX IF NOT EXISTS idx_schedules_train   ON schedules(train_number);
    CREATE INDEX IF NOT EXISTS idx_trains_from       ON trains(from_station_code);
    CREATE INDEX IF NOT EXISTS idx_trains_to         ON trains(to_station_code);
"""

import json
import os
import time
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Railway Data Loader", page_icon="🚆", layout="wide")

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR   = "data"
BATCH_SIZE = 500

st.title("🚆 Indian Railways — Supabase Data Loader")
st.caption("One-time setup. Run each table load once, then switch back to train_schedule.py.")
st.divider()

sched_files = sorted([
    f for f in os.listdir(DATA_DIR)
    if f.startswith("schedules_") and f.endswith(".json")
]) if os.path.exists(DATA_DIR) else []

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("stations.json",    "✅ Found" if os.path.exists(f"{DATA_DIR}/stations.json") else "❌ Missing")
with col2:
    st.metric("trains.json",      "✅ Found" if os.path.exists(f"{DATA_DIR}/trains.json")   else "❌ Missing")
with col3:
    st.metric("schedules chunks", f"✅ {len(sched_files)} found" if sched_files else "❌ Missing")

st.divider()

def batch_insert(table, records, progress_bar, status_text):
    total    = len(records)
    inserted = 0
    errors   = 0
    for i in range(0, total, BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        try:
            supabase.table(table).insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            errors += len(batch)
            status_text.warning(f"Batch error at {i}: {e}")
            time.sleep(1)
        pct = inserted / total
        progress_bar.progress(pct, text=f"{inserted:,} / {total:,} ({round(pct*100)}%)")
    return inserted, errors


# ── 1. Stations ────────────────────────────────────────────────────────────────
st.subheader("1 · Stations")
st.caption("8,990 stations — code, name, zone, state, lat/lon")

if st.button("Load Stations", type="primary"):
    path = f"{DATA_DIR}/stations.json"
    if not os.path.exists(path):
        st.error("stations.json not found in data/ folder.")
    else:
        with st.spinner("Reading..."):
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        records = []
        for feat in raw["features"]:
            props = feat.get("properties", {})
            geom  = feat.get("geometry")
            code  = props.get("code", "").strip()
            if not code:
                continue
            lat = lon = None
            if geom and geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if len(coords) == 2:
                    lon, lat = coords[0], coords[1]
            records.append({
                "station_code": code,
                "station_name": props.get("name", ""),
                "zone":         props.get("zone"),
                "state":        props.get("state"),
                "address":      props.get("address"),
                "latitude":     lat,
                "longitude":    lon,
            })
        pb  = st.progress(0, text="Starting...")
        txt = st.empty()
        t0  = time.time()
        ins, err = batch_insert("stations", records, pb, txt)
        st.success(f"✅ {ins:,} stations loaded in {round(time.time()-t0,1)}s — {err} errors")

st.divider()


# ── 2. Trains ──────────────────────────────────────────────────────────────────
st.subheader("2 · Trains")
st.caption("5,208 trains — type, classes, origin, destination, duration")

if st.button("Load Trains", type="primary"):
    path = f"{DATA_DIR}/trains.json"
    if not os.path.exists(path):
        st.error("trains.json not found in data/ folder.")
    else:
        with st.spinner("Reading..."):
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        records = []
        for feat in raw["features"]:
            p      = feat.get("properties", {})
            number = str(p.get("number", "")).strip()
            if not number:
                continue
            classes = []
            if p.get("first_ac"):    classes.append("1A")
            if p.get("second_ac"):   classes.append("2A")
            if p.get("third_ac"):    classes.append("3A")
            if p.get("sleeper"):     classes.append("SL")
            if p.get("chair_car"):   classes.append("CC")
            if p.get("first_class"): classes.append("FC")
            if not classes and p.get("classes"):
                classes = [c.strip() for c in p["classes"].split(",") if c.strip()]
            records.append({
                "train_number":      number,
                "train_name":        p.get("name", ""),
                "train_type":        p.get("type", ""),
                "from_station_code": p.get("from_station_code", ""),
                "from_station_name": p.get("from_station_name", ""),
                "to_station_code":   p.get("to_station_code", ""),
                "to_station_name":   p.get("to_station_name", ""),
                "departure":         p.get("departure", ""),
                "arrival":           p.get("arrival", ""),
                "duration_h":        p.get("duration_h", 0),
                "duration_m":        p.get("duration_m", 0),
                "distance_km":       p.get("distance", 0),
                "zone":              p.get("zone", ""),
                "classes":           ", ".join(classes) if classes else "",
                "return_train":      p.get("return_train", ""),
            })
        pb  = st.progress(0, text="Starting...")
        txt = st.empty()
        t0  = time.time()
        ins, err = batch_insert("trains", records, pb, txt)
        st.success(f"✅ {ins:,} trains loaded in {round(time.time()-t0,1)}s — {err} errors")

st.divider()


# ── 3. Schedules ───────────────────────────────────────────────────────────────
st.subheader("3 · Schedules")
st.caption(f"417,080 stop records across 3 chunks — found: {', '.join(sched_files) if sched_files else 'none'}")

if st.button("Load Schedules (all chunks)", type="primary"):
    if not sched_files:
        st.error("No schedules_*.json chunks found. Run split_schedules.py locally first.")
    else:
        total_ins = 0
        total_err = 0
        t0 = time.time()
        for chunk_file in sched_files:
            st.write(f"**{chunk_file}**")
            with st.spinner(f"Reading {chunk_file}..."):
                with open(os.path.join(DATA_DIR, chunk_file), "r", encoding="utf-8") as f:
                    raw = json.load(f)
            records = []
            for item in raw:
                train_no = str(item.get("train_number", "")).strip()
                stn_code = str(item.get("station_code", "")).strip()
                if not train_no or not stn_code:
                    continue
                arr = item.get("arrival",   "") or ""
                dep = item.get("departure", "") or ""
                arr = "" if arr in ("None", "null") else arr
                dep = "" if dep in ("None", "null") else dep
                records.append({
                    "id":           item.get("id"),
                    "train_number": train_no,
                    "train_name":   item.get("train_name", ""),
                    "station_code": stn_code,
                    "station_name": item.get("station_name", ""),
                    "arrival":      arr,
                    "departure":    dep,
                    "day":          item.get("day", 1),
                })
            pb  = st.progress(0, text="Starting...")
            txt = st.empty()
            ins, err = batch_insert("schedules", records, pb, txt)
            total_ins += ins
            total_err += err
            st.success(f"✅ {chunk_file} — {ins:,} records")

        elapsed = round(time.time() - t0, 1)
        st.balloons()
        st.success(f"🎉 All done — {total_ins:,} schedule records in {elapsed}s — {total_err} errors")

st.divider()
st.caption("Once all three are loaded, update your Streamlit Cloud app to point to train_schedule.py.")
