"""Total stream hours and archive size on Aurora PCL Hardware Streams, per camera.

Usage: python scripts/stream_totals.py
Needs: google-auth>=2.59 and requests, plus YOUTUBE_UPLOAD_TOKEN_PICKLE_B64 in the
environment (only read calls are made). Never prints token material.

Columns:
- broadcast h: actualStartTime to actualEndTime (or now, if live). Includes stretches
  where a camera dropped out but its broadcast stayed open (enableAutoStop is off).
- recorded h: the archive's duration (contentDetails.duration), i.e. video YouTube
  actually received. Archives still processing report the broadcast span instead.
- YouTube GB: sum of fileDetails.fileSize, the size of YouTube's re-encoded archive. The
  cameras upload several times more than this. Archives still processing and live
  broadcasts have no size yet.
"""

import base64
import os
import pickle
import re
from collections import defaultdict
from datetime import datetime, timezone

from google.auth.transport.requests import AuthorizedSession, Request

API = "https://www.googleapis.com/youtube/v3/"


def get_all(session, path, **params):
    items = []
    while True:
        r = session.get(API + path, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        items += data.get("items", [])
        if "nextPageToken" not in data:
            return items
        params["pageToken"] = data["nextPageToken"]


def seconds(duration):  # ISO 8601, e.g. P6DT7H43M52S
    d, h, m, s = (int(g or 0) for g in re.fullmatch(
        r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", duration).groups())
    return ((d * 24 + h) * 60 + m) * 60 + s


def ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    creds = pickle.loads(base64.b64decode(os.environ["YOUTUBE_UPLOAD_TOKEN_PICKLE_B64"]))
    creds.refresh(Request())
    session = AuthorizedSession(creds)
    now = datetime.now(timezone.utc)

    ids = [b["id"] for status in ("completed", "active") for b in get_all(
        session, "liveBroadcasts", part="id", broadcastStatus=status,
        broadcastType="all", maxResults=50)]
    videos = []
    for i in range(0, len(ids), 50):
        videos += get_all(session, "videos", id=",".join(ids[i:i + 50]),
                          part="snippet,contentDetails,liveStreamingDetails,fileDetails")

    cams = defaultdict(lambda: defaultdict(float))
    for v in videos:
        live = v["liveStreamingDetails"]
        if "actualStartTime" not in live:
            continue
        start = ts(live["actualStartTime"])
        end = ts(live["actualEndTime"]) if "actualEndTime" in live else now
        span = (end - start).total_seconds()
        cam = cams[v["snippet"]["title"].rsplit(" stream ", 1)[-1].split(",")[0]]
        cam["broadcasts"] += 1
        cam["live"] += "actualEndTime" not in live
        cam["broadcast_h"] += span / 3600
        cam["recorded_h"] += (seconds(v["contentDetails"]["duration"]) or span) / 3600
        cam["gb"] += int(v["fileDetails"].get("fileSize", 0)) / 1e9
        cam["no_size"] += "fileSize" not in v["fileDetails"]
        cam["first"] = min(cam["first"] or start.timestamp(), start.timestamp())

    cams["**Total**"] = {k: sum(c[k] for c in list(cams.values())) for k in
                         ("broadcasts", "live", "broadcast_h", "recorded_h", "gb", "no_size")}
    cams["**Total**"]["first"] = min(c["first"] for n, c in cams.items() if n != "**Total**")
    print(f"As of {now:%Y-%m-%d %H:%M} UTC\n")
    print("| camera | first stream | broadcasts (live now) | broadcast h | recorded h "
          "| YouTube GB (videos without a size) |")
    print("| --- | --- | --- | ---: | ---: | ---: |")
    for name, c in sorted(cams.items(), key=lambda kv: (kv[0].startswith("**"), kv[0])):
        first = datetime.fromtimestamp(c["first"], timezone.utc).date()
        print(f"| {name} | {first} | {c['broadcasts']:.0f} ({c['live']:.0f}) "
              f"| {c['broadcast_h']:,.0f} | {c['recorded_h']:,.0f} "
              f"| {c['gb']:,.1f} ({c['no_size']:.0f}) |")


if __name__ == "__main__":
    main()
