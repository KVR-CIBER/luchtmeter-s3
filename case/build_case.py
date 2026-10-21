"""Luchtmeter S3 case: front shell + back plate + desk stand (CadQuery), STL + STEP + renders.
Authors: Kobe Vanrobaeys (@KVR-CIBER) & varol56 (@varol56, co-inventor).

CAD axes: X = board x (right), Y = -board y (up), Z = towards the viewer; the front face of the case is at Z = 0.
Stack (measured in Waveshare's STEP of the 4.3in Capacitive Touch LCD):
  front plate 0 .. -1.6 | cover glass -1.6 .. -2.4 | module PCB -8.8 .. -10.4 | its own 4.1 mm standoffs |
  our PCB -14.5 .. -16.1 | back parts (SCD41 6.5 mm, LiPo ~5 mm) | back plate -23.6 .. -25.6
Run: ~/Downloads/solar-olympiade/.venv/bin/python case/build_case.py
"""
import math, os, sys
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import design as D                                       # board outline, holes, part positions

OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- dimensions
CAV_W, CAV_H = 106.6, 88.6                 # inner cavity (board 106 x 88 + 0.3 play)
WALL = 2.5
OUT_W, OUT_H = CAV_W + 2 * WALL, CAV_H + 2 * WALL
R_OUT = 8.0
PLATE = 1.6                                # front plate
Z_GLASS = -PLATE
Z_PCB_F, Z_PCB_B = -14.5, -16.1            # our board
Z_BACK_IN, BACK_T = -23.6, 2.0             # back plate
DEPTH = -Z_BACK_IN + BACK_T                # 25.6 mm
LCD_Y = -D.LCD_CY                          # screen module centre (CAD y)
GLASS_W, GLASS_H = 106.0, 67.9
WIN_W, WIN_H = 103.6, 65.6                 # front opening: ~1.2 mm lip around the cover glass


def by(y):                                 # board y -> CAD y
    return -y


def board_xy(ref):
    p = [q for q in D.parts if q['ref'] == ref][0]
    return p['at'][0], by(p['at'][1])


def rrect(w, h, r):
    return cq.Sketch().rect(w, h).vertices().fillet(r)


# ---------------------------------------------------------------- front shell
shell = (cq.Workplane('XY').workplane(offset=-DEPTH).placeSketch(rrect(OUT_W, OUT_H, R_OUT)).extrude(DEPTH))
shell = shell.faces('>Z').edges().fillet(2.2)                                   # soft front edge
cavity = (cq.Workplane('XY').workplane(offset=-DEPTH - 1).placeSketch(rrect(CAV_W, CAV_H, R_OUT - WALL))
          .extrude(DEPTH + 1 - PLATE))
shell = shell.cut(cavity)
# screen window (cover glass shows almost edge to edge), slight chamfer on the front
win = cq.Workplane('XY').workplane(offset=-PLATE - 0.1).center(0, LCD_Y).placeSketch(rrect(WIN_W, WIN_H, 3.0)).extrude(PLATE + 0.2)
shell = shell.cut(win)
shell = shell.edges(cq.selectors.BoxSelector((-WIN_W / 2 - 0.5, LCD_Y - WIN_H / 2 - 0.5, -0.3), (WIN_W / 2 + 0.5, LCD_Y + WIN_H / 2 + 0.5, 0.3))).chamfer(0.6)

# bosses for the two M3 screws (back plate -> spacer -> PCB H5/H6 -> boss), self-tapping 2.5 mm pilot
BOSS = []
for ref in ('H5', 'H6'):
    x, y = board_xy(ref)
    b = cq.Workplane('XY').workplane(offset=Z_PCB_F).center(x, y).circle(3.2).extrude(-Z_PCB_F - PLATE + 0.01)
    shell = shell.union(b)
    shell = shell.cut(cq.Workplane('XY').workplane(offset=Z_PCB_F - 0.1).center(x, y).circle(1.25).extrude(10.5))
    BOSS.append((x, y))

# light pipe for the LTR-303: dark tube from the front plate down to the sensor (no backlight leaking in)
lx, ly = board_xy('U4')
tube = cq.Workplane('XY').workplane(offset=Z_PCB_F + 0.4).center(lx, ly).circle(2.6).extrude(-Z_PCB_F - 0.4 - PLATE + 0.01)
shell = shell.union(tube)
shell = shell.cut(cq.Workplane('XY').workplane(offset=Z_PCB_F).center(lx, ly).circle(1.5).extrude(-Z_PCB_F + 1))
shell = shell.cut(cq.Workplane('XY').workplane(offset=-0.6).center(lx, ly).circle(2.2).extrude(1))      # seat for a 4 mm clear disc

# NFC mark on the front (0.4 mm deep), centred on the antenna coil
cx = (D.NFC['x0'] + D.NFC['x1']) / 2; cy = by((D.NFC['y0'] + D.NFC['y1']) / 2)
nfc = cq.Workplane('XY').workplane(offset=-0.4)
for i, r in enumerate((2.0, 3.6, 5.2)):                                         # three waves, like the NFC logo
    arc = (cq.Workplane('XY').workplane(offset=-0.4).center(cx - 4, cy).circle(r + 0.35).circle(r - 0.35).extrude(0.5)
           .intersect(cq.Workplane('XY').workplane(offset=-0.5).center(cx - 4 + r / 2 + 0.1, cy).rect(r + 0.2, 2 * r + 1).extrude(0.7)))
    shell = shell.cut(arc)
txt = cq.Workplane('XY').workplane(offset=-0.4).center(cx + 6.5, cy).text('NFC', 4.2, 0.5, halign='center', valign='center', kind='bold')
shell = shell.cut(txt)

