#!/usr/bin/env bash
# Regenerate everything from design.py: libraries, board, schematic, routing, checks, fab outputs (~10 min).
# Tool paths: see env.sh (macOS defaults, override with KICAD_PY / KICAD_CLI / VENV_PY / JAVA).
set -e
cd "$(dirname "$0")"
. ./env.sh
PY=$KICAD_PY; KC=$KICAD_CLI; VENV=$VENV_PY        # VENV: numpy + shapely for the finisher
[ -f freerouting.jar ] || curl -sL -o freerouting.jar https://github.com/freerouting/freerouting/releases/download/v2.4.1/freerouting-2.4.1.jar
mkdir -p ../out
python3 design.py
"$PY" libs.py 2>/dev/null
"$PY" build_pcb.py 2>/dev/null
"$PY" build_sch.py 2>/dev/null
./route.sh                                   # Freerouting + GND stitching/pours + DRC report
for i in 1 2 3; do                           # finish what Freerouting left open
  "$KC" pcb drc -o ../out/drc.rpt ../luchtmeter.kicad_pcb | grep -q "Found 0 unconnected" && break
  "$PY" finisher.py dump 2>/dev/null; "$VENV" finisher.py route; "$PY" finisher.py apply 2>/dev/null
done
"$PY" route.py cleanvias 2>/dev/null | grep -v Debug
"$PY" parity.py fixnc 2>/dev/null
"$KC" pcb drc --schematic-parity -o ../out/drc.rpt ../luchtmeter.kicad_pcb
"$KC" sch erc -o ../out/erc.rpt ../luchtmeter.kicad_sch
python3 fab.py
