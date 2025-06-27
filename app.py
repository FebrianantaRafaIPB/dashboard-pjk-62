import streamlit as st
import pandas as pd
import altair as alt
from itertools import product

# === INSIGHT DAN CHARTS ===
st.subheader("SI Insight")
total = len(df_filtered)
if total == 0:
    st.warning("Tidak ada data tersedia pada filter saat ini.")
    st.stop()

cr_avg = df_filtered["Completion Rate %"].mean()
pita_merah = (df_filtered["Status Pita"] == "Pita Merah").sum()
tidak_aktif = (df_filtered["StatusRegistrasi"] == "Tidak Aktif").sum()

penugasan_cols = [col for col in df.columns if "Penugasan" in col or "Challenge" in col]
melted = df_filtered.melt(id_vars=[dimensi], value_vars=penugasan_cols,
                          var_name="Tugas", value_name="Status").dropna()
melted = melted[melted["Status"].isin(["Graded", "Ungraded"])]
status_penugasan = melted.groupby("Status").size().to_dict()

status_cols = df_filtered.columns[20:30]
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
    <div style='border:1px solid #ccc; border-radius:10px; padding:15px;'>
        <h4>🎓 Ringkasan Maba</h4>
        <p><b>Jumlah Maba:</b> {total}</p>
        <p><b>Pita Merah:</b> {pita_merah}</p>
        <p><b>Completion Rate:</b> {cr_avg:.1f}%</p>
    </div>""", unsafe_allow_html=True)

with sc2:
    st.markdown(f"""
    <div style='border:1px solid #ccc; border-radius:10px; padding:15px;'>
        <h4>📝 Status Penugasan</h4>
        <p><b>Graded:</b> {status_penugasan.get("Graded", 0)}</p>
        <p><b>Ungraded:</b> {status_penugasan.get("Ungraded", 0)}</p>
        <p><b>Tidak Aktif:</b> {tidak_aktif}</p>
    </div>""", unsafe_allow_html=True)

with sc3:
    cr_terendah_html = f"<p><b>Completion Rate Terendah:</b> {lowest_group['Kelompok Sedang / Nama PJK']} ({lowest_group['Completion Rate %']:.1f}%)</p>" if lowest_group is not None else ""
    worst_tugas_html = ""
    if not status_counts.empty:
        worst_task = status_counts.idxmax()
        worst_count = status_counts.max()
        worst_tugas_html = f"<p><b>Tugas ❌:</b> {worst_task} ({worst_count} Not Completed)</p>"
    st.markdown(f"""
    <div style='border:1px solid #ccc; border-radius:10px; padding:15px;'>
        <h4>⚠️ Temuan Khusus</h4>
        {worst_tugas_html}
        {cr_terendah_html}
    </div>""", unsafe_allow_html=True)

# === CHART: COMPLETION RATE ===
st.subheader(f"Completion Rate ({dimensi})")
chart_cr = alt.Chart(cr_df).mark_bar(color="#3498db").encode(
    y=alt.Y(dimensi, sort='-x', axis=alt.Axis(labelFontSize=10)),
    x=alt.X("Completion Rate %:Q", axis=alt.Axis(labelFontSize=10)),
    tooltip=[dimensi, "Completion Rate %"]
).properties(height=320)
st.altair_chart(chart_cr, use_container_width=True)

# === CHART: STATUS PER TUGAS ===
if perspektif == "PJK":
    st.subheader(f"Status per Tugas ({dimensi})")
    def wrap_label(text, width=30):
        return '\n'.join([text[i:i+width] for i in range(0, len(text), width)])

    tugas_status["Tugas"] = tugas_status["Tugas"].apply(lambda x: wrap_label(x, 30))
    status_tugas_df = tugas_status.groupby(["Tugas", "Status"]).size().reset_index(name="Count")
    all_index = pd.DataFrame(product(tugas_status["Tugas"].unique(), ["Completed", "Not Completed"]),
                             columns=["Tugas", "Status"])
    status_tugas_df = all_index.merge(status_tugas_df, on=["Tugas", "Status"], how="left").fillna(0)

    chart_status = alt.Chart(status_tugas_df).mark_bar().encode(
        x=alt.X("Tugas:N", sort=None, axis=alt.Axis(labelAngle=-20, labelFontSize=10)),
        y=alt.Y("Count:Q", title="Jumlah Mahasiswa"),
        color=alt.Color("Status:N", scale=alt.Scale(
            domain=["Completed", "Not Completed"],
            range=["#3498db", "#e74c3c"]
        )),
        tooltip=["Tugas", "Status", "Count"]
    ).properties(height=380)
    st.altair_chart(chart_status, use_container_width=True)

elif perspektif == "Panglima":
    st.subheader(f"Status Penugasan ({dimensi})")
    status_df = melted.groupby([dimensi, "Status"]).size().reset_index(name="Count")
    ordered_groups = status_df[dimensi].unique().tolist()

    chart_melted = alt.Chart(status_df).mark_bar().encode(
        y=alt.Y(dimensi, sort=ordered_groups, axis=alt.Axis(labelFontSize=10)),
        x=alt.X("Count:Q", stack="zero", axis=alt.Axis(labelFontSize=10)),
        color=alt.Color("Status:N", scale=alt.Scale(
            domain=["Graded", "Ungraded"],
            range=["#3498db", "#e74c3c"]
        )),
        tooltip=[dimensi, "Status", "Count"]
    ).properties(height=320)
    st.altair_chart(chart_melted, use_container_width=True)
