# option A to YouTube until the next cron reboot; 1/min frame count, 1 still per 5 min; hands back to device.service if it stalls
source ~/buftest/common.sh; L=~/buftest/longrun; mkdir -p $L; monitor & M=$!
python3 ~/buftest/option_a.py $OUT $TSIP "${VF#hflip,vflip,}" "$YT" > $L/app.log 2>&1 & A=$!
echo "time,frame,snap_s,cpu_pct,temp_c,throttled,memavail_mb" > $L/frames.csv; last=0; n=0
while sleep 60; do
  n=$((n+1)); f=$(grep -o "^frame=[0-9]*" $OUT/progress.txt | tail -1 | cut -d= -f2); s=
  [ $((n % 5)) = 0 ] && s=$(curl -s -o /dev/null -w "%{time_total}" --max-time 20 http://$TSIP:8081/snap)
  echo "$(date +%T),${f:-0},$s,$(tail -1 $OUT/monitor.csv | cut -d, -f2,4-6)" >> $L/frames.csv
  if ! kill -0 $A 2>/dev/null || [ "${f:-0}" -le "$last" ]; then
    echo "$(date +%T) stalled -> device.service" >> $L/frames.csv
    kill $A $M; pkill -x ffmpeg; sudo systemctl start device.service; break
  fi
  last=$f
done
