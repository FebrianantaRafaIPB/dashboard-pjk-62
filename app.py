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

# === CLEAN DATA ===
df["Kelompok Besar"] = df["Kelompok Besar"].fillna("").astype(str).str.strip()
df["Kelompok Sedang"] = df["Kelompok Sedang"].fillna("").astype(str).str.strip()
df["Status Pita"] = df["Status Pita"].fillna("").astype(str).str.strip().str.title()
df["StatusRegistrasi"] = df["StatusRegistrasi"].fillna("").astype(str).str.strip().str.title()
df = df[df["Kelompok Besar"] != ""]
df = df[df["Kelompok Sedang"] != ""]

# === SIDEBAR FILTER ===
with st.sidebar:
    st.header("Filter")
    dimensi = st.selectbox("Dimension:", ["Kelompok Besar", "Kelompok Sedang"])
    kb_list = sorted(df["Kelompok Besar"].unique())
    ks_list = sorted(df["Kelompok Sedang"].unique())
    filter_kb = st.selectbox("Kelompok Besar", ["(All)"] + kb_list)
    filter_ks = st.selectbox("Kelompok Sedang", ["(All)"] + ks_list)

    st.markdown("---")
    st.markdown("**Pengaduan PJK 62**")
    st.markdown(
        '<a href="https://ipb.link/pengaduan-pjk-62" target="_blank">'
        '<button style="background-color:#e74c3c;color:white;padding:8px 12px;'
        'border:none;border-radius:6px;cursor:pointer;font-size:14px;'
        'font-weight:bold;width:100%;">Kirim Pengaduan</button>'
        '</a>',
        unsafe_allow_html=True
    )

# === FILTERED DATA ===
df_filtered = df.copy()
if filter_kb != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Besar"] == filter_kb]
if filter_ks != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Sedang"] == filter_ks]

# === TITLE & METRICS ===
st.title("DASHBOARD PJK MPKMB IPB 62 SARJANA")
col1, col2, col3 = st.columns(3)
col1.metric("Total Maba", len(df_filtered))
col2.metric("Maba Pita Merah", (df_filtered["Status Pita"] == "Pita Merah").sum())
col3.metric("Status Tidak Aktif", (df_filtered["StatusRegistrasi"] == "Tidak Aktif").sum())

# === CHART 1: Completion Rate ===
group_col = dimensi
cr_df = df_filtered.groupby(group_col)["Completion Rate %"].mean().reset_index()

st.subheader("Completion Rate")
chart1 = alt.Chart(cr_df).mark_bar(color="#3498db").encode(
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

st.subheader("Status Penugasan")
chart2 = alt.Chart(status_df).mark_bar().encode(
    y=alt.Y(group_col, sort=ordered_groups, axis=alt.Axis(labelFontSize=10)),
    x=alt.X("Count:Q", stack="zero", axis=alt.Axis(labelFontSize=10)),
    color=alt.Color("Status:N", scale=alt.Scale(
        domain=["Graded", "Ungraded"],
        range=["#3498db", "#e74c3c"]
    )),
    tooltip=[group_col, "Status", "Count"]
).properties(height=320)
st.altair_chart(chart2, use_container_width=True)

# === CHART 3: Status Per Tugas (Altair) ===
st.subheader("Status Per Tugas")

status_cols = df_filtered.columns[20:26]
tugas_status = df_filtered[status_cols].melt(
    var_name="Tugas", value_name="Status").dropna()
tugas_status["Status"] = tugas_status["Status"].str.strip().str.title()
tugas_status = tugas_status[tugas_status["Status"].isin(["Completed", "Not Completed"])]

def wrap_label(text, width=30):
    return '\n'.join([text[i:i+width] for i in range(0, len(text), width)])
tugas_status["Tugas"] = tugas_status["Tugas"].apply(lambda x: wrap_label(x, width=30))

status_tugas_df = tugas_status.groupby(["Tugas", "Status"]).size().reset_index(name="Count")
all_index = pd.DataFrame(product(tugas_status["Tugas"].unique(), ["Completed", "Not Completed"]),
                         columns=["Tugas", "Status"])
status_tugas_df = all_index.merge(status_tugas_df, on=["Tugas", "Status"], how="left").fillna(0)

chart3 = alt.Chart(status_tugas_df).mark_bar().encode(
    x=alt.X("Tugas:N", sort=None, axis=alt.Axis(labelAngle=-20, labelFontSize=10)),
    y=alt.Y("Count:Q", title="Jumlah Mahasiswa"),
    color=alt.Color("Status:N", scale=alt.Scale(
        domain=["Completed", "Not Completed"],
        range=["#3498db", "#e74c3c"]
    )),
    tooltip=["Tugas", "Status", "Count"]
).properties(height=380)
st.altair_chart(chart3, use_container_width=True)

# === INSIGHT OTOMATIS ===
st.subheader("SI Insight")
try:
    insight_lines = []
    total = len(df_filtered)
    if total == 0:
        insight_lines.append("Tidak ada data tersedia pada filter saat ini.")
    else:
        cr_avg = df_filtered["Completion Rate %"].mean()
        insight_lines.append(f"• Dari total {total} maba, rata-rata Completion Rate adalah {cr_avg:.1f}%.")

        status_penugasan = melted.groupby("Status").size().to_dict()
        for status in ["Graded", "Ungraded"]:
            if status in status_penugasan:
                insight_lines.append(f"• Terdapat {status_penugasan[status]} tugas dengan status **{status}**.")

        status_counts = tugas_status[tugas_status["Status"] == "Not Completed"].groupby("Tugas").size()
        if not status_counts.empty:
            worst_task = status_counts.idxmax()
            worst_count = status_counts.max()
            insight_lines.append(f"• Tugas **{worst_task}** adalah yang paling sering *Not Completed* ({worst_count} maba).")

        tidak_aktif = (df_filtered["StatusRegistrasi"] == "Tidak Aktif").sum()
        if tidak_aktif > 0:
            insight_lines.append(f"• Terdapat {tidak_aktif} maba dengan status **Tidak Aktif**.")

        if group_col in df_filtered.columns:
            lowest_group = cr_df.sort_values("Completion Rate %").iloc[0]
            insight_lines.append(
                f"• Kelompok **{lowest_group[group_col]}** memiliki Completion Rate terendah ({lowest_group['Completion Rate %']:.1f}%)."
            )

    for line in insight_lines:
        st.markdown(line)

except Exception as e:
    st.warning(f"Gagal menghasilkan insight otomatis: {e}")
