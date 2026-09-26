source ~/buftest/common.sh; monitor & M=$!
mkdir -p $OUT/seg
"${RPICAM[@]}" --intra 15 2>/dev/null | ffmpeg -loglevel error -y "${AUDIO[@]}" -thread_queue_size 1024 -use_wallclock_as_timestamps 1 -i pipe:0 \
  -filter_complex "[1:v]$VF,split=2[yt][snap]" \
  -map "[yt]" -map 0:a -c:v libx264 -preset ultrafast -g 30 -c:a aac -b:a 128k -async 1 -vsync cfr \
  -f tee "[f=flv:onfail=ignore]$OUT/yt_standin.flv|[f=segment:segment_time=10:segment_wrap=6:reset_timestamps=1]$OUT/seg/seg%02d.ts" \
  -map "[snap]" -r 2 -update 1 -q:v 4 $OUT/latest.jpg > $OUT/app.log 2>&1 &
( cd $OUT && python3 -m http.server 8081 --bind $TSIP > /dev/null 2>&1 ) & S=$!
sleep ${DUR:-190}; pkill -x rpicam-vid; pkill -x ffmpeg; kill $S; sleep 1; kill $M; true
