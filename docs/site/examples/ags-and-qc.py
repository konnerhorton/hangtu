import hangtu as ht

p = ht.Project.from_ags(
    ht.examples.path("site.ags"), db="site.sqlite", vertical_datum="NAVD88"
)
report = p.qc()
print(report)
report.to_csv("qc_report.csv")  # every finding, with its hole, depth and line

changes = p.diff("ISPT", changed_only=True)  # what ingest did to each SPT value
print(changes["change"].value_counts())
