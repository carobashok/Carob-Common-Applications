import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Train Schedule Finder", page_icon="🚆", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }
    div[data-testid="metric-container"] {
        background: #f8f9fa; border-radius: 8px; padding: 12px 16px; border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# ── Supabase client ────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = get_client()

# ── Load station list for dropdown (cached) ────────────────────────────────────
@st.cache_data(ttl=3600)
def load_stations():
    res = supabase.table("stations") \
        .select("station_code, station_name, zone, state") \
        .order("station_name") \
        .execute()
    return res.data  # list of dicts

@st.cache_data(ttl=3600)
def get_trains_at_station(station_code: str):
    """
    Get all schedule rows for a station, then enrich with train details.
    Returns a merged list of dicts.
    """
    # Step 1: all schedule rows for this station
    sched = supabase.table("schedules") \
        .select("train_number, train_name, arrival, departure, day") \
        .eq("station_code", station_code) \
        .execute().data

    if not sched:
        return []


    # Exclude local EMU/suburban trains by train number prefix
    # 4xxxx = EMU/MEMU suburban, 7xxxx = DEMU, 0xxxx = special/work trains
    LOCAL_PREFIXES = ("4", "7", "0")
    sched = [
        r for r in sched
        if not str(r["train_number"]).startswith(LOCAL_PREFIXES)
    ]

    if not sched:
        return []
    # Step 2: get train details for those train numbers
    train_nos = list({r["train_number"] for r in sched})

    # Supabase .in_() filter — fetch in one call
    trains_res = supabase.table("trains") \
        .select("train_number, train_name, train_type, from_station_code, from_station_name, to_station_code, to_station_name, departure, arrival, duration_h, duration_m, distance_km, classes") \
        .in_("train_number", train_nos) \
        .execute().data

    train_map = {t["train_number"]: t for t in trains_res}

    # Step 3: merge and determine relation
    merged = []
    for s in sched:
        t = train_map.get(s["train_number"], {})
        arr = s.get("arrival",   "") or ""
        dep = s.get("departure", "") or ""
        arr = "" if arr in ("None", "null", "none") else arr.replace(":00", "", 1) if arr.count(":") == 2 else arr
        dep = "" if dep in ("None", "null", "none") else dep.replace(":00", "", 1) if dep.count(":") == 2 else dep

        # Determine relation
        from_code = t.get("from_station_code", "")
        to_code   = t.get("to_station_code",   "")
        if from_code == station_code:
            rel = "Originates"
        elif to_code == station_code:
            rel = "Terminates"
        else:
            rel = "Passes"

        dur_h = t.get("duration_h", 0) or 0
        dur_m = t.get("duration_m", 0) or 0

        merged.append({
            "train_number":      s["train_number"],
            "train_name":        s.get("train_name") or t.get("train_name", ""),
            "train_type":        t.get("train_type", ""),
            "from_station_code": from_code,
            "from_station_name": t.get("from_station_name", ""),
            "to_station_code":   to_code,
            "to_station_name":   t.get("to_station_name", ""),
            "arrival":           arr,
            "departure":         dep,
            "duration":          f"{dur_h}h {dur_m:02d}m" if (dur_h or dur_m) else "",
            "distance_km":       t.get("distance_km", 0) or 0,
            "classes":           t.get("classes", "") or "",
            "relation":          rel,
        })

    return merged

@st.cache_data(ttl=3600)
def get_train_stops(train_number: str):
    """Get all intermediate stops for a train, ordered by id."""
    res = supabase.table("schedules") \
        .select("station_code, station_name, arrival, departure, day, id") \
        .eq("train_number", train_number) \
        .order("id") \
        .execute()
    return res.data

def fmt_time(t):
    """Strip seconds from HH:MM:SS → HH:MM."""
    if not t or t in ("None", "null", ""):
        return "--"
    parts = t.split(":")
    if len(parts) >= 2:
        return f"{parts[0]}:{parts[1]}"
    return t

TYPE_COLORS = {
    "RAJDHANI EXP": "#993556", "RAJDHANI":    "#993556",
    "VANDE BHART":  "#534AB7", "VANDE BHARAT":"#534AB7",
    "SHATABDI":     "#185FA5", "JAN SHATABDI":"#185FA5",
    "DURONTO":      "#534AB7", "HUMSAFAR":    "#534AB7",
    "SUPERFAST":    "#3B6D11", "SF EXPRESS":  "#3B6D11",
    "EXPRESS":      "#854F0B", "MAIL":        "#185FA5",
    "PASSENGER":    "#5F5E5A", "MEMU":        "#5F5E5A",
    "DEMU":         "#5F5E5A",
}

def type_color(t):
    return TYPE_COLORS.get(t.upper() if t else "", "#5F5E5A")

PREMIUM = {"RAJDHANI EXP","RAJDHANI","VANDE BHART","VANDE BHARAT",
           "SHATABDI","JAN SHATABDI","DURONTO","HUMSAFAR"}
SF_TYPES = {"SUPERFAST","SF EXPRESS"}
EX_TYPES = {"EXPRESS","MAIL"}

def time_to_min(t):
    if not t or t == "--":
        return 9999
    try:
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except:
        return 9999

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 🚆 Train Schedule Finder")
st.caption("Trains originating, terminating, or passing through any Indian Railway station")
st.divider()

# ── Load stations ──────────────────────────────────────────────────────────────
with st.spinner("Loading stations..."):
    all_stations = load_stations()

station_options = {
    f"{s['station_name']} ({s['station_code']})": s["station_code"]
    for s in all_stations
    if s.get("station_name") and s.get("station_code")
}

# ── Search bar ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    selected_label = st.selectbox(
        "Select Station",
        options=["— select a station —"] + list(station_options.keys()),
        index=0,
        label_visibility="collapsed",
    )
