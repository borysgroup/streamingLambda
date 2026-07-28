# RPi streaming camera setup (cams No. 0–5)

State of a fully set-up camera, as verified end-to-end on cam No. 0 on 2026-07-28.
Cameras are Raspberry Pi Zero 2 W (Debian 13 trixie) with Camera Module 3 (IMX708),
following the picam setup from
[ac-training-lab `src/ac_training_lab/picam/`](https://github.com/AccelerationConsortium/ac-training-lab/tree/main/src/ac_training_lab/picam).

## On-device components

1. `~/ac-training-lab` cloned (branch `main`); the picam code lives in
   `src/ac_training_lab/picam/`.
2. `my_secrets.py` in that directory (mode 600), defining `AUTH_BASE_URL`,
   `LAMBDA_TOKEN`, `LAMBDA_FUNCTION_URL`, `CAM_NAME`, `WORKFLOW_NAME` (unique per
   camera), `PRIVACY_STATUS`, `CAMERA_VFLIP`, `CAMERA_HFLIP`.
3. `/etc/systemd/system/device.service` (enabled) running `device.py` with the
   system `python3` (deps: apt `python3-picamera2`, `ffmpeg`, `python3-requests`) and
   `PICAM_WIDTH`/`PICAM_HEIGHT`/`PICAM_FPS` environment overrides.
4. Root crontab entry for 8-hour YouTube chunking (device local time):

   ```cron
   0 5,13,21 * * * /sbin/shutdown -r now
   ```

   Each reboot makes `device.py` call the Lambda `end` (finalizes the previous
   broadcast as its own video) then `create` (fresh broadcast + stream key).

## Verification procedure

- `systemctl is-active device.service` → `active`, `NRestarts=0`.
- `journalctl -u device.service -b` shows Lambda `end` → 200, `create` → 200,
  then `Stream started`.
- Exactly one `rpicam-vid` and one `ffmpeg` process; `ss -tn` shows an
  established connection to RTMP (port 1935).
- Reboot once and confirm the stream comes back on its own with a new stream id.

## Known quirks

- `device.py` on ac-training-lab `main` also polls a `status` action, which the
  Lambda deployed from this repo does not implement (`app.py` accepts only
  `create`/`end`), so a handful of harmless 400s appear at startup. Either add a
  `status` action to the Lambda or ignore them.
