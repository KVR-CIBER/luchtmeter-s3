"""Photo-like renders of the whole device with KiCad's raytracer: the real board + the case STEPs + Waveshare's screen STEP
as 3D models on one extra footprint.  Run with KiCad's python (see README)."""
import os, sys, shutil, subprocess
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out')
PRJ = os.path.dirname(HERE)
KC = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
SCREEN = os.path.join(PRJ, 'docs', 'waveshare43', 'drawing', '4.3inch Capacitive Touch LCD 3D Drawing', '1.stp')
Z_PCB_F = -14.5                                          # case CAD z of the board's front face


def model(fp, path, z, y=0.0, opacity=1.0):
    m = pcbnew.FP_3DMODEL(); m.m_Filename = path
    m.m_Offset = pcbnew.VECTOR3D(0, y, z); m.m_Opacity = opacity
    fp.Add3DModel(m)


def variant(name, parts, renders):
    src = os.path.join(PRJ, 'luchtmeter.kicad_pcb')
    b = pcbnew.LoadBoard(src)
    fp = pcbnew.FOOTPRINT(b); fp.SetReference('CASE'); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(150), pcbnew.FromMM(100)))
    b.Add(fp)
    for path, z, y in parts:
        model(fp, path, z, y)
    pcb = os.path.join(OUT, f'_render_{name}.kicad_pcb')
    pcbnew.SaveBoard(pcb, b)
    for fn, args in renders:
        subprocess.run([KC, 'pcb', 'render', *args, '--width', '1800', '--height', '1300', '--quality', 'high',
                        '--background', 'opaque', '-o', os.path.join(OUT, fn), pcb], capture_output=True)
        print('render', fn)


shell = os.path.join(OUT, 'luchtmeter_voorkant.step'); back = os.path.join(OUT, 'luchtmeter_achterplaat.step')
dz = -Z_PCB_F                                            # case CAD -> KiCad (board front face = 0)
variant('front', [(shell, dz, 0.0), (SCREEN, -10.4 + dz, 10.0)],
        [('foto_voorkant.png', ['--side', 'top', '--rotate', '-25,0,-20', '--zoom', '0.9', '--perspective']),
         ('foto_recht.png', ['--side', 'top', '--zoom', '0.95'])])
variant('back', [(shell, dz, 0.0), (back, dz, 0.0), (SCREEN, -10.4 + dz, 10.0)],
        [('foto_achterkant.png', ['--side', 'bottom', '--rotate', '25,0,20', '--zoom', '0.9', '--perspective'])])
variant('open', [(SCREEN, -10.4 + dz, 10.0)],
        [('foto_print_achter.png', ['--side', 'bottom', '--rotate', '20,0,15', '--zoom', '0.95', '--perspective'])])
for f in os.listdir(OUT):
    if f.startswith('_render_'):
        os.remove(os.path.join(OUT, f))
sys.stdout.flush(); os._exit(0)
