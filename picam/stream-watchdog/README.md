# RTMP stall watchdog

Restarts `device.service` when `ffmpeg` is alive but nothing is reaching YouTube (its RTMP push has hung). `Restart=always` never fires in that case, because no process exits.
It mirrors the watchdog on the vertical-cloud-lab cams (see `docs/ac-training-lab-picam-suggestions.md` in
vertical-cloud-lab/streamingLambda PR 2).

- Once a minute, it reads `bytes_acked` on the established `:1935` socket. After 3 checks with no progress, it restarts `device.service`, which ends the old broadcast and starts a new one.
- It skips the first 180 s after the service starts and does nothing while the service is stopped.
- It will not restart more than 6 times in any rolling 24 h (tracked in `/var/lib/stream-watchdog/restarts`). You can override this and set an optional `HEALTHCHECK_URL` in `/etc/default/stream-watchdog`.

Install (run from this directory on the Pi):

```bash
sudo install -m 755 stream-watchdog.sh /usr/local/bin/
sudo install -m 644 stream-watchdog.service stream-watchdog.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now stream-watchdog.timer
```

Logs: `journalctl -t stream-watchdog`. Stopping `device.service` is safe. If you run tests that leave it active but not streaming, stop the timer first.
