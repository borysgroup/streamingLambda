# option A to YouTube until the next cron reboot, restarted on stall/exit like device.py restarts ffmpeg; 1/min frame count, 1 still per 5 min
source ~/buftest/common.sh; L=~/buftest/longrun2; mkdir -p $L; monitor & M=$!
start() { rm -f $OUT/progress.txt; python3 ~/buftest/option_a.py $OUT $TSIP "${VF#hflip,vflip,}" "$YT" >> $L/app.log 2>&1 & A=$!; last=0; }
echo "time,restarts,frame,snap_s,cpu_pct,temp_c,throttled,memavail_mb" > $L/frames.csv; r=0; n=0; start
while sleep 60; do
  n=$((n+1)); f=$(grep -o "^frame=[0-9]*" $OUT/progress.txt 2>/dev/null | tail -1 | cut -d= -f2); s=
  [ $((n % 5)) = 0 ] && s=$(curl -s -o /dev/null -w "%{time_total}" --max-time 20 http://$TSIP:8081/snap)
  echo "$(date +%T),$r,${f:-0},$s,$(tail -1 $OUT/monitor.csv | cut -d, -f2,4-6)" >> $L/frames.csv
  if ! kill -0 $A 2>/dev/null || [ "${f:-0}" -le "$last" ]; then
    echo "$(date +%T) restart (frame=${f:-0})" >> $L/app.log
    kill $A 2>/dev/null; sleep 3; kill -9 $A 2>/dev/null; pkill -x ffmpeg; sleep 10; r=$((r+1)); start
  else last=$f; fi
done
