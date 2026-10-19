#!/bin/bash
# Uso: ./render_reel.sh <dir> <nn>  → out/_silent/reel-<nn>-{organico,pauta,pauta-4x5}.mp4
set -uo pipefail
d="$1"; n="$2"; HF="npx -y hyperframes@0.8.178"
cd "$d" && $HF render -o ../out/_silent/reel-$n-organico.mp4 --variables '{"cta":"organico"}' 2>&1 | grep -E "◇|rendered|rror"
$HF render -o ../out/_silent/reel-$n-pauta.mp4 --variables '{"cta":"pauta"}' 2>&1 | grep -E "◇|rendered|rror"
cd 4x5 && $HF render -o ../../out/_silent/reel-$n-pauta-4x5.mp4 --variables '{"cta":"pauta"}' 2>&1 | grep -E "◇|rendered|rror"
