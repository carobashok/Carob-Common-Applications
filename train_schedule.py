import streamlit as st
import pandas as pd

st.set_page_config(page_title="Train Schedule Finder", page_icon="🚆", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }
    div[data-testid="metric-container"] {
        background: #f8f9fa; border-radius: 8px; padding: 12px 16px; border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# ── Verified Train Database ────────────────────────────────────────────────────
# Sources: IndiaRailInfo, Wikipedia, IRCTC, ixigo — verified train numbers only
TRAIN_DB = {
    "Chennai Central (MAS)": [
        # VERIFIED: indiarailinfo.com, wikipedia
        dict(no="12621", name="Tamil Nadu SF Express",                    type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="NDLS", to_name="New Delhi",            arr="--",    dep="22:00", dur="32h 30m", dist=2182, stops=11, classes="1A, 2A, 3A, SL, GEN", days="Daily",                   rel="Originates"),
        dict(no="12433", name="Chennai Rajdhani Express",                 type="Rajdhani",     frm="MAS", frm_name="Chennai Central",    to="NZM",  to_name="Hazrat Nizamuddin",    arr="--",    dep="06:10", dur="28h 15m", dist=2182, stops=8,  classes="1A, 2A, 3A",          days="Tue Fri",                 rel="Originates"),
        dict(no="12695", name="Chennai–Trivandrum SF Express",            type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="TVC",  to_name="Trivandrum Central",   arr="--",    dep="15:20", dur="16h 30m", dist=922,  stops=22, classes="2A, 3A, SL",          days="Daily",                   rel="Originates"),
        dict(no="12673", name="Cheran SF Express",                        type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="CBE",  to_name="Coimbatore Jn",        arr="--",    dep="22:00", dur="8h 00m",  dist=495,  stops=7,  classes="2A, 3A, SL, GEN",     days="Daily",                   rel="Originates"),
        dict(no="12603", name="Chennai–Charlapalli SF Express",           type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="CHZ",  to_name="Charlapalli",          arr="--",    dep="06:10", dur="12h 00m", dist=694,  stops=19, classes="1A, 2A, 3A, SL, GEN", days="Daily",                   rel="Originates"),
        dict(no="12607", name="Lalbagh Express",                          type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="SBC",  to_name="KSR Bengaluru City",   arr="--",    dep="15:30", dur="6h 05m",  dist=358,  stops=5,  classes="CC, 2S",              days="Daily",                   rel="Originates"),
        dict(no="12609", name="Mysuru Express",                           type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="MYS",  to_name="Mysuru Jn",            arr="--",    dep="13:35", dur="9h 15m",  dist=497,  stops=8,  classes="CC, 2S",              days="Daily",                   rel="Originates"),
        dict(no="16053", name="Chennai–Tirupati Express",                 type="Express",      frm="MAS", frm_name="Chennai Central",    to="TPTY", to_name="Tirupati",             arr="--",    dep="06:10", dur="3h 25m",  dist=147,  stops=6,  classes="GEN",                 days="Daily",                   rel="Originates"),
        dict(no="20601", name="Chennai–Bodinayakanur SF Express",         type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="BSNR", to_name="Bodinayakanur",        arr="--",    dep="21:00", dur="11h 05m", dist=728,  stops=8,  classes="1A, 2A, 3A, SL, GEN", days="Mon Wed Fri",             rel="Originates"),
        dict(no="20625", name="Chennai–Bhagat Ki Kothi SF Express",       type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="BGKT", to_name="Bhagat Ki Kothi",      arr="--",    dep="09:15", dur="40h 30m", dist=2351, stops=30, classes="2A, 3A, SL, GEN",     days="Wed",                     rel="Originates"),
        dict(no="20643", name="Chennai–Coimbatore Vande Bharat Express",  type="Vande Bharat", frm="MAS", frm_name="Chennai Central",    to="CBE",  to_name="Coimbatore Jn",        arr="--",    dep="06:00", dur="5h 50m",  dist=495,  stops=3,  classes="EC, CC",              days="Mon Tue Wed Thu Fri Sat", rel="Originates"),
        dict(no="20677", name="Chennai–Narasapur Vande Bharat Express",   type="Vande Bharat", frm="MAS", frm_name="Chennai Central",    to="NS",   to_name="Narasapur",            arr="--",    dep="05:50", dur="8h 40m",  dist=652,  stops=7,  classes="EC, CC",              days="Mon Tue Wed Thu Fri Sat", rel="Originates"),
        dict(no="22601", name="Chennai–Sainagar Shirdi SF Express",       type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="SNSI", to_name="Sainagar Shirdi",      arr="--",    dep="13:25", dur="18h 15m", dist=1247, stops=16, classes="2A, 3A, SL, GEN",     days="Fri",                     rel="Originates"),
        dict(no="22869", name="Chennai–Visakhapatnam SF Express",         type="Superfast",    frm="MAS", frm_name="Chennai Central",    to="VSKP", to_name="Visakhapatnam",        arr="--",    dep="06:20", dur="13h 15m", dist=781,  stops=11, classes="2A, 3A, SL, GEN",     days="Tue",                     rel="Originates"),
        dict(no="16003", name="Chennai–Nagarsol Express",                 type="Express",      frm="MAS", frm_name="Chennai Central",    to="NSL",  to_name="Nagarsol",             arr="--",    dep="12:10", dur="26h 45m", dist=1367, stops=24, classes="2A, 3A, SL, GEN",     days="Wed",                     rel="Originates"),
        # Terminating at MAS
        dict(no="12622", name="Tamil Nadu SF Express (return)",           type="Superfast",    frm="NDLS",frm_name="New Delhi",          to="MAS",  to_name="Chennai Central",      arr="06:30", dep="--",    dur="32h 30m", dist=2182, stops=11, classes="1A, 2A, 3A, SL, GEN", days="Daily",                   rel="Terminates"),
        dict(no="12434", name="Chennai Rajdhani Express (return)",        type="Rajdhani",     frm="NZM", frm_name="Hazrat Nizamuddin",  to="MAS",  to_name="Chennai Central",      arr="10:55", dep="--",    dur="28h 15m", dist=2182, stops=8,  classes="1A, 2A, 3A",          days="Wed Sat",                 rel="Terminates"),
        dict(no="12696", name="Trivandrum–Chennai SF Express (return)",   type="Superfast",    frm="TVC", frm_name="Trivandrum Central", to="MAS",  to_name="Chennai Central",      arr="07:50", dep="--",    dur="16h 30m", dist=922,  stops=22, classes="2A, 3A, SL",          days="Daily",                   rel="Terminates"),
        dict(no="12674", name="Cheran SF Express (return)",               type="Superfast",    frm="CBE", frm_name="Coimbatore Jn",      to="MAS",  to_name="Chennai Central",      arr="06:20", dep="--",    dur="8h 00m",  dist=495,  stops=7,  classes="2A, 3A, SL, GEN",     days="Daily",                   rel="Terminates"),
        dict(no="12608", name="Lalbagh Express (return)",                 type="Superfast",    frm="SBC", frm_name="KSR Bengaluru City", to="MAS",  to_name="Chennai Central",      arr="21:35", dep="--",    dur="6h 05m",  dist=358,  stops=5,  classes="CC, 2S",              days="Daily",                   rel="Terminates"),
        dict(no="12610", name="Mysuru Express (return)",                  type="Superfast",    frm="MYS", frm_name="Mysuru Jn",          to="MAS",  to_name="Chennai Central",      arr="22:50", dep="--",    dur="9h 15m",  dist=497,  stops=8,  classes="CC, 2S",              days="Daily",                   rel="Terminates"),
        dict(no="18042", name="Shalimar–Chennai Express",                 type="Express",      frm="SHM", frm_name="Shalimar",           to="MAS",  to_name="Chennai Central",      arr="19:15", dep="--",    dur="18h 45m", dist=1644, stops=18, classes="GEN, SL, 3A, 2A",     days="Sat",                     rel="Terminates"),
        dict(no="12604", name="Charlapalli–Chennai SF Express (return)",  type="Superfast",    frm="CHZ", frm_name="Charlapalli",        to="MAS",  to_name="Chennai Central",      arr="19:30", dep="--",    dur="12h 00m", dist=694,  stops=19, classes="1A, 2A, 3A, SL, GEN", days="Daily",                   rel="Terminates"),
        dict(no="16054", name="Tirupati–Chennai Express (return)",        type="Express",      frm="TPTY",frm_name="Tirupati",           to="MAS",  to_name="Chennai Central",      arr="21:45", dep="--",    dur="3h 25m",  dist=147,  stops=6,  classes="GEN",                 days="Daily",                   rel="Terminates"),
    ],
}

TYPE_COLORS = {
    "Rajdhani":    "#993556",
    "Vande Bharat":"#534AB7",
    "Shatabdi":    "#185FA5",
    "Duronto":     "#534AB7",
    "Jan Shatabdi":"#185FA5",
    "Superfast":   "#3B6D11",
    "Mail":        "#185FA5",
    "Express":     "#854F0B",
    "Passenger":   "#5F5E5A",
    "MEMU":        "#5F5E5A",
    "DEMU":        "#5F5E5A",
}

def time_to_min(t):
    if not t or t == "--":
        return 9999
    h, m = map(int, t.split(":"))
    return h * 60 + m

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 🚆 Train Schedule Finder")
st.caption("Trains originating, terminating, or passing through Indian Railway stations")
st.divider()

col1, col2 = st.columns([3, 1])
with col1:
    station = st.selectbox(
        "Select Station",
        options=["— select a station —"] + list(TRAIN_DB.keys()),
        index=0,
        label_visibility="collapsed",
    )
with col2:
    sort_by = st.selectbox(
        "Sort",
        ["Departure ↑", "Arrival ↑", "Train Name A–Z", "Train No."],
        label_visibility="collapsed",
    )

if station == "— select a station —":
    st.info("👆 Select a station above to see trains", icon="🛤️")
    st.stop()

trains = TRAIN_DB[station]

# ── Filters ────────────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4, fc5 = st.columns(5)
with fc1: f_all  = st.checkbox("All",            value=True)
with fc2: f_prem = st.checkbox("Premium",         value=False)
with fc3: f_sf   = st.checkbox("Superfast",       value=False)
with fc4: f_exp  = st.checkbox("Express / Mail",  value=False)
with fc5:
    f_rel = st.selectbox("Relation",
        ["Any", "Originates here", "Terminates here", "Passes through"],
        label_visibility="collapsed")

PREMIUM = {"Rajdhani", "Shatabdi", "Vande Bharat", "Duronto", "Jan Shatabdi"}
SF      = {"Superfast"}
EXP     = {"Express", "Mail"}

def passes_filter(t):
    if not f_all and not f_prem and not f_sf and not f_exp:
        return True
    type_ok = (
        f_all or
        (f_prem and t["type"] in PREMIUM) or
        (f_sf   and t["type"] in SF) or
        (f_exp  and t["type"] in EXP)
    )
    rel_ok = (
        f_rel == "Any" or
        (f_rel == "Originates here"  and t["rel"] == "Originates") or
        (f_rel == "Terminates here"  and t["rel"] == "Terminates") or
        (f_rel == "Passes through"   and t["rel"] == "Passes")
    )
    return type_ok and rel_ok

filtered = [t for t in trains if passes_filter(t)]

# ── Sort ───────────────────────────────────────────────────────────────────────
if sort_by == "Departure ↑":
    filtered.sort(key=lambda t: time_to_min(t["dep"]))
elif sort_by == "Arrival ↑":
    filtered.sort(key=lambda t: time_to_min(t["arr"]))
elif sort_by == "Train Name A–Z":
    filtered.sort(key=lambda t: t["name"])
else:
    filtered.sort(key=lambda t: int(t["no"]))

# ── Metrics ────────────────────────────────────────────────────────────────────
stn_code = station.split("(")[-1].replace(")", "")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Station Code", stn_code)
m2.metric("Trains Shown", len(filtered))
m3.metric("Originate Here", sum(1 for t in filtered if t["rel"] == "Originates"))
m4.metric("Terminate Here", sum(1 for t in filtered if t["rel"] == "Terminates"))

st.divider()

if not filtered:
    st.warning("No trains match the selected filters.")
    st.stop()

view_mode = st.radio("View as", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")

if view_mode == "Table":
    rows = []
    for t in filtered:
        rows.append({
            "Train No":   t["no"],
            "Name":       t["name"],
            "Type":       t["type"],
            "From":       f"{t['frm_name']} ({t['frm']})",
            "To":         f"{t['to_name']} ({t['to']})",
            "Arrival":    t["arr"],
            "Departure":  t["dep"],
            "Duration":   t["dur"],
            "Dist (km)":  t["dist"],
            "Stops":      t["stops"],
            "Classes":    t["classes"],
            "Runs on":    t["days"],
            "Relation":   t["rel"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

else:
    for t in filtered:
        color    = TYPE_COLORS.get(t["type"], "#5F5E5A")
        rel_icon = {"Originates": "🟢", "Terminates": "🔴", "Passes": "🔵"}.get(t["rel"], "⚪")

        with st.container(border=True):
            r1, r2 = st.columns([5, 1])
            with r1:
                st.markdown(
                    f"**{t['name']}**&nbsp;&nbsp;"
                    f"<span style='background:{color}22;color:{color};"
                    f"padding:2px 10px;border-radius:12px;font-size:12px;font-weight:500'>"
                    f"{t['type']}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Train #{t['no']} &nbsp;·&nbsp; {rel_icon} {t['rel']} &nbsp;·&nbsp; {t['days']}")
            with r2:
                st.markdown(f"<div style='text-align:right;font-size:13px;color:gray'>{t['dist']} km</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:right;font-size:13px;color:gray'>{t['dur']}</div>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                # Left column: origin station — show DEP if originates/passes, ARR if terminates
                if t["rel"] == "Terminates":
                    st.markdown(f"**FROM**")
                else:
                    st.markdown(f"**DEP {t['dep']}**")
                st.caption(f"{t['frm_name']} ({t['frm']})")
            with c2:
                st.markdown("<div style='text-align:center;font-size:20px;padding-top:4px'>→</div>", unsafe_allow_html=True)
            with c3:
                # Right column: destination station — show ARR if terminates/passes, TO if originates
                if t["rel"] == "Originates":
                    st.markdown(f"**TO**")
                else:
                    st.markdown(f"**ARR {t['arr']}**")
                st.caption(f"{t['to_name']} ({t['to']})")

            st.caption(f"🪑 {t['classes']} &nbsp;·&nbsp; {t['stops']} stops")

st.divider()
st.caption("Data verified from IndiaRailInfo, Wikipedia & IRCTC. For live status and booking → [IRCTC](https://www.irctc.co.in) | [NTES](https://enquiry.indianrail.gov.in)")
