import streamlit as st
import pandas as pd
import altair as alt

# === CONFIG PAGE ===
st.set_page_config(layout="wide", page_title="Dashboard PJK MPKMB IPB 62")

# === LOAD GOOGLE SHEETS CSV ===
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1sWEVXl3YIWyvNJv08hZ4TrOBs2t8ndJXXP-VhKSp6mE/export?format=csv"
    return pd.read_csv(url)

df = load_data()

# === CLEAN & NORMALIZE STRING ===
df["Kelompok Besar"] = df["Kelompok Besar"].fillna("").astype(str).str.strip()
df["Kelompok Sedang"] = df["Kelompok Sedang"].fillna("").astype(str).str.strip()
df["Status Pita"] = df["Status Pita"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
df["StatusRegistrasi"] = df["StatusRegistrasi"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

# === HILANGKAN BARIS KOSONG ===
df = df[df["Kelompok Besar"] != ""]
df = df[df["Kelompok Sedang"] != ""]

# === SIDEBAR FILTER ===
with st.sidebar:
    st.header("🔍 Filter")
    dimensi = st.selectbox("Dimension:", ["Kelompok Besar", "Kelompok Sedang"])

    kelompok_besar_list = sorted(df["Kelompok Besar"].dropna().unique())
    kelompok_besar_list = [x for x in kelompok_besar_list if x.strip() != ""]
    filter_kb = st.selectbox("Kelompok Besar", ["(All)"] + kelompok_besar_list)

    kelompok_sedang_list = sorted(df["Kelompok Sedang"].dropna().unique())
    kelompok_sedang_list = [x for x in kelompok_sedang_list if x.strip() != ""]
    filter_ks = st.selectbox("Kelompok Sedang", ["(All)"] + kelompok_sedang_list)

# === TITLE ===
st.title("📊 DASHBOARD PJK MPKMB IPB 62 SARJANA")

# === FILTERED DATA ===
df_filtered = df.copy()
if filter_kb != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Besar"] == filter_kb]
if filter_ks != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Sedang"] == filter_ks]

# === SCORE CARDS ===
total_maba = len(df_filtered)
pita_merah = (df_filtered["Status Pita"] == "Pita Merah").sum()
tidak_aktif = (df_filtered["StatusRegistrasi"] == "Tidak Aktif").sum()

sc1, sc2, sc3 = st.columns(3)
sc1.metric("Total Maba", total_maba)
sc2.metric("Maba Pita Merah", pita_merah)
sc3.metric("Status Tidak Aktif", tidak_aktif)

# === DATA UNTUK CHARTS ===
group_col = dimensi
cr_df = df_filtered.groupby(group_col)["Completion Rate %"].mean().reset_index()

penugasan_cols = [col for col in df.columns if "Penugasan" in col or "Challenge" in col]
melted = df_filtered.melt(
    id_vars=[group_col],
    value_vars=penugasan_cols,
    var_name="Tugas",
    value_name="Status"
).dropna(subset=[group_col, "Status"])
melted = melted[melted["Status"].isin(["Graded", "Ungraded"])]
status_df = melted.groupby([group_col, "Status"]).size().reset_index(name="Count")
ordered_groups = status_df[group_col].unique().tolist()

status_cols = df_filtered.columns[20:26]
tugas_status = df_filtered[status_cols].melt(
    var_name="Tugas", value_name="Status"
).dropna()
tugas_status = tugas_status[tugas_status["Status"].isin(["Completed", "Not Completed"])]
status_tugas_df = tugas_status.groupby(["Tugas", "Status"]).size().reset_index(name="Count")

# === CHART 1 & 2 (SIDE BY SIDE) ===
c1, c2 = st.columns(2)

with c1:
    st.subheader("📈 Completion Rate")
    chart1 = alt.Chart(cr_df).mark_bar(color="steelblue").encode(
        y=alt.Y(group_col, sort='-x', title=group_col),
        x=alt.X("Completion Rate %:Q", title="Completion Rate"),
        tooltip=[group_col, "Completion Rate %"]
    ).properties(height=220)
    st.altair_chart(chart1, use_container_width=True)

with c2:
    st.subheader("📊 Status Penugasan")
    chart2 = alt.Chart(status_df).mark_bar().encode(
        y=alt.Y(group_col, sort=ordered_groups, title=group_col),
        x=alt.X("Count:Q", stack="zero", title="Jumlah Tugas"),
        color=alt.Color("Status:N", scale=alt.Scale(
            domain=["Graded", "Ungraded"],
            range=["#3b5ba3", "#c0392b"]
        )),
        tooltip=[group_col, "Status", "Count"]
    ).properties(height=220)
    st.altair_chart(chart2, use_container_width=True)

# === CHART 3 (FULL WIDTH) ===
st.subheader("📌 Status Per Tugas")
chart3 = alt.Chart(status_tugas_df).mark_bar().encode(
    x=alt.X("Tugas:N", sort=None, axis=alt.Axis(labelAngle=-35)),
    y=alt.Y("Count:Q", title="Jumlah Mahasiswa"),
    color=alt.Color("Status:N", scale=alt.Scale(
        domain=["Completed", "Not Completed"],
        range=["#27ae60", "#e74c3c"]
    )),
    tooltip=["Tugas", "Status", "Count"]
).properties(height=240)
st.altair_chart(chart3, use_container_width=True)
