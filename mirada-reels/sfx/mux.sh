#!/bin/bash
# Uso: sfx/mux.sh <video_sin_audio.mp4> <audio.wav> <salida.mp4>
# Normaliza el audio a -14 LUFS (dos pasadas, true peak -1 dBTP) y lo une al video sin recomprimir la imagen.
set -euo pipefail
v="$1"; a="$2"; o="$3"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")
m=$(ffmpeg -hide_banner -i "$a" -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$m" | python3 -c "import sys,json;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -hide_banner -loglevel error -y -i "$v" -i "$a" -map 0:v -map 1:a \
  -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000,apad" \
  -t "$dur" -c:v copy -c:a aac -b:a 192k -movflags +faststart "$o"
echo "$o"
