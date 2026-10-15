import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from importlib.metadata import version as _pkg_version
from pathlib import Path

st.set_page_config(page_title="IPL · Analytics Suite", page_icon="🏏", layout="wide",
                   initial_sidebar_state="expanded")

# ───────────────────────────── Design tokens ─────────────────────────────
GOLD, GOLD_L, GOLD_D = "#C9A24B", "#E8CF8E", "#8A6D2B"
IVORY, MUTED, BG = "#F3EEE2", "#8E887A", "#07070A"
TEAL, RUST = "#5F9EA0", "#B5654A"
GOLD_SCALE = ["#14110A", "#4A3A17", GOLD_D, GOLD, GOLD_L]
DIVERGING = [RUST, "#2A1D17", "#15130E", "#3B3216", GOLD]
TREEMAP_SCALE = ["#9C4F3A", "#6E5A2A", "#2F7F86"]
REGION_COLORS = {"India": GOLD, "UAE": IVORY, "South Africa": TEAL, "Other": MUTED}


def _ver(pkg):
    try:
        return tuple(int(x) for x in _pkg_version(pkg).split(".")[:2])
    except Exception:
        return (0, 0)


# Newer Streamlit replaced use_container_width with width="stretch".
FILL = {"width": "stretch"} if _ver("streamlit") >= (1, 50) else {"use_container_width": True}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', 'Segoe UI', sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 85% -10%, #1a1508 0%, #07070A 55%); color:#F3EEE2; }
#MainMenu, footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.6rem; padding-bottom:3rem; max-width:1500px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0C0B08 0%,#0A0A0E 100%); border-right:1px solid #26221A; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color:#CFC8B6; }
.brand { padding:6px 0 18px 0; border-bottom:1px solid #26221A; margin-bottom:18px; }
.brand .mark { font-family:'Cormorant Garamond',serif; font-size:40px; font-weight:700; letter-spacing:6px;
  background:linear-gradient(90deg,#E8CF8E,#C9A24B 60%,#8A6D2B); -webkit-background-clip:text; -webkit-text-fill-color:transparent; line-height:1; }
.brand .sub { color:#8E887A; font-size:10.5px; letter-spacing:4px; margin-top:6px; }
.navlabel { color:#8A6D2B; font-size:10.5px; letter-spacing:3px; margin:6px 0 4px 0; }
.hero { margin-bottom:1.2rem; padding-bottom:1rem; border-bottom:1px solid #26221A; }
.eyebrow { color:#C9A24B; font-size:11px; letter-spacing:5px; font-weight:600; }
.hero h1 { font-family:'Cormorant Garamond',serif; font-weight:600; font-size:46px; margin:4px 0 2px 0; color:#F3EEE2; letter-spacing:.5px; }
.hero p { color:#8E887A; font-size:13.5px; margin:0; }
.kpi { position:relative; background:linear-gradient(160deg,#121217,#0B0B0F); border:1px solid #26221A; border-radius:14px;
  padding:18px 20px 16px 20px; min-height:112px; box-shadow:0 10px 30px rgba(0,0,0,.35); overflow:hidden; }
.kpi:before { content:''; position:absolute; left:0; top:0; right:0; height:2px; background:linear-gradient(90deg,#C9A24B,rgba(201,162,75,0)); }
.kl { color:#8E887A; font-size:10.5px; letter-spacing:2.6px; font-weight:600; }
.kv { font-family:'Cormorant Garamond',serif; font-size:38px; font-weight:600; color:#F3EEE2; line-height:1.15; margin-top:6px; }
.kv.small { font-size:23px; line-height:1.5; padding-top:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.kn { color:#C9A24B; font-size:12px; margin-top:2px; }
[data-testid="stVerticalBlockBorderWrapper"] { background:linear-gradient(160deg,#101015,#0B0B0F);
  border:1px solid #26221A !important; border-radius:14px; box-shadow:0 10px 30px rgba(0,0,0,.35); }
.sec { display:flex; align-items:baseline; gap:12px; margin:2px 0 6px 0; }
.sec h3 { font-family:'Cormorant Garamond',serif; font-weight:600; font-size:23px; color:#F3EEE2 !important; margin:0; padding:0; }
.sec span { color:#8E887A; font-size:12px; }
.insight { border-left:2px solid #C9A24B; padding:4px 0 4px 14px; color:#CFC8B6; font-size:13.5px; line-height:1.5; }
.insight b { color:#E8CF8E; font-weight:600; }
.divider { height:1px; background:linear-gradient(90deg,#26221A,rgba(38,34,26,0)); margin:6px 0 14px 0; }
div[data-baseweb="select"] > div, .stTextInput input { background:#0F0F14 !important; border-color:#26221A !important; }
[data-testid="stDataFrame"] { border:1px solid #26221A; border-radius:10px; overflow:hidden; }
.stDownloadButton button { background:transparent; border:1px solid #C9A24B; color:#E8CF8E; border-radius:8px; }
.stDownloadButton button:hover { background:#C9A24B; color:#07070A; border-color:#C9A24B; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────── Reference data ─────────────────────────────
TEAM_META = {
    "Chennai Super Kings": ("CSK", "#F2C230"), "Mumbai Indians": ("MI", "#2E6FD8"),
    "Royal Challengers Bangalore": ("RCB", "#C8323B"), "Kolkata Knight Riders": ("KKR", "#7A4FBF"),
    "Sunrisers Hyderabad": ("SRH", "#F2812E"), "Rajasthan Royals": ("RR", "#E2569B"),
    "Delhi Capitals": ("DC", "#5CC8F2"), "Punjab Kings": ("PBKS", "#E8503A"),
    "Gujarat Titans": ("GT", "#8AA0C4"), "Lucknow Super Giants": ("LSG", "#35C5C0"),
    "Gujarat Lions": ("GL", "#E5742C"), "Rising Pune Supergiant": ("RPS", "#9C6FD6"),
    "Pune Warriors": ("PWI", "#3D9A8B"), "Kochi Tuskers Kerala": ("KTK", "#D98FBF"),
    "Deccan Chargers": ("DCH", "#9AA4B2"),
}
TEAM_ALIAS = {"Rising Pune Supergiants": "Rising Pune Supergiant"}
TEAM_COLORS = {k: v[1] for k, v in TEAM_META.items()}

# keyword in raw venue name -> (clean ground name, city, region). Order matters.
GROUND_RULES = [
    ("chinnaswamy", "M Chinnaswamy Stadium", "Bengaluru", "India"),
    ("chidambaram", "MA Chidambaram Stadium", "Chennai", "India"),
    ("wankhede", "Wankhede Stadium", "Mumbai", "India"),
    ("eden gardens", "Eden Gardens", "Kolkata", "India"),
    ("arun jaitley", "Arun Jaitley Stadium", "Delhi", "India"),
    ("feroz shah", "Arun Jaitley Stadium", "Delhi", "India"),
    ("rajiv gandhi", "Rajiv Gandhi Intl Stadium", "Hyderabad", "India"),
    ("sawai mansingh", "Sawai Mansingh Stadium", "Jaipur", "India"),
    ("narendra modi", "Narendra Modi Stadium", "Ahmedabad", "India"),
    ("motera", "Narendra Modi Stadium", "Ahmedabad", "India"),
    ("maharaja yadavindra", "Maharaja Yadavindra Singh Stadium", "Mullanpur", "India"),
    ("bindra", "PCA IS Bindra Stadium", "Mohali", "India"),
    ("punjab cricket", "PCA IS Bindra Stadium", "Mohali", "India"),
    ("maharashtra cricket", "MCA Stadium", "Pune", "India"),
    ("subrata roy", "MCA Stadium", "Pune", "India"),
    ("brabourne", "Brabourne Stadium", "Mumbai", "India"),
    ("dy patil", "DY Patil Stadium", "Navi Mumbai", "India"),
    ("ekana", "Ekana Cricket Stadium", "Lucknow", "India"),
    ("barsapara", "Barsapara Stadium", "Guwahati", "India"),
    ("barabati", "Barabati Stadium", "Cuttack", "India"),
    ("himachal", "HPCA Stadium", "Dharamsala", "India"),
    ("holkar", "Holkar Cricket Stadium", "Indore", "India"),
    ("jsca", "JSCA Stadium", "Ranchi", "India"),
    ("saurashtra", "Saurashtra Cricket Stadium", "Rajkot", "India"),
    ("green park", "Green Park", "Kanpur", "India"),
    ("nehru stadium", "Nehru Stadium", "Kochi", "India"),
    ("shaheed veer", "Shaheed Veer Narayan Singh Stadium", "Raipur", "India"),
    ("vidarbha", "VCA Stadium, Jamtha", "Nagpur", "India"),
    ("rajasekhara", "ACA-VDCA Stadium", "Visakhapatnam", "India"),
    ("dubai", "Dubai International Stadium", "Dubai", "UAE"),
    ("sharjah", "Sharjah Cricket Stadium", "Sharjah", "UAE"),
    ("zayed", "Sheikh Zayed Stadium", "Abu Dhabi", "UAE"),
    ("kingsmead", "Kingsmead", "Durban", "South Africa"),
    ("supersport", "SuperSport Park", "Centurion", "South Africa"),
    ("wanderers", "New Wanderers Stadium", "Johannesburg", "South Africa"),
    ("newlands", "Newlands", "Cape Town", "South Africa"),
    ("george's park", "St George's Park", "Gqeberha", "South Africa"),
    ("buffalo park", "Buffalo Park", "East London", "South Africa"),
    ("de beers", "De Beers Diamond Oval", "Kimberley", "South Africa"),
    ("outsurance", "OUTsurance Oval", "Bloemfontein", "South Africa"),
]


def canon_ground(raw):
    s = str(raw).lower()
    for key, name, city, region in GROUND_RULES:
        if key in s:
            return name, city, region
    return str(raw).split(",")[0].strip(), "Unknown", "Other"


def _find(name):
    base = Path(__file__).parent
    for p in (base / name, base / "data" / name):
        if p.exists():
            return p
    raise FileNotFoundError(f"{name} not found next to app.py (or in ./data)")


@st.cache_data(show_spinner=False)
def load_data():
    teams = pd.read_csv(_find("teams.csv"))
    venues = pd.read_csv(_find("venues.csv"))
    m = pd.read_csv(_find("matches.csv"))

    # Teams: resolve names through teams.csv ids, then unify franchise spellings.
    id2name = dict(zip(teams["team_id"].astype(int), teams["team_name"].astype(str).str.strip()))
    for col, idc in [("team1", "team1_id"), ("team2", "team2_id"),
                     ("toss_winner", "toss_winner_id"), ("match_winner", "match_winner_id")]:
        mapped = m[idc].astype("Int64").map(id2name)
        m[col] = mapped.where(mapped.notna(), m[col]).fillna("").astype(str).str.strip().replace(TEAM_ALIAS)

    # Venues: collapse spelling variants into one ground; city/region come from the mapping.
    info = m["venue"].fillna("").map(canon_ground)
    m["ground"] = info.map(lambda x: x[0])
    m["city_clean"] = info.map(lambda x: x[1])
    m["region"] = info.map(lambda x: x[2])

    m["date"] = pd.to_datetime(m["match_date"], errors="coerce")
    m["season_year"] = m["season"].astype(str).str[:4].astype(int)
    m["result"] = m["result"].fillna("").astype(str).str.strip()
    m["player_of_match"] = m["player_of_match"].fillna("").astype(str)

    other = np.where(m["toss_winner"] == m["team1"], m["team2"], m["team1"])
    m["bat_first"] = np.where(m["toss_decision"] == "bat", m["toss_winner"], other)
    m["decided"] = m["result"].eq("win") & m["match_winner"].ne("")
    m["bat_first_won"] = m["decided"] & (m["match_winner"] == m["bat_first"])
    m["toss_won_match"] = m["decided"] & (m["toss_winner"] == m["match_winner"])

    def method(r):
        if r.result == "tie":
            return "Tie · Super Over"
        if r.result == "no result":
            return "No result"
        if pd.notna(r.win_by_runs):
            return "Won by runs"
        if pd.notna(r.win_by_wickets):
            return "Won by wickets"
        return "Other"

    m["method"] = m.apply(method, axis=1)
    m["margin"] = np.where(m["win_by_runs"].notna(), m["win_by_runs"].fillna(0).astype(int).astype(str) + " runs",
                  np.where(m["win_by_wickets"].notna(), m["win_by_wickets"].fillna(0).astype(int).astype(str) + " wkts", "—"))
    return teams, venues, m


teams_df, venues_df, M = load_data()


# ───────────────────────────── Helpers ─────────────────────────────
def pct(a, b):
    return float(a) / float(b) * 100 if b else np.nan


def fmt_pct(x):
    return "—" if pd.isna(x) else f"{x:.1f}%"


def team_long(df):
    a = df.assign(team=df["team1"], opp=df["team2"])
    b = df.assign(team=df["team2"], opp=df["team1"])
    L = pd.concat([a, b], ignore_index=True)
    L["won"] = L["decided"] & (L["match_winner"] == L["team"])
    L["lost"] = L["decided"] & (L["match_winner"] != L["team"])
    L["batted_first"] = L["bat_first"] == L["team"]
    L["toss_won"] = L["toss_winner"] == L["team"]
    return L


def team_table(L):
    if L.empty:
        return pd.DataFrame(columns=["team", "played", "wins", "losses", "win_pct", "bf_win_pct", "chase_win_pct", "toss_pct"])
    g = L.groupby("team")
    t = g.agg(played=("won", "size"), wins=("won", "sum"), losses=("lost", "sum"), toss_won=("toss_won", "sum")).reset_index()
    dec = L[L["won"] | L["lost"]]
    bf = dec[dec["batted_first"]].groupby("team").agg(bf_w=("won", "sum"), bf_n=("won", "size")).reset_index()
    ch = dec[~dec["batted_first"]].groupby("team").agg(ch_w=("won", "sum"), ch_n=("won", "size")).reset_index()
    t = t.merge(bf, on="team", how="left").merge(ch, on="team", how="left")
    for c in ["bf_w", "bf_n", "ch_w", "ch_n"]:
        t[c] = t[c].fillna(0)
    t["win_pct"] = (t["wins"] / (t["wins"] + t["losses"]).replace(0, np.nan) * 100).round(1)
    t["bf_win_pct"] = (t["bf_w"] / t["bf_n"].replace(0, np.nan) * 100).round(1)
    t["chase_win_pct"] = (t["ch_w"] / t["ch_n"].replace(0, np.nan) * 100).round(1)
    t["toss_pct"] = (t["toss_won"] / t["played"] * 100).round(1)
    return t.sort_values(["wins", "win_pct"], ascending=False).reset_index(drop=True)


def ground_table(df):
    g = df.groupby(["ground", "city_clean", "region"]).agg(
        matches=("match_id", "size"), decided=("decided", "sum"), bf_wins=("bat_first_won", "sum"),
        toss_field=("toss_decision", lambda s: (s == "field").mean() * 100)).reset_index()
    g["bf_pct"] = (g["bf_wins"] / g["decided"].replace(0, np.nan) * 100).round(1)
    g["chase_pct"] = (100 - g["bf_pct"]).round(1)
    g["toss_field"] = g["toss_field"].round(1)
    best = (df[df["decided"]].groupby(["ground", "match_winner"]).size().reset_index(name="w")
            .sort_values(["ground", "w"]).drop_duplicates("ground", keep="last"))
    g = g.merge(best.rename(columns={"match_winner": "top_team", "w": "top_wins"}), on="ground", how="left")
    return g.sort_values("matches", ascending=False).reset_index(drop=True)


def section(title, sub=""):
    st.markdown(f'<div class="sec"><h3>{title}</h3><span>{sub}</span></div>', unsafe_allow_html=True)


def hero(eyebrow, title, sub):
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{sub}</p></div>',
                unsafe_allow_html=True)


def kpis(items):
    for col, (label, value, note, small) in zip(st.columns(len(items)), items):
        cls = "kv small" if small else "kv"
        col.markdown(f'<div class="kpi"><div class="kl">{label}</div><div class="{cls}">{value}</div>'
                     f'<div class="kn">{note}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)


def base(fig, h=340, legend=True):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#CFC8B6", size=12),
        margin=dict(l=8, r=12, t=34 if legend else 12, b=8), showlegend=legend,
        legend=dict(orientation="h", y=1.14, x=0, title=None, font=dict(size=11)),
        hoverlabel=dict(bgcolor="#15130E", bordercolor=GOLD, font=dict(color=IVORY)),
        colorway=[GOLD, IVORY, TEAL, RUST, GOLD_D])
    fig.update_xaxes(gridcolor="#1A1812", zerolinecolor="#26221A", linecolor="#26221A", automargin=True, title=None)
    fig.update_yaxes(gridcolor="#1A1812", zerolinecolor="#26221A", linecolor="#26221A", automargin=True, title=None)
    return fig


def show(fig):
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False}, **FILL)


def empty_note(msg="No data for the current filters."):
    st.info(msg)


# ───────────────────────────── Sidebar ─────────────────────────────
st.sidebar.markdown('<div class="brand"><div class="mark">IPL</div><div class="sub">ANALYTICS SUITE</div></div>',
                    unsafe_allow_html=True)
st.sidebar.markdown('<div class="navlabel">NAVIGATE</div>', unsafe_allow_html=True)
PAGES = ["Executive Overview", "Franchise Intelligence", "Venue Intelligence", "Franchise × Venue", "Match Ledger"]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

st.sidebar.markdown('<div class="navlabel" style="margin-top:22px">FILTERS</div>', unsafe_allow_html=True)
years = sorted(M["season_year"].unique().tolist())
yr = st.sidebar.select_slider("Seasons", options=years, value=(years[0], years[-1]))
all_regions = sorted(M["region"].unique().tolist())
regions = st.sidebar.multiselect("Region", all_regions, default=all_regions)
all_teams = sorted(set(M["team1"]) | set(M["team2"]))
teams_sel = st.sidebar.multiselect("Franchises", all_teams, default=[], placeholder="All franchises")

F = M[(M["season_year"].between(*yr)) & (M["region"].isin(regions))]
if teams_sel:
    F = F[F["team1"].isin(teams_sel) | F["team2"].isin(teams_sel)]

st.sidebar.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
st.sidebar.caption(
    f"**{len(F):,}** of {len(M):,} matches in view  \n"
    f"{M['ground'].nunique()} grounds · {venues_df.shape[0]} raw venue records  \n"
    f"Data through {M['date'].max():%d %b %Y}")

if F.empty:
    hero("INDIAN PREMIER LEAGUE", page, "No matches fit the selected filters.")
    empty_note("Widen the season range, region or franchise selection in the sidebar.")
    st.stop()

L_all = team_long(F)
L = L_all[L_all["team"].isin(teams_sel)] if teams_sel else L_all
TT = team_table(L)
span = f"{yr[0]} – {yr[1]}" if yr[0] != yr[1] else f"{yr[0]}"
sub_line = f"{len(F):,} matches · {F['ground'].nunique()} grounds · {len(set(F['team1']) | set(F['team2']))} franchises · seasons {span}"

# ═════════════════════════ PAGE 1 · OVERVIEW ═════════════════════════
if page == "Executive Overview":
    hero(f"INDIAN PREMIER LEAGUE · {span}", "Executive Overview", sub_line)
    dec = F[F["decided"]]
    bf_pct = pct(dec["bat_first_won"].sum(), len(dec))
    toss_edge = pct(dec["toss_won_match"].sum(), len(dec))
    kpis([
        ("MATCHES", f"{len(F):,}", f"{F['season_year'].nunique()} seasons", False),
        ("FRANCHISES", f"{len(set(F['team1']) | set(F['team2']))}", "Competing sides", False),
        ("GROUNDS", f"{F['ground'].nunique()}", f"{F['city_clean'].nunique()} cities · {F['region'].nunique()} regions", False),
        ("CHASE WIN RATE", fmt_pct(100 - bf_pct), f"Bat-first wins {fmt_pct(bf_pct)}", False),
        ("TOSS → VICTORY", fmt_pct(toss_edge), "Toss winners who won", False),
    ])

    # Auto-generated insights
    top = TT.iloc[0] if len(TT) else None
    qual = TT[TT["played"] >= 30].sort_values("win_pct", ascending=False)
    busiest = F["ground"].value_counts()
    field_share = pct((F["toss_decision"] == "field").sum(), len(F))
    ins = st.columns(4)
    texts = [
        f"<b>{top['team']}</b> lead the table with <b>{int(top['wins'])}</b> wins from {int(top['played'])} matches." if top is not None else "—",
        f"<b>{qual.iloc[0]['team']}</b> post the best win rate (<b>{qual.iloc[0]['win_pct']:.1f}%</b>, min. 30 matches)." if len(qual) else "Not enough matches for a win-rate leader.",
        f"<b>{busiest.index[0]}</b> hosted the most games — <b>{int(busiest.iloc[0])}</b> matches.",
        f"Captains chose to <b>field first in {field_share:.0f}%</b> of toss decisions.",
    ]
    for c, t in zip(ins, texts):
        c.markdown(f'<div class="insight">{t}</div>', unsafe_allow_html=True)
    st.markdown('<div class="divider" style="margin-top:14px"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.15, 1])
    with c1, st.container(border=True):
        section("Matches per season", "stacked by region")
        s = F.groupby(["season_year", "region"]).size().reset_index(name="matches")
        fig = px.bar(s, x="season_year", y="matches", color="region", color_discrete_map=REGION_COLORS)
        fig.update_xaxes(dtick=1, tickangle=-45)
        fig.update_traces(marker_line_width=0)
        show(base(fig, 340))
    with c2, st.container(border=True):
        section("Bat first vs chase", "win share by season")
        d = F[F["decided"]].groupby("season_year").agg(n=("bat_first_won", "size"), bf=("bat_first_won", "sum")).reset_index()
        d["Bat first"] = d["bf"] / d["n"] * 100
        d["Chase"] = 100 - d["Bat first"]
        dl = d.melt(id_vars="season_year", value_vars=["Bat first", "Chase"], var_name="Strategy", value_name="Win %")
        fig = px.line(dl, x="season_year", y="Win %", color="Strategy", markers=True,
                      color_discrete_map={"Bat first": IVORY, "Chase": GOLD})
        fig.add_hline(y=50, line_dash="dot", line_color=MUTED)
        fig.update_yaxes(range=[20, 80], ticksuffix="%")
        fig.update_xaxes(dtick=2)
        show(base(fig, 340))

    c3, c4 = st.columns(2)
    with c3, st.container(border=True):
        section("Busiest grounds", "top 10 by matches hosted")
        g = F.groupby("ground").size().nlargest(10).sort_values().reset_index(name="matches")
        fig = go.Figure(go.Bar(x=g["matches"], y=g["ground"], orientation="h", marker_color=GOLD,
                               text=g["matches"], textposition="outside", cliponaxis=False,
                               textfont=dict(color=IVORY)))
        show(base(fig, 400, legend=False))
    with c4, st.container(border=True):
        section("Franchise wins", "top 10 · colour = franchise")
        t = TT.head(10).sort_values("wins")
        fig = go.Figure(go.Bar(x=t["wins"], y=t["team"], orientation="h",
                               marker_color=[TEAM_COLORS.get(x, MUTED) for x in t["team"]],
                               text=t["wins"].astype(int), textposition="outside", cliponaxis=False,
                               textfont=dict(color=IVORY),
                               customdata=np.c_[t["played"], t["win_pct"]],
                               hovertemplate="%{y}<br>Wins %{x} · Played %{customdata[0]} · Win %{customdata[1]}%<extra></extra>"))
        show(base(fig, 400, legend=False))

    c5, c6, c7 = st.columns([1, 1, 1.1])
    with c5, st.container(border=True):
        section("Toss decisions", "share electing to bat or field")
        td = F.groupby(["season_year", "toss_decision"]).size().reset_index(name="n")
        td["toss_decision"] = td["toss_decision"].map({"field": "Field", "bat": "Bat"})
        fig = px.bar(td, x="season_year", y="n", color="toss_decision",
                     color_discrete_map={"Field": GOLD, "Bat": IVORY})
        fig.update_layout(barmode="stack", barnorm="percent")
        fig.update_xaxes(dtick=2)
        fig.update_yaxes(ticksuffix="%")
        show(base(fig, 330))
    with c6, st.container(border=True):
        section("How matches are decided", "result mix")
        mm = F["method"].value_counts().reset_index()
        mm.columns = ["method", "n"]
        fig = go.Figure(go.Pie(labels=mm["method"], values=mm["n"], hole=0.62, sort=False,
                               marker=dict(colors=[GOLD, IVORY, TEAL, RUST, MUTED][:len(mm)], line=dict(color=BG, width=2)),
                               textinfo="percent", textfont=dict(color=BG, size=12)))
        show(base(fig, 330))
    with c7, st.container(border=True):
        section("Player of the Match", "most awards")
        p = F[F["player_of_match"] != ""]["player_of_match"].value_counts().head(8).sort_values().reset_index()
        p.columns = ["player", "awards"]
        fig = go.Figure(go.Bar(x=p["awards"], y=p["player"], orientation="h", marker_color=GOLD_L,
                               text=p["awards"], textposition="outside", cliponaxis=False, textfont=dict(color=IVORY)))
        show(base(fig, 330, legend=False))

# ═════════════════════════ PAGE 2 · FRANCHISES ═════════════════════════
elif page == "Franchise Intelligence":
    hero("TEAMS × MATCHES", "Franchise Intelligence", sub_line)
    if TT.empty:
        empty_note()
        st.stop()
    best = TT[TT["played"] >= 20].sort_values("win_pct", ascending=False)
    kpis([
        ("FRANCHISES SHOWN", f"{len(TT)}", "After filters", False),
        ("MOST WINS", TT.iloc[0]["team"], f"{int(TT.iloc[0]['wins'])} wins", True),
        ("BEST WIN RATE", best.iloc[0]["team"] if len(best) else "—",
         f"{best.iloc[0]['win_pct']:.1f}% (min. 20 matches)" if len(best) else "Not enough matches", True),
        ("BEST CHASERS", (TT[TT["played"] >= 20].sort_values("chase_win_pct", ascending=False).iloc[0]["team"] if len(best) else "—"),
         "Highest win % when chasing", True),
    ])

    with st.container(border=True):
        section("League table", "wins, losses and tactical splits")
        tbl = TT.rename(columns={"team": "Franchise", "played": "Matches", "wins": "Wins", "losses": "Losses",
                                 "win_pct": "Win %", "bf_win_pct": "Bat-first win %", "chase_win_pct": "Chase win %",
                                 "toss_pct": "Toss win %"})[
            ["Franchise", "Matches", "Wins", "Losses", "Win %", "Bat-first win %", "Chase win %", "Toss win %"]]
        pc = lambda lbl: st.column_config.ProgressColumn(lbl, min_value=0, max_value=100, format="%.1f%%")
        st.dataframe(tbl, hide_index=True, height=min(520, 38 * (len(tbl) + 1) + 4),
                     column_config={"Win %": pc("Win %"), "Bat-first win %": pc("Bat-first win %"),
                                    "Chase win %": pc("Chase win %"), "Toss win %": pc("Toss win %")}, **FILL)

    c1, c2 = st.columns([1, 1.25])
    with c1, st.container(border=True):
        section("Win rate ranking", "decided matches only")
        min_m = st.slider("Minimum matches", 0, int(TT["played"].max()), min(20, int(TT["played"].max())), key="min_m")
        t = TT[TT["played"] >= min_m].sort_values("win_pct")
        if t.empty:
            empty_note("No franchise meets the minimum.")
        else:
            fig = go.Figure(go.Bar(x=t["win_pct"], y=t["team"], orientation="h",
                                   marker_color=[TEAM_COLORS.get(x, MUTED) for x in t["team"]],
                                   text=t["win_pct"].map(lambda v: f"{v:.1f}%"), textposition="outside",
                                   cliponaxis=False, textfont=dict(color=IVORY),
                                   customdata=t["played"], hovertemplate="%{y}<br>%{x:.1f}% · %{customdata} matches<extra></extra>"))
            fig.add_vline(x=50, line_dash="dot", line_color=MUTED)
            fig.update_xaxes(range=[0, max(75, t["win_pct"].max() + 8)], ticksuffix="%")
            show(base(fig, 120 + 30 * len(t), legend=False))
    with c2, st.container(border=True):
        section("Season-by-season form", "win % per franchise (min. 3 decided matches)")
        dd = L[L["won"] | L["lost"]].groupby(["team", "season_year"]).agg(w=("won", "sum"), n=("won", "size")).reset_index()
        dd = dd[dd["n"] >= 3]
        dd["p"] = dd["w"] / dd["n"] * 100
        if dd.empty:
            empty_note()
        else:
            pv = dd.pivot(index="team", columns="season_year", values="p").reindex(TT["team"].tolist())
            pv = pv.dropna(how="all")
            fig = go.Figure(go.Heatmap(
                z=pv.values, x=[str(c) for c in pv.columns], y=pv.index, colorscale=GOLD_SCALE, zmin=0, zmax=100,
                text=np.where(np.isnan(pv.values), "", np.round(pv.values).astype(str)) if pv.size else None,
                texttemplate="%{text}", textfont=dict(size=10, color=IVORY), xgap=2, ygap=2,
                hovertemplate="%{y} · %{x}<br>Win %{z:.0f}%<extra></extra>",
                colorbar=dict(title="Win %", thickness=10, len=0.8)))
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(tickangle=-45)
            show(base(fig, 120 + 30 * len(pv), legend=False))

    with st.container(border=True):
        section("Head-to-head", "row franchise's win rate against column franchise · cell text = wins–losses")
        dec = L_all[L_all["won"] | L_all["lost"]].copy()
        dec["w"] = dec["won"].astype(int)
        rows = TT["team"].tolist()
        cols = [t for t in team_table(L_all)["team"].tolist()]
        W = dec.pivot_table(index="team", columns="opp", values="w", aggfunc="sum", fill_value=0).reindex(index=rows, columns=cols, fill_value=0)
        N = dec.pivot_table(index="team", columns="opp", values="w", aggfunc="size", fill_value=0).reindex(index=rows, columns=cols, fill_value=0)
        Z = (W / N.replace(0, np.nan) * 100)
        txt = np.where(N.values > 0, W.values.astype(int).astype(str) + "–" + (N.values - W.values).astype(int).astype(str), "")
        fig = go.Figure(go.Heatmap(z=Z.values, x=cols, y=rows, text=txt, texttemplate="%{text}", zmid=50, zmin=0, zmax=100,
                                   colorscale=DIVERGING, xgap=2, ygap=2, textfont=dict(size=10, color=IVORY),
                                   hovertemplate="%{y} vs %{x}<br>Win %{z:.0f}%<extra></extra>",
                                   colorbar=dict(title="Win %", thickness=10, len=0.8)))
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(tickangle=-40, side="bottom")
        show(base(fig, 130 + 36 * len(rows), legend=False))

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    prof_opts = TT["team"].tolist()
    team = st.selectbox("Franchise profile", prof_opts, key="profile_team")
    Lt = L_all[L_all["team"] == team]
    tt1 = team_table(Lt).iloc[0]
    kpis([
        ("MATCHES", f"{int(tt1['played'])}", team, False),
        ("WINS / LOSSES", f"{int(tt1['wins'])} / {int(tt1['losses'])}", f"Win rate {fmt_pct(tt1['win_pct'])}", False),
        ("BATTING FIRST", fmt_pct(tt1["bf_win_pct"]), "Win rate setting a target", False),
        ("CHASING", fmt_pct(tt1["chase_win_pct"]), "Win rate chasing", False),
    ])
    p1, p2 = st.columns([1.3, 1])
    tcolor = TEAM_COLORS.get(team, GOLD)
    with p1, st.container(border=True):
        section(f"{team}", "wins and losses by season")
        ss = Lt.groupby("season_year").agg(Wins=("won", "sum"), Losses=("lost", "sum")).reset_index()
        fig = go.Figure()
        fig.add_bar(x=ss["season_year"], y=ss["Wins"], name="Wins", marker_color=tcolor)
        fig.add_bar(x=ss["season_year"], y=ss["Losses"], name="Losses", marker_color="#3A362B")
        fig.update_layout(barmode="stack")
        fig.update_xaxes(dtick=1, tickangle=-45)
        show(base(fig, 330))
    with p2, st.container(border=True):
        section("Where they win", "top grounds by matches played")
        gg = Lt.groupby("ground").agg(Played=("won", "size"), Won=("won", "sum")).reset_index().nlargest(8, "Played").sort_values("Played")
        fig = go.Figure()
        fig.add_bar(y=gg["ground"], x=gg["Played"], name="Played", orientation="h", marker_color="#3A362B")
        fig.add_bar(y=gg["ground"], x=gg["Won"], name="Won", orientation="h", marker_color=tcolor)
        fig.update_layout(barmode="overlay")
        show(base(fig, 330))

# ═════════════════════════ PAGE 3 · VENUES ═════════════════════════
elif page == "Venue Intelligence":
    hero("VENUES × MATCHES", "Venue Intelligence", sub_line)
    GT = ground_table(F)
    gq = GT[GT["matches"] >= 10].sort_values("chase_pct", ascending=False)
    kpis([
        ("GROUNDS", f"{len(GT)}", f"{venues_df.shape[0]} raw venue records merged", False),
        ("CITIES", f"{GT['city_clean'].nunique()}", f"{GT['region'].nunique()} regions", False),
        ("BUSIEST GROUND", GT.iloc[0]["ground"], f"{int(GT.iloc[0]['matches'])} matches", True),
        ("CHASER'S PARADISE", gq.iloc[0]["ground"] if len(gq) else "—",
         f"{gq.iloc[0]['chase_pct']:.1f}% chase wins (min. 10)" if len(gq) else "Not enough matches", True),
    ])

    c1, c2 = st.columns([1, 1.1])
    with c1, st.container(border=True):
        section("Matches hosted", "top 15 grounds")
        g = GT.head(15).sort_values("matches")
        fig = go.Figure(go.Bar(x=g["matches"], y=g["ground"], orientation="h",
                               marker_color=[REGION_COLORS.get(r, MUTED) for r in g["region"]],
                               text=g["matches"], textposition="outside", cliponaxis=False, textfont=dict(color=IVORY)))
        show(base(fig, 520, legend=False))
    with c2, st.container(border=True):
        section("Venue map", "region → city → ground · colour = chase win %")
        tm = px.treemap(GT, path=[px.Constant("IPL"), "region", "city_clean", "ground"], values="matches",
                        color="chase_pct", color_continuous_scale=TREEMAP_SCALE, range_color=(30, 70))
        tm.update_traces(root_color="rgba(0,0,0,0)", marker_line_color=BG, marker_line_width=2,
                         textfont=dict(color=IVORY), hovertemplate="%{label}<br>%{value} matches<extra></extra>")
        tm.update_layout(coloraxis_colorbar=dict(title="Chase %", thickness=10, len=0.8))
        show(base(tm, 520, legend=False))

    c3, c4 = st.columns(2)
    with c3, st.container(border=True):
        section("Does the venue favour chasing?", "grounds with 8+ decided matches · bubble = matches")
        gb = GT[GT["decided"] >= 8]
        if gb.empty:
            empty_note("No ground has 8+ decided matches under these filters.")
        else:
            fig = px.scatter(gb, x="matches", y="chase_pct", size="matches", color="region", hover_name="ground",
                             color_discrete_map=REGION_COLORS, size_max=34)
            fig.add_hline(y=50, line_dash="dot", line_color=MUTED)
            fig.update_yaxes(range=[15, 85], ticksuffix="%")
            fig.update_xaxes(title="Matches hosted")
            show(base(fig, 380))
    with c4, st.container(border=True):
        section("Toss call by ground", "% choosing to field first · top 10 grounds")
        gt = GT.head(10).sort_values("toss_field")
        fig = go.Figure()
        fig.add_bar(y=gt["ground"], x=gt["toss_field"], name="Field", orientation="h", marker_color=GOLD)
        fig.add_bar(y=gt["ground"], x=100 - gt["toss_field"], name="Bat", orientation="h", marker_color="#3A362B")
        fig.update_layout(barmode="stack")
        fig.update_xaxes(ticksuffix="%", range=[0, 100])
        show(base(fig, 380))

    with st.container(border=True):
        section("Ground register", "every ground in the current view")
        reg = GT.rename(columns={"ground": "Ground", "city_clean": "City", "region": "Region", "matches": "Matches",
                                 "bf_pct": "Bat-first win %", "chase_pct": "Chase win %", "toss_field": "Field-first toss %",
                                 "top_team": "Most successful side", "top_wins": "Wins"})[
            ["Ground", "City", "Region", "Matches", "Bat-first win %", "Chase win %", "Field-first toss %", "Most successful side", "Wins"]]
        pc = lambda lbl: st.column_config.ProgressColumn(lbl, min_value=0, max_value=100, format="%.1f%%")
        st.dataframe(reg, hide_index=True, height=420,
                     column_config={"Bat-first win %": pc("Bat-first win %"), "Chase win %": pc("Chase win %"),
                                    "Field-first toss %": pc("Field-first toss %")}, **FILL)
        st.download_button("Download ground register (CSV)", reg.to_csv(index=False).encode(),
                           file_name="ground_register.csv", mime="text/csv")

# ═════════════════════════ PAGE 4 · FRANCHISE × VENUE ═════════════════════════
elif page == "Franchise × Venue":
    hero("TEAMS × VENUES × MATCHES", "Franchise × Venue", "How each franchise performs at each ground · " + sub_line)
    ctl1, ctl2 = st.columns(2)
    top_n = ctl1.slider("Grounds shown (by matches hosted)", 6, 20, 12)
    min_cell = ctl2.slider("Minimum matches for a cell", 1, 6, 2)
    top_grounds = F["ground"].value_counts().head(top_n).index.tolist()
    Lg = L[L["ground"].isin(top_grounds)]
    dec = Lg.assign(w=Lg["won"].astype(int))
    P = dec.groupby(["team", "ground"]).agg(played=("w", "size"), wins=("w", "sum"), dec_n=("decided", "sum")).reset_index()
    P["pct"] = np.where(P["dec_n"] > 0, P["wins"] / P["dec_n"].replace(0, np.nan) * 100, np.nan)
    P = P[P["played"] >= min_cell]
    rows = TT["team"].tolist()
    if P.empty:
        empty_note("No franchise/ground pair meets the minimum under these filters.")
    else:
        with st.container(border=True):
            section("Win rate heatmap", "cell text = wins / matches played · blank = below minimum")
            Z = P.pivot(index="team", columns="ground", values="pct").reindex(index=rows, columns=top_grounds)
            Tx = P.assign(t=P["wins"].astype(int).astype(str) + "/" + P["played"].astype(int).astype(str)) \
                  .pivot(index="team", columns="ground", values="t").reindex(index=rows, columns=top_grounds).fillna("")
            fig = go.Figure(go.Heatmap(z=Z.values, x=top_grounds, y=rows, text=Tx.values, texttemplate="%{text}",
                                       zmid=50, zmin=0, zmax=100, colorscale=DIVERGING, xgap=2, ygap=2,
                                       textfont=dict(size=10, color=IVORY),
                                       hovertemplate="%{y} at %{x}<br>Win %{z:.0f}%<extra></extra>",
                                       colorbar=dict(title="Win %", thickness=10, len=0.8)))
            fig.update_yaxes(autorange="reversed")
            fig.update_xaxes(tickangle=-40)
            show(base(fig, 190 + 34 * len(rows), legend=False))

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        team = st.selectbox("Franchise detail", rows, key="tv_team")
        Lt = L_all[L_all["team"] == team]
        by_g = Lt.groupby(["ground", "city_clean"]).agg(Played=("won", "size"), Won=("won", "sum"), Lost=("lost", "sum")).reset_index()
        by_g["Win %"] = (by_g["Won"] / (by_g["Won"] + by_g["Lost"]).replace(0, np.nan) * 100).round(1)
        q = by_g[by_g["Played"] >= 3].sort_values("Win %", ascending=False)
        kpis([
            ("MATCHES", f"{len(Lt)}", team, False),
            ("GROUNDS VISITED", f"{by_g['ground'].nunique()}", f"{Lt['city_clean'].nunique()} cities", False),
            ("FORTRESS", q.iloc[0]["ground"] if len(q) else "—", f"{q.iloc[0]['Win %']:.1f}% win (min. 3 matches)" if len(q) else "Not enough matches", True),
            ("TOUGHEST TRIP", q.iloc[-1]["ground"] if len(q) else "—", f"{q.iloc[-1]['Win %']:.1f}% win (min. 3 matches)" if len(q) else "Not enough matches", True),
        ])
        a, b = st.columns([1.2, 1])
        tcolor = TEAM_COLORS.get(team, GOLD)
        with a, st.container(border=True):
            section(f"{team}", "matches played and won by ground")
            gg = by_g.nlargest(12, "Played").sort_values("Played")
            fig = go.Figure()
            fig.add_bar(y=gg["ground"], x=gg["Played"], name="Played", orientation="h", marker_color="#3A362B")
            fig.add_bar(y=gg["ground"], x=gg["Won"], name="Won", orientation="h", marker_color=tcolor)
            fig.update_layout(barmode="overlay")
            show(base(fig, 440))
        with b, st.container(border=True):
            section("Ground record", "all grounds")
            st.dataframe(by_g.sort_values("Played", ascending=False).rename(columns={"ground": "Ground", "city_clean": "City"}),
                         hide_index=True, height=440,
                         column_config={"Win %": st.column_config.ProgressColumn("Win %", min_value=0, max_value=100, format="%.1f%%")},
                         **FILL)

# ═════════════════════════ PAGE 5 · MATCH LEDGER ═════════════════════════
else:
    hero("THE RECORD", "Match Ledger", sub_line)
    q = st.text_input("Search franchise, ground, city or player", placeholder="e.g. Chennai, Wankhede, Kohli")
    led = F.copy()
    if q:
        blob = (led["team1"] + " " + led["team2"] + " " + led["ground"] + " " + led["city_clean"] + " " + led["player_of_match"]).str.lower()
        led = led[blob.str.contains(q.lower(), regex=False)]
    out = led.sort_values("date", ascending=False)[
        ["date", "season_year", "team1", "team2", "ground", "city_clean", "toss_winner", "toss_decision",
         "match_winner", "margin", "player_of_match", "result"]].copy()
    out["date"] = out["date"].dt.strftime("%d %b %Y")
    out.columns = ["Date", "Season", "Team 1", "Team 2", "Ground", "City", "Toss won by", "Toss decision",
                   "Winner", "Margin", "Player of the Match", "Result"]
    with st.container(border=True):
        section("All matches", f"{len(out):,} shown")
        st.dataframe(out, hide_index=True, height=520, **FILL)
        st.download_button("Download matches (CSV)", out.to_csv(index=False).encode(),
                           file_name="ipl_matches_filtered.csv", mime="text/csv")

    w1, w2 = st.columns(2)
    with w1, st.container(border=True):
        section("Biggest wins by runs", "top 8")
        b = led[led["win_by_runs"].notna()].nlargest(8, "win_by_runs")
        st.dataframe(pd.DataFrame({"Winner": b["match_winner"], "Margin": b["win_by_runs"].astype(int).astype(str) + " runs",
                                   "Against": np.where(b["match_winner"] == b["team1"], b["team2"], b["team1"]),
                                   "Ground": b["ground"], "Season": b["season_year"]}), hide_index=True, **FILL)
    with w2, st.container(border=True):
        section("Most dominant chases", "most wickets in hand · top 8")
        b = led[led["win_by_wickets"].notna()].nlargest(8, "win_by_wickets")
        st.dataframe(pd.DataFrame({"Winner": b["match_winner"], "Margin": b["win_by_wickets"].astype(int).astype(str) + " wkts",
                                   "Against": np.where(b["match_winner"] == b["team1"], b["team2"], b["team1"]),
                                   "Ground": b["ground"], "Season": b["season_year"]}), hide_index=True, **FILL)
