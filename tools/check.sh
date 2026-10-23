#!/usr/bin/env bash
# Rebuild the placement only and plot it (../out/plan.png).
cd "$(dirname "$0")"
. ./env.sh
mkdir -p ../out
"$KICAD_PY" build_pcb.py 2>&1 | grep -v assert | tail -1
"$KICAD_PY" dumpfp.py ../luchtmeter.kicad_pcb ../out/fp.json 2>/dev/null
"$VENV_PY" plot.py ../out/fp.json ../out/plan.png
