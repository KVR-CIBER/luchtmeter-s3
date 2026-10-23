#!/usr/bin/env bash
# Two Freerouting passes (second one only fills the gaps), then GND stitching + pours + DRC.
cd "$(dirname "$0")"
. ./env.sh
PY=$KICAD_PY
for pass in 1; do
  "$PY" route.py export 2>/dev/null
  (cd ../out && rm -f board.ses && "$JAVA" -jar ../tools/freerouting.jar -de board.dsn -do board.ses -mp $([ $pass = 1 ] && echo 100 || echo 40) -mt 8 --gui.enabled=false > fr$pass.log 2>&1)
  grep -E "Auto-routing stage completed" ../out/fr$pass.log | sed 's/.*final score/pass '$pass' score/'
  "$PY" route.py import_raw 2>/dev/null | grep -v Debug
done
"$PY" route.py finish 2>/dev/null | grep -v Debug
"$KICAD_CLI" pcb drc -o ../out/drc.rpt ../luchtmeter.kicad_pcb | grep Found
grep -A3 "^\[" ../out/drc.rpt | grep -E "^\[|@"
