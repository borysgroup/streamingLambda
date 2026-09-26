pkill -f "bash .*buftest/option_"; pkill -f "buftest/option_a.py"; pkill -f "m http.server 8081"; pkill -x mediamtx; pkill -x rpicam-vid; pkill -x ffmpeg
sleep 3; pgrep -a "rpicam|ffmpeg|mediamtx" || echo clean
