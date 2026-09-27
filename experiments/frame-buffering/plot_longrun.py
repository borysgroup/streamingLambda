# 8 h option A run on cam-y5hk (data/longrun2_*.csv -> longrun2.png)
import pandas as pd, matplotlib.pyplot as plt, matplotlib.dates as md
A, INK, INK2, GRID, BG = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
d = pd.read_csv("data/longrun2_option_a_y5hk.csv"); d["t"] = pd.to_datetime("2026-09-26 " + d.time)
d["fps"] = d.frame.diff() / d.t.diff().dt.total_seconds()
yt = pd.read_csv("data/longrun2_youtube_archive.csv")
fig, ax = plt.subplots(2, 3, figsize=(13, 6), facecolor=BG)
panels = [("fps", "Frames sent to YouTube (fps, per minute)", (0, 20), 15, "target 15 fps"),
          ("snap_s", "Still capture on the Pi (s), every 5 min", (0, 0.2), None, ""),
          ("cpu_pct", "CPU (%, 4 cores)", (0, 30), 15.4, "production baseline"),
          ("memavail_mb", "Free memory (MemAvailable, MB)", (0, 250), 172, "production after 8 h"),
          ("temp_c", "SoC temperature (°C), never throttled", (0, 80), None, "")]
for a, (col, title, ylim, ref, lab) in zip(ax.flat, panels):
    s = d.dropna(subset=[col])
    (a.scatter if col == "snap_s" else a.plot)(s.t, s[col], color=A, **({"s": 10} if col == "snap_s" else {"lw": 1.5}))
    if ref: a.axhline(ref, color=INK2, lw=1, ls="--"); lo = col == "cpu_pct"; a.text(d.t.iloc[5], ref, f"\n{lab}" if lo else f"{lab}\n", color=INK2, fontsize=8, va="top" if lo else "bottom")
    a.set(ylim=ylim, title=title); a.xaxis.set_major_formatter(md.DateFormatter("%H:%M"))
b = ax[1, 2]
b.barh(yt.cam, yt.archived_s / 3600, color=[A if w == "option A" else "#b7b5ae" for w in yt.sent_by], height=0.6)
for y, (h, w) in enumerate(zip(yt.archived_s / 3600, yt.sent_by)): b.text(h + 0.1, y, f"{int(h)}h{round(h % 1 * 60):02d}m  {w}", va="center", fontsize=8, color=INK)
b.set(xlim=(0, 11), title="YouTube archive, 05:00–13:00 broadcast (h)"); b.invert_yaxis()
for a in ax.flat:
    a.set_facecolor(BG); a.grid(axis="y" if a is not b else "x", color=GRID); a.set_axisbelow(True); a.title.set_fontsize(10)
    a.tick_params(colors=INK2, labelsize=8); [a.spines[k].set_visible(False) for k in ("top", "right")]
fig.suptitle("Option A (picamera2) live to YouTube for 8 h on cam-y5hk, 26 Sep 05:02–13:00 MDT: 0 restarts", x=0.01, ha="left", color=INK)
fig.tight_layout(); fig.savefig("longrun2.png", dpi=130)
