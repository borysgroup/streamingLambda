"""Plot CPU use and snapshot round-trip time for options A-C (data/ -> results.png; `plot.py youtube` -> results_youtube.png)."""
import csv, statistics, sys
import matplotlib.pyplot as plt

COL = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
NAME = {"A": "A · picamera2 main+lores", "B": "B · MediaMTX relay", "C": "C · ffmpeg tee"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

def rows(p): return list(csv.DictReader(open(p)))
SFX = "_" + sys.argv[1] if len(sys.argv) > 1 else ""

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.6, 1]})
fig.patch.set_facecolor("#fcfcfb")
base = [int(r["cpu_pct"]) for k in "abc" for r in rows(f"data/monitor_baseline_cam_{k}.csv")]
ax1.axhline(statistics.mean(base), color=INK2, lw=1.5, ls="--")
ax1.text(3, statistics.mean(base) - 1.8, "production baseline (device.py)", color=INK2, fontsize=9)
for k in "ABC":
    r = rows(f"data/monitor_option_{k.lower()}{SFX}.csv")
    ax1.plot([int(x["t"]) for x in r], [int(x["cpu_pct"]) for x in r], color=COL[k], lw=2)
    ax1.text(int(r[-1]["t"]), int(r[-1]["cpu_pct"]), f"  {k}", color=INK, va="center", fontsize=10, fontweight="bold")
ax1.set(xlabel="seconds into run", ylabel="total CPU (%, 4 cores)", ylim=(0, 40), xlim=(0, max(int(x["t"]) for k in "abc" for x in rows(f"data/monitor_option_{k}{SFX}.csv")) * 1.08),
        title="Pi Zero 2 W CPU while streaming + buffering" + (" (live to YouTube)" if SFX else ""))

snap = rows(f"data/snapshots{SFX}.csv")
for i, k in enumerate("ABC"):
    v = [float(r["wall_s"]) for r in snap if r["option"] == k and r["n"] != "clip" and "probesize" not in r["note"]]
    ax2.bar(i, statistics.median(v), color=COL[k], width=0.6)
    ax2.scatter([i] * len(v), v, color=INK, s=10, zorder=3)
    ax2.text(i, statistics.median(v) + 0.12, f"{statistics.median(v):.2f} s", ha="center", color=INK, fontsize=9)
    ax2.text(i, -0.35, NAME[k].split(" · ")[1], ha="center", color=INK2, fontsize=8)
ax2.set_xticks(range(3), [k for k in "ABC"], fontsize=8.5)
ax2.set_ylim(0, 3.6); ax2.set(ylabel="seconds (runner → Pi over tailnet)", title="Snapshot round-trip, median + each call")
for a in (ax1, ax2):
    a.set_facecolor("#fcfcfb"); a.grid(axis="y", color=GRID); a.set_axisbelow(True)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    a.title.set_fontsize(11)
fig.tight_layout(); fig.savefig(f"results{SFX}.png", dpi=130)
