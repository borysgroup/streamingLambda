source ~/buftest/common.sh; monitor & M=$!
(cd ~/buftest; exec ./mediamtx mediamtx.yml) > $OUT/mediamtx.log 2>&1 & X=$!
sleep 2
( "${RPICAM[@]}" --intra 15 2>/dev/null | ffmpeg -loglevel error -f h264 -i pipe:0 -c copy -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/cam ) > $OUT/app.log 2>&1 &
sleep ${DUR:-190}; pkill -x rpicam-vid; pkill -x ffmpeg; kill $X; sleep 1; kill $M; true
