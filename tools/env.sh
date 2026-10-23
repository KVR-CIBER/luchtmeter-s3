# Tool locations for the build scripts (sourced). Override any of them in the environment; defaults = macOS (KiCad.app, brew).
#   KICAD_PY   KiCad's python (has the pcbnew module)       Linux flatpak: tools/flatpak/kicad-python
#   KICAD_CLI  kicad-cli                                     Linux flatpak: tools/flatpak/kicad-cli
#   VENV_PY    python with numpy + shapely (+ matplotlib) for finisher.py route / plot.py
#   JAVA       java 25+ for freerouting.jar (2.4.1 is built for class file version 69)
_MAC=/Applications/KiCad/KiCad.app/Contents
if [ -x "$_MAC/MacOS/kicad-cli" ]; then
  : "${KICAD_PY:=$_MAC/Frameworks/Python.framework/Versions/3.9/bin/python3}"
  : "${KICAD_CLI:=$_MAC/MacOS/kicad-cli}"
  : "${VENV_PY:=$HOME/Documents/GitHub/arachne-18/.venv/bin/python}"
  : "${JAVA:=$(brew --prefix openjdk 2>/dev/null)/bin/java}"
else
  _T=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  : "${KICAD_PY:=$(command -v kicad-python || echo "$_T/flatpak/kicad-python")}"
  : "${KICAD_CLI:=$(command -v kicad-cli || echo "$_T/flatpak/kicad-cli")}"
  : "${VENV_PY:=$_T/../.venv/bin/python}"
  : "${JAVA:=$(ls -d /usr/lib/jvm/java-2[5-9]*/bin/java /usr/lib/jvm/java-[3-9]*/bin/java 2>/dev/null | head -1)}"
  : "${JAVA:=$(command -v java)}"
fi
export KICAD_PY KICAD_CLI VENV_PY JAVA
