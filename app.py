import streamlit as st
import pandas as pd
import altair as alt
from itertools import product

# === CONFIG PAGE ===
st.set_page_config(layout="wide", page_title="Dashboard PJK MPKMB IPB 62")

@st.cache_data(show_spinner=False)
def load_data():
    url = st.secrets["CSV_URL"]
    return pd.read_csv(url)

df = load_data()

# === CLEAN DATA ===
df["Kelompok Besar"] = df["Kelompok Besar"].fillna("").astype(str).str.strip()
df["Kelompok Sedang / Nama PJK"] = df["Kelompok Sedang / Nama PJK"].fillna("").astype(str).str.strip()
df["Status Pita"] = df["Status Pita"].fillna("").astype(str).str.strip().str.title()
df["StatusRegistrasi"] = df["StatusRegistrasi"].fillna("").astype(str).str.strip().str.title()
df = df[df["Kelompok Besar"] != ""]
df = df[df["Kelompok Sedang / Nama PJK"] != ""]

# === SIDEBAR FILTER ===
with st.sidebar:
    if st.button("Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    perspektif = st.radio("🔍 Anda di sini sebagai:", ["PJK", "Panglima"], horizontal=True)

    st.header("Filter")
    dimensi = st.selectbox("Dimension:", ["Kelompok Besar", "Kelompok Sedang / Nama PJK"])

    kb_list = sorted(df["Kelompok Besar"].unique())
    ksnp_list = sorted(df["Kelompok Sedang / Nama PJK"].unique())

    filter_kb = st.selectbox("Kelompok Besar", ["(All)"] + kb_list)
    filter_ksnp = st.selectbox("Kelompok Sedang / Nama PJK", ["(All)"] + ksnp_list)

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
if filter_ksnp != "(All)":
    df_filtered = df_filtered[df_filtered["Kelompok Sedang / Nama PJK"] == filter_ksnp]

# === SI INSIGHT (CARD DENGAN BORDER) ===
st.subheader("SI Insight")

total = len(df_filtered)
if total == 0:
    st.warning("Tidak ada data tersedia pada filter saat ini.")
else:
    cr_avg = df_filtered["Completion Rate %"].mean()
    pita_merah = (df_filtered["Status Pita"] == "Pita Merah").sum()
    tidak_aktif = (df_filtered["StatusRegistrasi"] == "Tidak Aktif").sum()

    penugasan_cols = [col for col in df.columns if "Penugasan" in col or "Challenge" in col]
    melted = df_filtered.melt(id_vars=[dimensi], value_vars=penugasan_cols,
                              var_name="Tugas", value_name="Status").dropna()
    melted = melted[melted["Status"].isin(["Graded", "Ungraded"])]
    status_penugasan = melted.groupby("Status").size().to_dict()

    status_cols = df_filtered.columns[20:26]
    tugas_status = df_filtered[status_cols].melt(var_name="Tugas", value_name="Status").dropna()
    tugas_status["Status"] = tugas_status["Status"].str.strip().str.title()
    tugas_status = tugas_status[tugas_status["Status"].isin(["Completed", "Not Completed"])]
    status_counts = tugas_status[tugas_status["Status"] == "Not Completed"].groupby("Tugas").size()

    cr_df_full = df_filtered.groupby("Kelompok Sedang / Nama PJK")["Completion Rate %"].mean().reset_index()
    lowest_group = cr_df_full.sort_values("Completion Rate %").iloc[0] if not cr_df_full.empty else None

    cr_df = df_filtered.groupby(dimensi)["Completion Rate %"].mean().reset_index()

    sc1, sc2, sc3 = st.columns(3)

    with sc1:
        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h4>🎓 Ringkasan Maba</h4>
            <p><b>Jumlah Maba:</b> {total}</p>
            <p><b>Pita Merah:</b> {pita_merah}</p>
            <p><b>Completion Rate:</b> {cr_avg:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with sc2:
        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h4>📝 Status Penugasan</h4>
            <p><b>Graded:</b> {status_penugasan.get("Graded", 0)}</p>
            <p><b>Ungraded:</b> {status_penugasan.get("Ungraded", 0)}</p>
            <p><b>Tidak Aktif:</b> {tidak_aktif}</p>
        </div>
        """, unsafe_allow_html=True)

    with sc3:
        worst_tugas_html = ""
        if not status_counts.empty:
            worst_task = status_counts.idxmax()
            worst_count = status_counts.max()
            worst_tugas_html = f"<p><b>Tugas ❌:</b> {worst_task} ({worst_count} Not Completed)</p>"

        cr_terendah_html = ""
        if lowest_group is not None:
            group_label = lowest_group["Kelompok Sedang / Nama PJK"]
            rate = float(lowest_group["Completion Rate %"])
            cr_terendah_html = f"<p><b>Completion Rate Terendah:</b> {group_label} ({rate:.1f}%)</p>"

        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;">
            <h4>⚠️ Temuan Khusus</h4>
            {worst_tugas_html}
            {cr_terendah_html}
        </div>
        """, unsafe_allow_html=True)
