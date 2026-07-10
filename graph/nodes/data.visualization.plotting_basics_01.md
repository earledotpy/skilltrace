---
id: data.visualization.plotting_basics_01
title: Produce a clear, labeled plot
summary: Build a readable chart with titles, axis labels, and units.
domain: data
track: foundational
estimated_effort:
  min_minutes: 30
  max_minutes: 90
micro_session_fit:
  can_fit_15_min: false
  can_fit_30_min: true
  requires_long_block: false
tags:
- data
- visualization
- matplotlib
created_at: 2026-07-06
updated_at: 2026-07-06
---

# Produce a clear, labeled plot

## Learning target

Turn a small dataset into a chart a reader can understand without your help: a
descriptive title, labeled axes with units, a legend when there is more than one
series, and a sensible scale. The evidence is a plot you produced (with the code
that made it) plus a sentence on what it shows.

## Study pointers

The Matplotlib "Quick start" and "Pyplot tutorial" (matplotlib.org/stable) for
building a figure and setting title, `xlabel`/`ylabel`, and legend; Claus Wilke's
"Fundamentals of Data Visualization" (clauswilke.com/dataviz) chapters on axes
and labeling for what makes a chart readable.

## Notes

Manual-gated: producing a figure is mechanical, but "is this chart clear and
correctly labeled?" is a judgment, so the gate reads the plot and its code rather
than exit-checking that a file was written (which would be the proxy the honesty
rule forbids).
