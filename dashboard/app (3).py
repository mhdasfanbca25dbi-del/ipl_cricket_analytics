from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="IPL Cricket Analytics", page_icon="🏏", layout="wide")

APP_DIR = Path(__file__).resolve().parent
CANDIDATES = [
    APP_DIR / "data" / "raw" / "ipl.db",
    APP_DIR.parent / "data" / "raw" / "ipl.db",
    APP_DIR.parent.parent / "data" / "raw" / "ipl.db",
    Path.cwd() / "data" / "raw" / "ipl.db",
    Path(r"C:\Users\asfan\ipl-cricket_analytics\data\raw\ipl.db"),
]
DB_PATH = next((p for p in CANDIDATES if p.exists()), None)

st.markdown("""
<style>
.stApp {background:#f5f7fb;}
[data-testid="stSidebar"] {background:#10233f;}
[data-testid="stSidebar"] * {color:white;}
div[data-testid="stMetric"] {background:white;border:1px solid #e4eaf3;padding:16px;border-radius:14px;}
</style>
""", unsafe_allow_html=True)


def qi(value):
    return '"' + value.replace('"', '""') + '"'


@st.cache_data(show_spinner=False)
def database_tables(db_path):
    with sqlite3.connect(db_path) as conn:
        names = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        result = {}
        for name in names:
            columns = conn.execute(f"PRAGMA table_info({qi(name)})").fetchall()
            result[name] = [{"Column": c[1], "Type": c[2] or "Unknown",
                             "Primary key": bool(c[5]), "Not null": bool(c[3])}
                            for c in columns]
    return result


@st.cache_data(show_spinner=False)
def load_table(db_path, table_name):
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {qi(table_name)}", conn)


with st.sidebar:
    st.markdown("## 🏏 IPL ANALYTICS")
    st.caption("SQLite database dashboard")
    page = st.radio("Navigate", ["Overview", "Explore Data", "Data Quality", "Table Details"])

st.title("IPL Cricket Analytics Dashboard")
st.caption("Team and venue data explorer powered by your SQLite database.")

if DB_PATH is None:
    st.error("Database file ipl.db was not found.")
    st.write("Expected local path:")
    st.code(r"C:\Users\asfan\ipl-cricket_analytics\data\raw\ipl.db")
    st.info("If deploying to Streamlit Cloud, add the database file to the repository and configure a relative path.")
    st.stop()

try:
    metadata = database_tables(str(DB_PATH))
except Exception as exc:
    st.error(f"Could not open database: {exc}")
    st.stop()

if not metadata:
    st.warning("Database opened, but no tables were found.")
    st.stop()

tables = list(metadata)
data = {}
for table in tables:
    try:
        data[table] = load_table(str(DB_PATH), table)
    except Exception as exc:
        st.warning(f"Could not load table {table}: {exc}")

total_rows = sum(len(df) for df in data.values())
total_columns = sum(len(df.columns) for df in data.values())

if page == "Overview":
    st.subheader("Database overview")
    a, b, c, d = st.columns(4)
    a.metric("Tables", len(tables))
    b.metric("Total rows", f"{total_rows:,}")
    c.metric("Total columns", f"{total_columns:,}")
    d.metric("Database size", f"{DB_PATH.stat().st_size / (1024 * 1024):.2f} MB")

    row_counts = pd.DataFrame([
        {"Table": name, "Rows": len(df)} for name, df in data.items()
    ]).sort_values("Rows", ascending=True)
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("### Records by table")
        fig = px.bar(row_counts, x="Rows", y="Table", orientation="h", text="Rows")
        fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### Tables")
        st.dataframe(row_counts.sort_values("Rows", ascending=False), use_container_width=True, hide_index=True)
    st.info("Charts and counts are calculated from the actual database; no statistics are invented.")

elif page == "Explore Data":
    st.subheader("Explore database records")
    table = st.selectbox("Select table", tables)
    df = data[table]
    query = st.text_input("Search all columns", placeholder="Enter a team, venue, city, or value")
    shown = df
    if query.strip():
        match = df.astype(str).apply(
            lambda col: col.str.contains(query.strip(), case=False, na=False)
        ).any(axis=1)
        shown = df[match]
    st.caption(f"Showing {len(shown):,} of {len(df):,} rows")
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.download_button("Download displayed rows as CSV", shown.to_csv(index=False).encode("utf-8"),
                       file_name=f"{table}.csv", mime="text/csv")

    cat_cols = [col for col in df.columns if df[col].dtype == "object"]
    if cat_cols and not df.empty:
        st.markdown("### Quick category chart")
        col = st.selectbox("Choose a text column", cat_cols)
        limit = st.slider("Show top categories", min_value=5, max_value=30, value=10)
        counts = df[col].fillna("(Missing)").astype(str).value_counts().head(limit).rename_axis(col).reset_index(name="Records")
        fig = px.bar(counts.sort_values("Records"), x="Records", y=col, orientation="h", text="Records")
        fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Data Quality":
    st.subheader("Data quality report")
    report = []
    for name, df in data.items():
        report.append({
            "Table": name,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Missing cells": int(df.isna().sum().sum()),
            "Columns with missing values": int((df.isna().sum() > 0).sum()),
            "Duplicate rows": int(df.duplicated().sum()) if not df.empty else 0,
        })
    st.dataframe(pd.DataFrame(report), use_container_width=True, hide_index=True)
    table = st.selectbox("Inspect columns in table", tables)
    df = data[table]
    detail = pd.DataFrame({
        "Column": df.columns,
        "Data type": [str(df[c].dtype) for c in df.columns],
        "Missing values": [int(df[c].isna().sum()) for c in df.columns],
        "Missing %": [round(float(df[c].isna().mean() * 100), 2) if len(df) else 0 for c in df.columns],
    })
    st.dataframe(detail, use_container_width=True, hide_index=True)
    if df.isna().any(axis=None):
        st.markdown("### Rows containing missing values")
        st.dataframe(df[df.isna().any(axis=1)], use_container_width=True, hide_index=True)
    else:
        st.success("No missing values in this table.")

elif page == "Table Details":
    st.subheader("Table and column details")
    table = st.selectbox("Select table", tables)
    st.markdown(f"### `{table}`")
    st.dataframe(pd.DataFrame(metadata[table]), use_container_width=True, hide_index=True)
    st.markdown("### First 100 rows")
    st.dataframe(data[table].head(100), use_container_width=True, hide_index=True)

st.divider()
st.caption(f"Database: {DB_PATH} • Streamlit + Pandas + Plotly + SQLite")
