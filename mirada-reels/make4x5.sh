#!/bin/bash
# Genera <reel>/4x5/ (1080x1350) desde <reel>/index.html: mismo código, layout recompuesto por la tabla L de cada reel.
set -euo pipefail
r="$1"
rm -rf "$r/4x5"; mkdir -p "$r/4x5"
sed -e 's/data-height="1920"/data-height="1350"/' -e 's/height=1920/height=1350/' -e 's/ data-resolution="portrait"//' "$r/index.html" > "$r/4x5/index.html"
cp -r "$r/assets" "$r/4x5/assets"
cp "$r/hyperframes.json" "$r/meta.json" "$r/package.json" "$r/4x5/"
echo "$r/4x5"
