import io, subprocess, sys, threading, time, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from libcamera import Transform
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, CircularOutput

OUT, TSIP, VF, YT = sys.argv[1:5]
picam2 = Picamera2()
cfg = picam2.create_video_configuration(
    main={"size": (1536, 864), "format": "YUV420"},   # point-and-shoot stills
    lores={"size": (640, 360), "format": "YUV420"},   # -> H.264 -> YouTube leg
    sensor={"output_size": (2304, 1296)},            # full FOV, like device.py SENSOR_MODE
    transform=Transform(hflip=1, vflip=1),            # device.py flips in ffmpeg; flip here so stills match
    controls={"FrameRate": 15}, buffer_count=4)
picam2.configure(cfg)

# the production ffmpeg (drawtext + libx264 -> flv), reading H.264 from stdin
ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
    "-thread_queue_size", "1024", "-use_wallclock_as_timestamps", "1", "-framerate", "15", "-i", "pipe:0",
    "-vf", VF, "-c:v", "libx264", "-preset", "ultrafast", "-g", "30", "-c:a", "aac", "-b:a", "128k",
    "-async", "1", "-vsync", "cfr", "-r", "15", "-progress", f"{OUT}/progress.txt", "-f", "flv", YT], stdin=subprocess.PIPE)
enc = H264Encoder(bitrate=1_000_000, repeat=True, iperiod=15)
circ = CircularOutput(buffersize=15 * 10)   # last 10 s at 15 fps
enc.output = [FileOutput(ff.stdin), circ]
picam2.start_encoder(enc, name="lores")
picam2.start()

lock = threading.Lock()
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        t0 = time.time()
        if self.path == "/snap":
            buf = io.BytesIO()
            with lock:
                picam2.capture_file(buf, format="jpeg", name="main")
            body, ctype = buf.getvalue(), "image/jpeg"
        elif self.path == "/clip":   # dump the last 10 s (pre-trigger) + 2 s after
            fn = f"{OUT}/clip_{int(t0)}.h264"
            circ.fileoutput = fn; circ.start(); time.sleep(2); circ.stop()
            body, ctype = open(fn, "rb").read(), "video/h264"
        else:
            self.send_response(404); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Type", ctype)
        self.send_header("X-Server-Seconds", f"{time.time()-t0:.3f}"); self.end_headers()
        self.wfile.write(body)
ThreadingHTTPServer((TSIP, 8081), H).serve_forever()
