# production pipeline as-is, 60 s of monitoring
source ~/buftest/common.sh; monitor & M=$!; sleep 62; kill $M; cat $OUT/monitor.csv
