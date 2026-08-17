---
name: quant-figures
description: HFT/quant research-desk figure quality spec (Jane Street standard). Use whenever producing charts, plots, or figures from data - matplotlib/seaborn or otherwise - for a research note or analysis. Enforces restraint, statistical rigor (CIs, distributions, log scales), finding-first titles, and a two-pass critique before saving.
---

# Figure Quality Spec (Jane Street / HFT research desk standard)

Every figure must pass this spec before it is saved. No exceptions.

## Design philosophy

You are producing figures for an internal research note at a top HFT firm. The reader is a senior quant with 10 seconds per chart. Every pixel must earn its place. Restraint over decoration. Density over emptiness. Findings over descriptions. A chart that merely displays data has failed. A chart must argue a point.

## Hard style contract

- Stack: matplotlib + seaborn. `seaborn.set_theme(style="ticks")`, then `sns.despine()` top and right.
- Figure: figsize (10, 5.5) single panel, (12, 7) for 2x2 grids. dpi 200. `constrained_layout=True`.
- Fonts: sans-serif (Helvetica/Arial/DejaVu Sans). Title 11pt regular weight, axes 10pt, ticks 9pt, footnote 8pt gray.
- Palette: maximum 4 series colors, colorblind safe. Primary `#1f3b73` (deep navy), accent `#c44e52` (muted red) reserved only for the series the title is about. All context/comparison series in `#9a9a9a` gray at alpha 0.6.
- Gridlines: horizontal only, `#e0e0e0`, linewidth 0.5, zorder behind data.
- Lines: linewidth 1.2. Markers only if n < 50 points, size 3.
- No legends when 3 or fewer series. Direct-label each line at its right endpoint in the series color.
- Axis labels always include units: "Tip (SOL, log scale)", "Landing rate (%)", "Latency (ms, p99)".
- Number formatting: thousands separators, SI suffixes for large counts (48.2k not 48231), percentages to 1 decimal.
- Y axis starts at zero for bar/area charts. Truncated axes allowed for line charts only if a break annotation is shown.

## Statistical requirements

- Never plot a bare mean. Every point estimate carries a 95% CI, bootstrapped (n=10,000 resamples) unless a closed form exists. CIs drawn as bands (alpha 0.15) for lines, thin caps for points.
- Distributions: ECDF or letter-value plot. Bar charts of means over skewed data are forbidden.
- Skewed positive data (tips, fees, latency): log scale, state it in the axis label.
- Reference lines for p50, p90, p99 where percentiles matter, dashed gray, labeled inline.
- Time series: raw data as scatter at alpha 0.08 underneath, rolling median (state the window) on top. Never a smoothed line alone.
- Regression or fit lines must print the fit statistic on the chart (R2, slope with SE) or be removed.
- Every subgroup comparison states n per group on the chart.
- Winsorize or flag outliers explicitly. Silent clipping is forbidden.

## Title and annotation rules

- Titles state the finding, not the variables. Include the sample size.
  - Bad: "Tip amount vs landing rate"
  - Good: "Tips above 0.001 SOL buy no marginal landing improvement (n=48.2k txs)"
- One annotation per chart calling out the single most decision-relevant feature, thin arrow or bracket, 9pt.
- Footnote block, bottom left, 8pt gray, three lines max: data source and API, date range and filters, methodology note (e.g. "CIs: 10k bootstrap resamples, tx-level").

## Forbidden

Pie charts. Dual y-axes. 3D. Stacked areas with more than 3 categories. Default matplotlib blue/orange. Rainbow palettes. Drop shadows. Bold titles. Chart borders. Legends floating over data. Rotated x tick labels beyond 30 degrees (aggregate or flip the axis instead). Emoji. Titles that describe axes instead of findings.

## Two-pass review (mandatory)

After rendering each figure, run this critique before saving:
1. Would a reviewer at a quant fund flag anything? Check: misleading axis, missing n, missing units, missing uncertainty, chartjunk, unlabeled log scale, mean over skewed data.
2. Cover the title. Can the finding be recovered from the chart alone in 10 seconds? If not, add the annotation or simplify.
3. Cover the chart. Does the title alone state something falsifiable with a number in it? If not, rewrite the title.
4. Print the critique as a comment in the code, then regenerate the corrected figure. Save only the corrected version.

## Output

- Save as PNG at dpi 200 and PDF (vector) side by side: `fig_<nn>_<slug>.png/.pdf`.
- Emit a one-line caption per figure into `figures_manifest.md`: filename, finding, n, date range.
