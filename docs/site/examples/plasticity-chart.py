import hangtu as ht

lengths = ["ground_level", "depth", "elevation", "depth_top", "depth_base"]
atterberg = ht.read_csv(
    ht.examples.path("atterberg.csv"), units=dict.fromkeys(lengths, "ft")
)

# One PI in the example data is wrong on purpose, for the QC guide: use LL - PL.
atterberg = atterberg.drop(columns="plasticity_index")

fig, ax = ht.plot.plasticity_chart(atterberg, system="uscs")
fig.savefig("plasticity-chart.png")
