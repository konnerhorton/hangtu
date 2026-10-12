"""Draw order of plot marks, bottom to top (P01 §7, P07 §7).

Gridlines sit below everything (``axes.axisbelow``).
"""

STRATA = 1.0
RANGES = 1.1
LINES = 1.2  # reference and design lines
WATER_LEVEL = 1.3
BASELINE = 1.4  # P07 baseline bars
INTERVALS = 2.0
CONNECT = 2.1
MARKERS = 2.5
QUALIFIERS = 2.6
SUMMARY = 2.7  # P07 summary bars and boxes, over the points
CENTRAL = 2.8  # P07 central markers
EDGE = 3.0  # out-of-range markers, from edge_markers()
ANNOTATIONS = 4.0
