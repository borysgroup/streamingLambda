OUT=/tmp/buftest; mkdir -p $OUT
TSIP=$(tailscale ip -4 | head -1)
VF="hflip,vflip,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5:x=10:y=10:text='%{localtime\:%Y-%m-%d_%H-%M-%S}'"
YT_ENC=(-vf "$VF" -c:v libx264 -preset ultrafast -g 30 -c:a aac -b:a 128k -async 1 -vsync cfr)
AUDIO=(-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100)
RPICAM=(rpicam-vid --inline --nopreview -t 0 --width 640 --height 360 --framerate 15 --codec h264 --bitrate 1000000 --mode 2304:1296 -o -)
monitor() {  # 5 s samples: cpu%, load1, temp, throttled, MemAvailable MB
  echo "t,cpu_pct,load1,temp_c,throttled,memavail_mb" > $OUT/monitor.csv
  read -r _ a b c d e f g _ < /proc/stat; pt=$((a+b+c+d+e+f+g)); pi=$d; t0=$(date +%s)
  while sleep 5; do
    read -r _ a b c d e f g _ < /proc/stat; tt=$((a+b+c+d+e+f+g)); ii=$d
    cpu=$(( 100*((tt-pt)-(ii-pi))/(tt-pt) )); pt=$tt; pi=$ii
    echo "$(( $(date +%s)-t0 )),$cpu,$(cut -d' ' -f1 /proc/loadavg),$(vcgencmd measure_temp | grep -o '[0-9.]*'),$(vcgencmd get_throttled | cut -d= -f2),$(( $(grep MemAvailable /proc/meminfo | awk '{print $2}')/1024 ))" >> $OUT/monitor.csv
  done
}
