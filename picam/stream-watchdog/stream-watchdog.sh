#!/bin/bash
# RTMP stall watchdog (mirrors the vertical-cloud-lab picam watchdog).
# Restarts device.service when ffmpeg is alive but no data is reaching YouTube,
# i.e. bytes_acked on the :1935 socket stops advancing for STALL_CHECKS runs.
STALL_CHECKS=3
GRACE_SEC=180
MAX_RESTARTS_PER_DAY=6
HEALTHCHECK_URL=
[ -r /etc/default/stream-watchdog ] && . /etc/default/stream-watchdog

RUN=/run/stream-watchdog; LIB=/var/lib/stream-watchdog
mkdir -p "$RUN" "$LIB"
log() { logger -t stream-watchdog "$*"; }

systemctl is-active --quiet device.service || { rm -f "$RUN"/*; exit 0; }
started=$(systemctl show device.service -p ActiveEnterTimestampMonotonic --value)
now=$(awk '{printf "%d", $1 * 1000000}' /proc/uptime)
if (( (now - started) / 1000000 < GRACE_SEC )); then rm -f "$RUN"/*; exit 0; fi

acked=$(ss -Htin state established '( dport = :1935 )' | grep -o 'bytes_acked:[0-9]*' | cut -d: -f2 | sort -n | tail -1)
last=$(cat "$RUN/last" 2>/dev/null)
misses=$(cat "$RUN/misses" 2>/dev/null || echo 0)

# Progress = bytes moved, or a lower count (new socket after a reconnect)
if [ -n "$acked" ] && [ "$acked" != "$last" ]; then
  echo "$acked" > "$RUN/last"; echo 0 > "$RUN/misses"
  [ -n "$HEALTHCHECK_URL" ] && curl -fsS -m 10 --retry 3 -o /dev/null "$HEALTHCHECK_URL"
  exit 0
fi

misses=$((misses + 1)); echo "$misses" > "$RUN/misses"
log "no RTMP progress (bytes_acked=${acked:-none}), miss $misses/$STALL_CHECKS"
(( misses < STALL_CHECKS )) && exit 0

cutoff=$(( $(date +%s) - 86400 ))
awk -v c="$cutoff" '$1 >= c' "$LIB/restarts" 2>/dev/null > "$LIB/restarts.tmp"; mv "$LIB/restarts.tmp" "$LIB/restarts"
if (( $(wc -l < "$LIB/restarts") >= MAX_RESTARTS_PER_DAY )); then
  log "restart budget exhausted ($MAX_RESTARTS_PER_DAY/24h), holding off"
  exit 0
fi
date +%s >> "$LIB/restarts"; rm -f "$RUN"/*
log "RTMP stalled for $STALL_CHECKS checks, restarting device.service"
systemctl restart device.service
