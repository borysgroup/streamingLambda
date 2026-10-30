# live time per camera from YouTube broadcast history (device.py starts a new broadcast on every (re)start)
import pandas as pd, matplotlib.pyplot as plt
d = pd.read_csv("data/youtube_broadcasts.csv").dropna(subset=["start"])
d = d[d.end.notna() | (d.status == "live")]
for c in ["start", "end"]: d[c] = pd.to_datetime(d[c], utc=True).dt.tz_convert("America/Boise").dt.tz_localize(None)
d["end"] = d.end.fillna(d.start.max())
cams = sorted(d.cam.unique(), reverse=True)
fig, ax = plt.subplots(figsize=(11, 3.2), facecolor="#fcfcfb")
for y, cam in enumerate(cams):
    g = d[d.cam == cam].sort_values("start"); t, live = g.start.min(), 0.0
    for s, e in zip(g.start, g.end): live += max((e - max(s, t)).total_seconds(), 0); t = max(t, e)  # union, no double count
    up = live / (g.end.max() - g.start.min()).total_seconds()
    ax.broken_barh([(s, e - s) for s, e in zip(g.start, g.end)], (y - 0.35, 0.7), color="#2a78d6", lw=0)
    ax.text(1.005, y, f"{up:.1%} live", transform=ax.get_yaxis_transform(), va="center", color="#52514e")
ax.set_yticks(range(len(cams)), [c.replace("aurora-", "cam-") for c in cams]); ax.set_facecolor("#fcfcfb")
ax.set_title("YouTube live time per camera (gaps = not streaming)", loc="left", color="#0b0b0b")
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.tick_params(colors="#52514e"); fig.tight_layout(); fig.savefig("uptime_youtube.png", dpi=150)
