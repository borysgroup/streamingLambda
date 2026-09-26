# One camera, livestream + point-and-shoot: options A–C on real hardware

Hardware trial for [issue 9](https://github.com/borysgroup/streamingLambda/issues/9). It tests the three options from
[vertical-cloud-lab/streamingLambda#6](https://github.com/vertical-cloud-lab/streamingLambda/issues/6#issuecomment-5110582954),
each on its own tailnet stream camera. All three cameras are Pi Zero 2 W boards with a Camera Module 3 (imx708) and 415 MB RAM, running Debian 13.

| Option | What runs on the Pi | Still for decisions | Clip incl. moments *before* trigger |
|---|---|---|---|
| **A** | one picamera2 process: `main` 1536x864 for stills, `lores` 640x360 → HW H.264 → production ffmpeg, plus `CircularOutput` | HTTP `/snap` → `capture_file(name="main")` | `CircularOutput`, 10 s ring in RAM |
| **B** | `rpicam-vid → ffmpeg -c copy → MediaMTX` (on the Pi). MediaMTX runs the production ffmpeg leg and records 10 s fMP4 segments | any RTSP client grabs a frame | last completed recording segment |
| **C** | production `rpicam-vid \| ffmpeg`. After drawtext, `split` feeds the encoder (tee → flv + 10 s `.ts` segments) and a 2 fps `latest.jpg` | HTTP GET `latest.jpg` | last completed tee segment |

**Test conditions.** `device.service` was paused for about 3.5 min on each camera. The "YouTube" leg used the exact `device.py` encode
(`hflip,vflip,drawtext` → `libx264 -preset ultrafast` → flv at 640x360, 15 fps) but wrote to a local file, so no broadcasts were created.
Snapshots were requested from the GitHub runner over the tailnet. The service was restarted afterwards.

![results](results.png)

| | Baseline (`device.py`) | A | B | C |
|---|---|---|---|---|
| Mean CPU (4 cores) | 15.4 % | **22.4 %** | 16.5 % | 18.7 % |
| Throttling (`get_throttled`) | 0x0 | 0x0 | 0x0 | 0x0 |
| Stream leg | 15 fps | ran continuously (see note) | 3031 frames / ~206 s ≈ 14.7 fps | 3153 frames / 209.7 s ≈ 15.0 fps |
| Snapshot round-trip, median | – | 0.45 s (on-Pi capture 0.04 s) | 2.97 s (2.1 s with `-probesize 32768 -analyzeduration 0`) | **0.19 s** |
| Still resolution | – | **1536x864** (sensor mode) | 640x360 | 640x360, timestamp burned in |
| Clip | – | 179 frames (10 s pre + 2 s post) | 150 frames (10 s) | 150 frames (10 s) |

Raw numbers: [`data/`](data). Example stills: [`snapshots/`](snapshots). Scripts: [`scripts/`](scripts).

## Takeaways

- **All three work on a Pi Zero 2 W with the stream still running.** None of them throttled. So "one process owns the camera" is not a reason to need a
  second camera; it only rules out *separate* processes like `rpicam-vid` + `rpicam-still`.
- **C is the smallest change to `device.py`.** It keeps the `rpicam-vid | ffmpeg` shape and adds one `split` and one extra output. It was also the fastest to
  serve a still. Its stills are stream resolution, and they carry the timestamp overlay, which is useful for provenance.
- **A is the one that gives real "point-and-shoot" stills.** Its stills are 1536x864 while the stream stays at 640x360, and its clip includes the 10 s before
  the trigger. It costs about 7 points more CPU, and it means replacing the `rpicam-vid` subprocess with picamera2 (`apt install python3-picamera2`).
- **B puts the most on the Pi for the least gain.** Snapshots take about 2–3 s because each RTSP client connects and waits for a keyframe. It is the right shape
  only when a separate server does the relaying and analysis, not the Pi itself.

## Gotchas found

- A: the picamera2 still is **not flipped**. `device.py` applies `hflip,vflip` in ffmpeg, so A needs `Transform(hflip=1, vflip=1)` in the camera config.
- A: the flv from picamera2's H.264 reported ~6100 packets over 239 s. That points to ffmpeg guessing 25 fps on the raw pipe and `-vsync cfr` padding frames.
  Pass `-framerate 15` on the input.
- B: `runOnReady` is deprecated in MediaMTX v1.21 (use `runOnAvailable`). Also, the hook script must be executable, or MediaMTX silently never starts it.
- The tests wrote their files to `/tmp`, which is tmpfs (RAM). MemAvailable fell by about 80–110 MB over each run. For a long-running deployment, put
  segments/recordings on the SD card or cap them.
