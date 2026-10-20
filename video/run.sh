#!/bin/bash
# Full render on lvdell: Blender (Cycles OptiX, RTX 3070) -> overlays -> H.264 4K
set -e
cd "$(dirname "$0")"
rm -rf frames final; mkdir -p frames
/opt/blender-4.5.3-linux-x64/blender -b -P scene.py -- labels > log_labels.txt 2>&1
/opt/blender-4.5.3-linux-x64/blender -b -P scene.py -- anim > log_render.txt 2>&1
python3 overlay.py > log_overlay.txt 2>&1
ffmpeg -loglevel error -y -framerate 30 -i final/%04d.png -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p -movflags +faststart luchtmeter_s3_4k.mp4
ffmpeg -loglevel error -y -i luchtmeter_s3_4k.mp4 -vf scale=1920:-2 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart luchtmeter_s3_1080p.mp4
echo DONE > done.txt