with col2:
    sort_by = st.selectbox(
        "Sort",
        ["Departure ↑", "Arrival ↑", "Train Name A–Z", "Train No."],
        label_visibility="collapsed",
    )

if selected_label == "— select a station —":
    st.info("👆 Select any station above — all 8,500+ Indian Railway stations are available", icon="🛤️")
    st.stop()

station_code = station_options[selected_label]

# ── Fetch trains ───────────────────────────────────────────────────────────────
with st.spinner(f"Fetching trains at {selected_label}..."):
    trains = get_trains_at_station(station_code)

if not trains:
    st.warning(f"No trains found for station code **{station_code}**.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4, fc5 = st.columns(5)
with fc1: f_all  = st.checkbox("All",           value=True)
with fc2: f_prem = st.checkbox("Premium",        value=False)
with fc3: f_sf   = st.checkbox("Superfast",      value=False)
with fc4: f_exp  = st.checkbox("Express / Mail", value=False)
with fc5:
    f_rel = st.selectbox("Relation",
        ["Any", "Originates here", "Terminates here", "Passes through"],
        label_visibility="collapsed")

def passes_filter(t):
    typ = (t.get("train_type") or "").upper()
    if not f_all and not f_prem and not f_sf and not f_exp:
        type_ok = True
    else:
        type_ok = (
            f_all or
            (f_prem and typ in PREMIUM) or
            (f_sf   and typ in SF_TYPES) or
            (f_exp  and typ in EX_TYPES)
        )
    rel_ok = (
        f_rel == "Any" or
        (f_rel == "Originates here"  and t["relation"] == "Originates") or
        (f_rel == "Terminates here"  and t["relation"] == "Terminates") or
        (f_rel == "Passes through"   and t["relation"] == "Passes")
    )
    return type_ok and rel_ok

filtered = [t for t in trains if passes_filter(t)]

# ── Sort ───────────────────────────────────────────────────────────────────────
if sort_by == "Departure ↑":
    filtered.sort(key=lambda t: time_to_min(t["departure"]))
elif sort_by == "Arrival ↑":
    filtered.sort(key=lambda t: time_to_min(t["arrival"]))
elif sort_by == "Train Name A–Z":
    filtered.sort(key=lambda t: t["train_name"])
else:
    filtered.sort(key=lambda t: t["train_number"])

# ── Metrics ────────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Station Code",   station_code)
m2.metric("Trains Shown",   len(filtered))
m3.metric("Originate Here", sum(1 for t in filtered if t["relation"] == "Originates"))
m4.metric("Terminate Here", sum(1 for t in filtered if t["relation"] == "Terminates"))

st.divider()

if not filtered:
    st.warning("No trains match the selected filters.")
    st.stop()

# ── View toggle ────────────────────────────────────────────────────────────────
view_mode = st.radio("View as", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")

# ── Table view ─────────────────────────────────────────────────────────────────
if view_mode == "Table":
    rows = []
    for t in filtered:
        rows.append({
            "Train No":  t["train_number"],
            "Name":      t["train_name"],
            "Type":      t["train_type"],
            "From":      f"{t['from_station_name']} ({t['from_station_code']})",
            "To":        f"{t['to_station_name']} ({t['to_station_code']})",
            "Arrival":   fmt_time(t["arrival"]),
            "Departure": fmt_time(t["departure"]),
            "Duration":  t["duration"],
            "Dist (km)": t["distance_km"],
            "Classes":   t["classes"],
            "Relation":  t["relation"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Card view ──────────────────────────────────────────────────────────────────
else:
    for t in filtered:
        color    = type_color(t["train_type"])
        rel_icon = {"Originates": "🟢", "Terminates": "🔴", "Passes": "🔵"}.get(t["relation"], "⚪")
        arr      = fmt_time(t["arrival"])
        dep      = fmt_time(t["departure"])

        with st.container(border=True):
            r1, r2 = st.columns([5, 1])
            with r1:
                st.markdown(
                    f"**{t['train_name']}**&nbsp;&nbsp;"
                    f"<span style='background:{color}22;color:{color};"
                    f"padding:2px 10px;border-radius:12px;font-size:12px;font-weight:500'>"
                    f"{t['train_type']}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Train #{t['train_number']} &nbsp;·&nbsp; {rel_icon} {t['relation']}")
            with r2:
                if t["distance_km"]:
                    st.markdown(f"<div style='text-align:right;font-size:13px;color:gray'>{t['distance_km']} km</div>", unsafe_allow_html=True)
                if t["duration"]:
                    st.markdown(f"<div style='text-align:right;font-size:13px;color:gray'>{t['duration']}</div>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                lbl  = "ARR" if t["relation"] == "Terminates" else "DEP"
                time = arr   if t["relation"] == "Terminates" else dep
                st.markdown(f"**{lbl} {time}**")
                st.caption(f"{t['from_station_name']} ({t['from_station_code']})")
            with c2:
                st.markdown("<div style='text-align:center;font-size:20px;padding-top:4px'>→</div>", unsafe_allow_html=True)
            with c3:
                lbl2  = "ARR" if t["relation"] != "Originates" else "TO"
                time2 = arr  if t["relation"] != "Originates" else ""
                st.markdown(f"**{lbl2} {time2}**" if time2 else f"**{lbl2}**")
                st.caption(f"{t['to_station_name']} ({t['to_station_code']})")

            if t["classes"]:
                st.caption(f"🪑 {t['classes']}")

            # Expandable stops
            with st.expander("View intermediate stops"):
                stops = get_train_stops(t["train_number"])
                if stops:
                    stop_rows = []
                    for i, s in enumerate(stops, start=1):
                        stop_rows.append({
                            "Stop #":    i,
                            "Station":   s.get("station_name", ""),
                            "Code":      s.get("station_code", ""),
                            "Arrival":   fmt_time(s.get("arrival",   "")),
                            "Departure": fmt_time(s.get("departure", "")),
                            "Day":       s.get("day", 1),
                        })
                    st.dataframe(pd.DataFrame(stop_rows), use_container_width=True, hide_index=True)
                else:
                    st.caption("No stop data available.")

st.divider()
st.caption("Data source: Indian Railways open dataset. For live status → [NTES](https://enquiry.indianrail.gov.in) | Booking → [IRCTC](https://www.irctc.co.in)")
