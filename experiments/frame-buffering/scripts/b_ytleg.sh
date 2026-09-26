#!/bin/bash
source ~/buftest/common.sh
exec ffmpeg -loglevel error -y "${AUDIO[@]}" -rtsp_transport tcp -i rtsp://127.0.0.1:8554/cam "${YT_ENC[@]}" -progress $OUT/progress.txt -f flv "$YT"
