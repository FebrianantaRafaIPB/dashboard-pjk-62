import streamlit as st
import pandas as pd
import altair as alt
from itertools import product

# === CONFIG PAGE ===
st.set_page_config(layout="wide", page_title="Dashboard PJK MPKMB IPB 62")

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1sWEVXl3YIWyvNJv08hZ4TrOBs2t8ndJXXP-VhKSp6mE/export?format=csv"
    return pd.read_csv(url)

df = load_data()

# === CLEAN ===
df["Kelompok Besar"] = df["Kelompok Besar"].fillna("").astype(str).str.strip()
df["Kelompok Sedang"] = df["Kelompok Sedang"].fillna("").astype(str).str.strip()
df["Status Pita"] = df["Status Pita"].fillna("").astype(str).str.strip()
df["StatusRegistrasi"] = df["StatusRegistrasi"].fillna("").astype(str).str.strip()
df = df[df["Kelompok Besar"] != ""]
df = df[df["Kelompok Sedang"] != ""]

# === SIDEBAR FILTER ===
with st.sidebar:
    st.header("🔍 Filter")
    dimensi = st.selectbox("Dimension:", ["Kelompok Besar", "Kelompok Sedang"])
    kb_list = sorted(df["Kelompok Besar"].unique())
    ks_list = sorted(df["Kelompok Sedang"].unique())
    filter_kb = st.selectbox("Kelompok Besar", ["(All)"] + kb_list)
    filter_ks = st.selectbox("Kelompok Sedang", ["(All)"] + ks_list)

# === FILTERED DATA ===
df_filtered = df.copy()
if filter_kb != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Besar"] == filter_kb]
if filter_ks != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Sedang"] == filter_ks]

# === TITLE & METRICS ===
st.title("📊 DASHBOARD PJK MPKMB IPB 62 SARJANA")
col1, col2, col3 = st.columns(3)
col1.metric("Total Maba", len(df_filtered))
col2.metric("Maba Pita Merah", (df_filtered["Status Pita"] == "Pita Merah").sum())
col3.metric("Status Tidak Aktif", (df_filtered["StatusRegistrasi"] == "Tidak Aktif").sum())

# === CHART 1: Completion Rate ===
group_col = dimensi
cr_df = df_filtered.groupby(group_col)["Completion Rate %"].mean().reset_index()

st.subheader("📈 Completion Rate")
chart1 = alt.Chart(cr_df).mark_bar(color="steelblue").encode(
    y=alt.Y(group_col, sort='-x', axis=alt.Axis(labelFontSize=10)),
    x=alt.X("Completion Rate %:Q", axis=alt.Axis(labelFontSize=10)),
    tooltip=[group_col, "Completion Rate %"]
).properties(height=320)
st.altair_chart(chart1, use_container_width=True)

# === CHART 2: Status Penugasan ===
penugasan_cols = [col for col in df.columns if "Penugasan" in col or "Challenge" in col]
melted = df_filtered.melt(id_vars=[group_col], value_vars=penugasan_cols,
                          var_name="Tugas", value_name="Status").dropna()
melted = melted[melted["Status"].isin(["Graded", "Ungraded"])]
status_df = melted.groupby([group_col, "Status"]).size().reset_index(name="Count")
ordered_groups = status_df[group_col].unique().tolist()

st.subheader("📊 Status Penugasan")
chart2 = alt.Chart(status_df).mark_bar().encode(
    y=alt.Y(group_col, sort=ordered_groups, axis=alt.Axis(labelFontSize=10)),
    x=alt.X("Count:Q", stack="zero", axis=alt.Axis(labelFontSize=10)),
    color=alt.Color("Status:N", scale=alt.Scale(
        domain=["Graded", "Ungraded"],
        range=["#3b5ba3", "#c0392b"]
    )),
    tooltip=[group_col, "Status", "Count"]
).properties(height=320)
st.altair_chart(chart2, use_container_width=True)

# === CHART 3: Status Per Tugas ===
status_cols = df_filtered.columns[20:26]
tugas_status = df_filtered[status_cols].melt(
    var_name="Tugas", value_name="Status").dropna()

tugas_status["Status"] = tugas_status["Status"].str.strip().str.title()
tugas_status = tugas_status[tugas_status["Status"].isin(["Completed", "Not Completed"])]
status_tugas_df = tugas_status.groupby(["Tugas", "Status"]).size().reset_index(name="Count")

# Tambahkan kombinasi kosong
all_tugas = tugas_status["Tugas"].unique()
full_index = pd.DataFrame(product(all_tugas, ["Completed", "Not Completed"]),
                          columns=["Tugas", "Status"])
status_tugas_df = full_index.merge(status_tugas_df, on=["Tugas", "Status"], how="left").fillna(0)

# Urutan stack fix
status_order = ["Completed", "Not Completed"]
status_tugas_df["Status"] = pd.Categorical(status_tugas_df["Status"], categories=status_order, ordered=True)
status_tugas_df = status_tugas_df.sort_values(["Tugas", "Status"])

# CHART 3
st.subheader("📌 Status Per Tugas")
chart3 = alt.Chart(status_tugas_df).mark_bar().encode(
    x=alt.X("Tugas:N", sort=None, axis=alt.Axis(
        labelAngle=-35,
        labelFontSize=10,
        labelExpr="replace(datum.label, 'Status ', '')",  # remove "Status "
        titleFontSize=12
    )),
    y=alt.Y("Count:Q", title="Jumlah Mahasiswa", axis=alt.Axis(labelFontSize=10)),
    color=alt.Color("Status:N", scale=alt.Scale(
        domain=["Not Completed", "Completed"],  # warna merah atas
        range=["#e74c3c", "#27ae60"]
    )),
    tooltip=["Tugas", "Status", "Count"]
).properties(height=340)
st.altair_chart(chart3, use_container_width=True)