# USB-C opening in the left wall (connector on the back of the board)
ux, uy = board_xy('J2')
uz = Z_PCB_B - 1.6
usb = cq.Workplane('YZ').workplane(offset=-OUT_W / 2 - 1).center(uy, uz).sketch().rect(12.4, 6.8).vertices().fillet(3.0).finalize().extrude(WALL + 2)
shell = shell.cut(usb)
# slots for the two hooks at the top of the back plate
for x in (-30.0, 30.0):
    shell = shell.cut(cq.Workplane('XY').workplane(offset=Z_BACK_IN - 0.1).center(x, CAV_H / 2 + 0.6).rect(10.4, 1.4).extrude(2.6))
# shallow pocket inside the top wall for the U.FL flex antenna (40 x 10 mm sticker)
shell = shell.cut(cq.Workplane('XZ').workplane(offset=-CAV_H / 2 - 0.6).center(0, -9.0).rect(42, 11).extrude(0.6))
# small ventilation slots in the bottom wall, under the sensor strip
for i in range(-4, 5):
    shell = shell.cut(cq.Workplane('XZ').workplane(offset=OUT_H / 2 + 1).center(20 + i * 3.2, -20.0).rect(1.4, 5.0).extrude(-WALL - 2))

# ---------------------------------------------------------------- back plate (inset, 2 mm), hooks at the top, 2 screws at the bottom
bp = (cq.Workplane('XY').workplane(offset=-DEPTH).placeSketch(rrect(CAV_W - 0.4, CAV_H - 0.4, R_OUT - WALL - 0.2)).extrude(BACK_T))
for x in (-30.0, 30.0):                                                          # hooks into the top wall slots
    hook = cq.Workplane('XY').workplane(offset=Z_BACK_IN).center(x, CAV_H / 2 - 0.2 - 1.0).rect(10.0, 2.0).extrude(2.0)
    lip = cq.Workplane('XY').workplane(offset=Z_BACK_IN + 0.9).center(x, CAV_H / 2 + 0.25).rect(10.0, 1.1).extrude(1.1)
    bp = bp.union(hook).union(lip)
for x, y in BOSS:                                                                # spacer tubes up to the PCB
    bp = bp.union(cq.Workplane('XY').workplane(offset=Z_BACK_IN).center(x, y).circle(3.2).extrude(Z_PCB_B - Z_BACK_IN - 0.1))
    bp = bp.cut(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(x, y).circle(1.7).extrude(DEPTH))
    bp = bp.cut(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(x, y).circle(3.1).extrude(1.9))   # screw head recess
# vents over the SCD41 and the SHT45 tongue
for ref, nx, ny in (('U5', 6, 4), ('U6', 3, 4)):
    x0, y0 = board_xy(ref)
    for i in range(nx):
        for j in range(ny):
            bp = bp.cut(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(x0 + (i - (nx - 1) / 2) * 3.0, y0 + (j - (ny - 1) / 2) * 3.4)
                        .slot2D(2.6, 1.3, 90).extrude(BACK_T + 0.2))
# WEKKEN: flexible button tongue with a nub that reaches the switch; RESET: pin hole
wx, wy = board_xy('SW1')
gap = (cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(wx, wy - 1.5)
       .rect(9.0, 12.0).rect(7.8, 10.8).extrude(BACK_T + 0.2))
bp = bp.cut(gap).union(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(wx, wy + 4.5).rect(9.0, 0.7).extrude(BACK_T + 0.2))
bp = bp.cut(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(wx, wy + 4.5).rect(7.8, 0.6).extrude(BACK_T + 0.2))
bp = bp.union(cq.Workplane('XY').workplane(offset=Z_BACK_IN).center(wx, wy).circle(1.6).extrude(Z_PCB_B - 2.6 - Z_BACK_IN))
rx, ry = board_xy('SW2')
bp = bp.cut(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(rx, ry).circle(0.9).extrude(BACK_T + 0.2))
# subtle debossed name on the back
bp = bp.cut(cq.Workplane('XY').workplane(offset=-DEPTH - 0.1).center(-20, -10).text('LUCHTMETER', 6.0, 0.5, halign='center', kind='bold')
            .mirror('YZ', basePointVector=(-20, 0, 0)))

# ---------------------------------------------------------------- desk stand (20 deg lean), slides onto the bottom edge
LEAN = math.radians(20)
stand = (cq.Workplane('XY').box(70, 46, 6, centered=(True, False, False)).translate((0, -8, 0))
         .union(cq.Workplane('XY').box(70, 6, 18, centered=(True, False, False)).translate((0, -8, 0))
                .rotate((0, -8, 0), (1, -8, 0), -20))
         .union(cq.Workplane('XY').box(70, 4, 10, centered=(True, False, False)).translate((0, DEPTH * 1.06, 0))))
stand = stand.edges('|X').fillet(1.0)

# ---------------------------------------------------------------- export
cq.exporters.export(shell, os.path.join(OUT, 'luchtmeter_voorkant.stl'), tolerance=0.02, angularTolerance=0.1)
cq.exporters.export(bp, os.path.join(OUT, 'luchtmeter_achterplaat.stl'), tolerance=0.02, angularTolerance=0.1)
cq.exporters.export(stand, os.path.join(OUT, 'luchtmeter_standaard.stl'), tolerance=0.02, angularTolerance=0.1)
for n, w in (('voorkant', shell), ('achterplaat', bp), ('standaard', stand)):
    cq.exporters.export(w, os.path.join(OUT, f'luchtmeter_{n}.step'))
print('case: %.1f x %.1f x %.1f mm' % (OUT_W, OUT_H, DEPTH))
for n, w in (('voorkant', shell), ('achterplaat', bp), ('standaard', stand)):
    print(n, 'volume %.1f cm3' % (w.val().Volume() / 1000))
