# === CHART 3: Status Per Tugas (Plotly) ===
st.subheader("📌 Status Completion Per Tugas")

status_cols = df_filtered.columns[20:26]
tugas_status = df_filtered[status_cols].melt(
    var_name="Tugas", value_name="Status").dropna()
tugas_status["Status"] = tugas_status["Status"].str.strip().str.title()
tugas_status = tugas_status[tugas_status["Status"].isin(["Completed", "Not Completed"])]

status_tugas_df = tugas_status.groupby(["Tugas", "Status"]).size().reset_index(name="Count")
all_tugas = tugas_status["Tugas"].unique()
full_index = pd.DataFrame(product(all_tugas, ["Completed", "Not Completed"]),
                          columns=["Tugas", "Status"])
status_tugas_df = full_index.merge(status_tugas_df, on=["Tugas", "Status"], how="left").fillna(0)

def wrap_label(text, width=30):
    return '\n'.join([text[i:i+width] for i in range(0, len(text), width)])
status_tugas_df["Tugas"] = status_tugas_df["Tugas"].apply(lambda x: wrap_label(x, width=30))

status_tugas_df = status_tugas_df.sort_values(
    by=["Tugas", "Status"],
    key=lambda col: col.map({"Completed": 0, "Not Completed": 1})
)

fig = px.bar(
    status_tugas_df,
    x="Tugas",
    y="Count",
    color="Status",
    color_discrete_map={
        "Completed": "#3498db",
        "Not Completed": "#e74c3c"
    },
    barmode="stack",
    labels={"Count": "Jumlah Mahasiswa"},
    width=900,
    height=380
)

fig.update_layout(
    xaxis_tickangle=-20,
    xaxis_title=None,
    yaxis_title="Jumlah Mahasiswa",
    legend_title=None,
    margin=dict(t=10, b=100),
    font=dict(size=10)
)

st.plotly_chart(fig, use_container_width=False)
