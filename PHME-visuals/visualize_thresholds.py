"""
RSSH Grant Threshold Compliance Visualizer
Reads all grant data from MOZ data_test.xlsx, prompts user to select a grant,
then generates a two-panel bar chart ($ amount and % share).
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import matplotlib as mpl

mpl.rcParams["font.family"] = "Arial"

# ── Column map ─────────────────────────────────────────────────────────────────
AREAS = ["HRH-CHW", "HPM", "M&E+EWS", "Labs", "CRSS", "HFS"]

COL_ACTUAL_USD = ["HRH-CHW $", "HPM $", "M&E+EWS $", "Labs $", "CRSS $", "HFS $"]
COL_ACTUAL_PCT = ["HRH-CHW %", "HPM %", "M&E+EWS %", "Labs %", "CRSS %", "HFS %"]
COL_THRESH_USD = [
    "HRH-CHW threshold $",
    "HPM\nthreshold ($)",
    "M&E+EWS threshold ($)",
    "Labs \nthreshold ($)",
    "CRSS\nthreshold ($)",
    "HFS\nthreshold ($)",
]
COL_THRESH_PCT = [
    "HRH-CHW threshold ($)",   # actual % threshold column (0.1 = 10 %)
    "HPM\nthreshold (%)",
    "M&E+EWS threshold (%)",
    "Labs \nthreshold (%)",
    "CRSS\nthreshold (%)",
    "HFS\nthreshold (%)",
]

# ── Load data ──────────────────────────────────────────────────────────────────
EXCEL_FILE = "Complete dataset.xlsx"

try:
    df = pd.read_excel(EXCEL_FILE)
except FileNotFoundError:
    sys.exit(f"❌  Could not find '{EXCEL_FILE}'. Make sure it is in the same folder.")

grants = df["Grant"].tolist()

# ── Grant selection ────────────────────────────────────────────────────────────
print("\nAvailable grants:")
for i, g in enumerate(grants, 1):
    print(f"  {i:>2}. {g}")

while True:
    raw = input("\nEnter grant number: ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(grants):
        chosen_idx = int(raw) - 1
        break
    print(f"   Please enter a number between 1 and {len(grants)}.")

row        = df.iloc[chosen_idx]
grant_name = row["Grant"]

actual_usd = [float(row[c]) for c in COL_ACTUAL_USD]
actual_pct = [float(row[c]) * 100 for c in COL_ACTUAL_PCT]   # stored as 0.xx → convert to %
thresh_usd = [float(row[c]) for c in COL_THRESH_USD]
thresh_pct = [float(row[c]) * 100 for c in COL_THRESH_PCT]   # same conversion

print(f"\n✔  Selected: {grant_name}")

# ── Compliance flags (per panel independently) ────────────────────────────────
met_usd = [a >= t for a, t in zip(actual_usd, thresh_usd)]
met_pct = [a >= t for a, t in zip(actual_pct, thresh_pct)]

# ── Palette ───────────────────────────────────────────────────────────────────
CLR_MET    = "#2ECC71"
CLR_MISS   = "#E74C3C"
CLR_THRESH = "#2C3E50"

x     = np.arange(len(AREAS))
bar_w = 0.55

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 6), facecolor="white")
fig.patch.set_facecolor("white")

# ── Axis style ────────────────────────────────────────────────────────────────
def style_ax(ax):
    ax.set_facecolor("white")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(colors="#444444", labelsize=12)
    ax.yaxis.set_tick_params(length=0)
    ax.set_yticks([])
    ax.set_axisbelow(True)

# ── Threshold line + label (suppressed when too close; clamped when off-chart) ─
CLOSE_RATIO  = 0.15   # hide label if |actual − threshold| / threshold < this
OFFCHART_CAP = 1.10   # if threshold > max_actual × this, show as off-chart

def draw_threshold(ax, i, thresh_axis, actual_axis, label, ylim_top=1, max_actual=None):
    """
    Draw the dotted threshold line.
    - If thresh_axis > max_actual * OFFCHART_CAP the threshold is way above the
      visible bars: draw a short stub at the top with an upward-arrow label.
    - Otherwise draw it normally and add the value label unless too close.
    """
    if max_actual is None:
        max_actual = ylim_top

    if thresh_axis > max_actual * OFFCHART_CAP:
        # Off-chart: stub at top of plot area + arrow label
        stub_y = ylim_top * 0.97
        ax.plot([i - bar_w / 2, i + bar_w / 2],
                [stub_y, stub_y],
                color=CLR_THRESH, linewidth=2.0,
                linestyle=(0, (4, 3)), zorder=4, alpha=0.7)
        ax.text(i + bar_w / 2 + 0.06, stub_y, f"↑ {label}",
                ha="left", va="center", fontsize=9,
                color=CLR_THRESH, fontweight="bold", fontfamily="Arial")
        return

    ax.plot([i - bar_w / 2, i + bar_w / 2],
            [thresh_axis, thresh_axis],
            color=CLR_THRESH, linewidth=2.2,
            linestyle=(0, (4, 3)), zorder=4)

    # Use ylim_top to determine if the label overlaps with the actual bar label.
    # The actual label is drawn at: actual_axis + ylim_top * 0.015
    # The threshold label is drawn at: thresh_axis
    # Check if the absolute difference is less than a certain fraction of the total chart height
    dynamic_close_margin = ylim_top * 0.06 # Minimum 6% of total chart height between labels
    close = abs(actual_axis + ylim_top * 0.015 - thresh_axis) < dynamic_close_margin
    
    # Also check if actual is simply very close to threshold in general
    close = close or (abs(actual_axis - thresh_axis) / (thresh_axis if thresh_axis else 1) < CLOSE_RATIO)
    
    if not close:
        ax.text(i + bar_w / 2 + 0.06, thresh_axis, label,
                ha="left", va="center", fontsize=10,
                color=CLR_THRESH, fontweight="bold", fontfamily="Arial")

# ══════════════════════════════════════════════════════════════════════════════
# Panel 1 — Budget Amount
# ══════════════════════════════════════════════════════════════════════════════
usd_vals    = [v / 1e6 for v in actual_usd]
max_usd     = max(usd_vals) if max(usd_vals) > 0 else 1
ylim1       = max_usd * 1.18

bars1 = ax1.bar(x, usd_vals, width=bar_w,
                color=[CLR_MET if m else CLR_MISS for m in met_usd],
                edgecolor="white", linewidth=1.2, zorder=3)

for i, (t, a) in enumerate(zip(thresh_usd, actual_usd)):
    draw_threshold(ax1, i, t / 1e6, a / 1e6,
                   label=f"{t/1e6:.0f}M", ylim_top=ylim1, max_actual=max_usd)

for bar, val in zip(bars1, actual_usd):
    ax1.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + ylim1 * 0.015,
             f"{val/1e6:.1f}M",
             ha="center", va="bottom", fontsize=12,
             color="#333333", fontweight="bold", fontfamily="Arial")

style_ax(ax1)
ax1.set_xticks(x)
ax1.set_xticklabels(AREAS, fontsize=11, color="#333333", fontweight="bold",
                    fontfamily="Arial", rotation=33, ha="right")
ax1.set_title("Budget Amount (US$ millions)", fontsize=14, fontweight="bold",
              color="#1a1a1a", pad=6, fontfamily="Arial")
ax1.set_ylim(0, ylim1)

# ══════════════════════════════════════════════════════════════════════════════
# Panel 2 — Share of Total Grant Budget
# ══════════════════════════════════════════════════════════════════════════════
max_pct = max(actual_pct) if max(actual_pct) > 0 else 1
ylim2   = max_pct * 1.18

bars2 = ax2.bar(x, actual_pct, width=bar_w,
                color=[CLR_MET if m else CLR_MISS for m in met_pct],
                edgecolor="white", linewidth=1.2, zorder=3)

for i, (t, a) in enumerate(zip(thresh_pct, actual_pct)):
    draw_threshold(ax2, i, t, a,
                   label=f"{t:.0f}%", ylim_top=ylim2, max_actual=max_pct)

for bar, val in zip(bars2, actual_pct):
    ax2.text(bar.get_x() + bar.get_width() / 2,
             bar.get_height() + ylim2 * 0.015,
             f"{val:.1f}%",
             ha="center", va="bottom", fontsize=12,
             color="#333333", fontweight="bold", fontfamily="Arial")

style_ax(ax2)
ax2.set_xticks(x)
ax2.set_xticklabels(AREAS, fontsize=11, color="#333333", fontweight="bold",
                    fontfamily="Arial", rotation=33, ha="right")
ax2.set_title("Share of Total Grant Budget (%)", fontsize=14, fontweight="bold",
              color="#1a1a1a", pad=6, fontfamily="Arial")
ax2.set_ylim(0, ylim2)

# ── Shared legend ─────────────────────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(facecolor=CLR_MET,  edgecolor="none", label="Threshold met"),
    mpatches.Patch(facecolor=CLR_MISS, edgecolor="none", label="Threshold not met"),
    plt.Line2D([0], [0], color=CLR_THRESH, linewidth=2,
               linestyle=(0, (4, 3)), label="Threshold"),
]
fig.legend(handles=legend_handles, loc="lower center", ncol=3,
           frameon=False, bbox_to_anchor=(0.5, -0.04),
           prop={"family": "Arial", "size": 12})

plt.subplots_adjust(left=0.06, right=0.97, top=0.91, bottom=0.14,
                    wspace=0.30, hspace=0.0)

out_file = f"{grant_name}_threshold_compliance.png"
plt.savefig(out_file, dpi=200, facecolor="white", edgecolor="none")
print(f"✅  Saved: {out_file}  (1800×1200 px)")