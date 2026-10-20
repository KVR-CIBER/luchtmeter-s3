"""Dump footprint positions (board centre origin, mm, y down as in design.py) for the video scene."""
import json, pcbnew
b = pcbnew.LoadBoard('luchtmeter.kicad_pcb')
out = {}
for f in b.GetFootprints():
    p = f.GetPosition(); bb = f.GetBoundingBox(False, False)
    out[f.GetReference()] = dict(x=pcbnew.ToMM(p.x) - 150, y=pcbnew.ToMM(p.y) - 100, rot=f.GetOrientationDegrees(),
                                 back=f.IsFlipped(), fp=f.GetFPID().GetLibItemName().wx_str(), value=f.GetValue(),
                                 w=pcbnew.ToMM(bb.GetWidth()), h=pcbnew.ToMM(bb.GetHeight()))
json.dump(out, open('video/assets/parts.json', 'w'), indent=1)
print(len(out))
