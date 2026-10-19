"""Draw order of plot marks, bottom to top (P01 §7, P04 §7, P05 §7, P07 §7).

Gridlines sit below everything else (``axes.axisbelow``, zorder 0.5).
"""

ENVELOPES = 0.4  # P05 envelopes, under the gridlines
STRATA = 1.0
REGIONS = 1.05  # P04 user regions
RANGES = 1.1
ZONES = 1.15  # P04 CL-ML hatch
LINES = 1.2  # reference and design lines
CHART_LINES = 1.2  # P04 A-line, U-line, dividers and PI = LL
DIVIDERS = 1.2  # P05 fraction and part boundaries
ZONE_LABELS = 1.3  # P04 zone, line and band labels
WATER_LEVEL = 1.3
BASELINE = 1.4  # P07 baseline bars
INTERVALS = 2.0
CONNECT = 2.1
MARKERS = 2.5
QUALIFIERS = 2.6
SUMMARY = 2.7  # P07 summary bars and boxes, over the points
CENTRAL = 2.8  # P07 central markers
D_VALUES = 2.9  # P05 D-value leaders and ticks
EDGE = 3.0  # out-of-range markers, from edge_markers()
ANNOTATIONS = 4.0
