#!/bin/bash
# Arma el audio de un film: score sintetizado -> beats medidos -> SFX sobre la grilla -> audio.wav
# Uso: npm run sound -- films/<nombre>
# Si el film trae un track propio (track.wav), se mide ese y se mezclan los SFX encima.
set -euo pipefail
film="${1:?uso: tools/sound.sh films/<nombre>}"
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$film"

if [ -f track.wav ]; then
  cp track.wav score.wav
  echo "usando track.wav suministrado"
else
  python3 sound.py score score.wav
fi

bpm=$(python3 -c "import importlib.util,sys;s=importlib.util.spec_from_file_location('s','sound.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(getattr(m,'BPM',''))" 2>/dev/null || true)
python3 "$here/tools/beats.py" score.wav . ${bpm:+--bpm "$bpm"}
python3 sound.py mix audio.wav
echo "listo: $film/audio.wav"
