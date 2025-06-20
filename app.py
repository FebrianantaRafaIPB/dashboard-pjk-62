import streamlit as st
import pandas as pd
import altair as alt

# === LOAD GOOGLE SHEETS CSV ===
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1sWEVXl3YIWyvNJv08hZ4TrOBs2t8ndJXXP-VhKSp6mE/export?format=csv"
    return pd.read_csv(url)

df = load_data()

# === CLEAN STRING FIELDS ===
df["Kelompok Besar"] = df["Kelompok Besar"].fillna("").astype(str)
df["Kelompok Sedang"] = df["Kelompok Sedang"].fillna("").astype(str)
df["Status Pita"] = df["Status Pita"].astype(str).str.strip()
df["StatusRegistrasi"] = df["StatusRegistrasi"].astype(str).str.strip()

# === UI FILTERS ===
st.title("📊 DASHBOARD PJK MPKMB IPB 62 SARJANA")
cols = st.columns(3)

dimensi = cols[0].selectbox("Dimension:", ["Kelompok Besar", "Kelompok Sedang"])
filter_kb = cols[1].selectbox("Kelompok Besar", ["(All)"] + sorted(df["Kelompok Besar"].unique()))
filter_ks = cols[2].selectbox("Kelompok Sedang", ["(All)"] + sorted(df["Kelompok Sedang"].unique()))

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

m1, m2, m3 = st.columns(3)
m1.metric("Total Maba", total_maba)
m2.metric("Maba Pita Merah", pita_merah)
m3.metric("Status Tidak Aktif", tidak_aktif)

# === CHART 1: COMPLETION RATE ===
group_col = dimensi
cr_df = df_filtered.groupby(group_col)["Completion Rate %"].mean().reset_index()

st.subheader("📈 Completion Rate Penugasan")
chart1 = alt.Chart(cr_df).mark_bar(color="steelblue").encode(
    x=alt.X(group_col, sort='-y'),
    y=alt.Y("Completion Rate %:Q"),
    tooltip=["Completion Rate %"]
).properties(height=300)
st.altair_chart(chart1, use_container_width=True)

# === CHART 2: STATUS PENILAIAN PER KELOMPOK ===
penugasan_cols = [col for col in df.columns if "Penugasan" in col or "Challenge" in col]

if penugasan_cols:
    melted = df_filtered.melt(
        id_vars=[group_col],
        value_vars=penugasan_cols,
        var_name="Tugas",
        value_name="Status"
    ).dropna(subset=[group_col, "Status"])

    melted = melted[melted["Status"].isin(["Graded", "Ungraded"])]

    status_df = melted.groupby([group_col, "Status"]).size().reset_index(name="Count")
    ordered_groups = status_df[group_col].unique().tolist()

    st.subheader("📊 Status Penilaian Tugas per Kelompok")
    chart2 = alt.Chart(status_df).mark_bar().encode(
        y=alt.Y(group_col, sort=ordered_groups, title=group_col),
        x=alt.X("Count:Q", stack="zero", title="Jumlah Tugas"),
        color=alt.Color("Status:N", scale=alt.Scale(
            domain=["Graded", "Ungraded"],
            range=["#3b5ba3", "#c0392b"]
        )),
        tooltip=[group_col, "Status", "Count"]
    ).properties(height=300)
    st.altair_chart(chart2, use_container_width=True)

# === CHART 3: STATUS PER TUGAS (COMPLETED VS NOT) ===
status_cols = df_filtered.columns[20:26]  # Kolom U-Z
tugas_status = df_filtered[status_cols].melt(
    var_name="Tugas", value_name="Status"
).dropna()

tugas_status = tugas_status[tugas_status["Status"].isin(["Completed", "Not Completed"])]
status_tugas_df = tugas_status.groupby(["Tugas", "Status"]).size().reset_index(name="Count")

st.subheader("📌 Status Per Tugas (Completed vs Not Completed)")
chart3 = alt.Chart(status_tugas_df).mark_bar().encode(
    x=alt.X("Tugas:N", sort=None),
    y=alt.Y("Count:Q", title="Jumlah Mahasiswa"),
    color=alt.Color("Status:N", scale=alt.Scale(
        domain=["Completed", "Not Completed"],
        range=["#27ae60", "#e74c3c"]
    )),
    tooltip=["Tugas", "Status", "Count"]
).properties(height=400)

st.altair_chart(chart3, use_container_width=True)
