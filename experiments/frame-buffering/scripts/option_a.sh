source ~/buftest/common.sh; monitor & M=$!
python3 ~/buftest/option_a.py $OUT $TSIP "${VF#hflip,vflip,}" "$YT" > $OUT/app.log 2>&1 & A=$!
sleep ${DUR:-190}; kill $A; sleep 2; kill $M; pkill -f option_a.py; pkill -x ffmpeg; true
