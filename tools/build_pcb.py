import sys
"""Place the Luchtmeter S3 board in pcbnew: outline, footprints, nets, planes, keep-outs, artwork.
Routing is done afterwards by route.py (Freerouting)."""
import os, json, math, uuid, shutil
import pcbnew
import design, libs

PRJ = libs.PRJ
NAME = 'luchtmeter'
OX, OY = 150.0, 100.0          # board centre on the KiCad page
MM = pcbnew.FromMM
W, H, RC = design.BOARD_W, design.BOARD_H, design.CORNER_R
X0, Y0, X1, Y1 = -W / 2, -H / 2, W / 2, H / 2


def V(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


def sym_uuid(ref, unit=1):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'luchtmeter/{ref}/{unit}'))


ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, 'luchtmeter/root'))
OUTLINE = {k: [tuple(p) for p in v[:-1]] for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outline.json'))).items()}


# ---------------------------------------------------------------- project file
def write_project():
    tpl = json.load(open(os.path.expanduser('~/Documents/GitHub/tiltbox-kicad/tiltbox.kicad_pro')))
    tpl['meta']['filename'] = NAME + '.kicad_pro'
    tpl['sheets'] = [[ROOT_UUID, 'Root']]
    tpl['boards'] = []
    ds = tpl['board']['design_settings']
    ds['rules'].update({'min_clearance': 0.127, 'min_track_width': 0.1, 'min_via_diameter': 0.45,
                        'min_through_hole_diameter': 0.2, 'min_via_annular_width': 0.1,
                        'min_copper_edge_clearance': 0.3, 'min_hole_clearance': 0.2, 'min_hole_to_hole': 0.25,
                        'min_silk_clearance': 0.0})
    ds['track_widths'] = [0.0, 0.15, 0.25, 0.5, 1.0, 1.5]
    ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.45, 'drill': 0.2},
                            {'diameter': 0.6, 'drill': 0.3}, {'diameter': 0.8, 'drill': 0.4}]
    sev = ds.setdefault('rule_severities', {})
    sev.update({'silk_overlap': 'ignore', 'silk_over_copper': 'ignore', 'silk_edge_clearance': 'ignore',
                'lib_footprint_mismatch': 'ignore', 'lib_footprint_issues': 'ignore', 'text_height': 'ignore',
                'footprint_symbol_mismatch': 'ignore',
                'connection_width': 'ignore'})   # sub-0.1 mm slivers at the edge of the GND pours only
    base = dict(tpl['net_settings']['classes'][0])
    base.update({'name': 'Default', 'track_width': 0.15, 'clearance': 0.15, 'via_diameter': 0.45, 'via_drill': 0.2})
    classes = [base]
    pats = []
    for i, (cname, (nets, tw, cl)) in enumerate(design.NETCLASS.items()):
        c = dict(base); c.update({'name': cname, 'track_width': tw, 'clearance': cl, 'priority': i,
                                 'via_diameter': 0.6 if tw >= 0.5 else 0.45, 'via_drill': 0.3 if tw >= 0.5 else 0.2})
        classes.append(c)
        pats += [{'netclass': cname, 'pattern': n} for n in nets]
    tpl['net_settings']['classes'] = classes
    tpl['net_settings']['netclass_patterns'] = pats
    tpl['net_settings']['netclass_assignments'] = None
    json.dump(tpl, open(os.path.join(PRJ, NAME + '.kicad_pro'), 'w'), indent=2)


# ---------------------------------------------------------------- helpers
def shape_line(board, layer, a, b, w=0.15):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*a)); s.SetEnd(V(*b)); s.SetLayer(layer); s.SetWidth(MM(w)); board.Add(s); return s


def shape_circle(board, layer, c, r, w=0.15, fill=False):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(V(*c)); s.SetEnd(V(c[0] + r, c[1])); s.SetLayer(layer); s.SetWidth(MM(w))
    s.SetFilled(fill); board.Add(s); return s


def shape_poly(board, layer, pts, w=0.0, fill=True):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_POLY)
    s.SetPolyPoints([V(*p) for p in pts]); s.SetLayer(layer); s.SetWidth(MM(w)); s.SetFilled(fill)
    board.Add(s); return s


def text(board, layer, s, at, size=1.0, th=0.15, rot=0, mirror=False, bold=False):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(V(*at)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(th)); t.SetTextAngleDegrees(rot)
    t.SetMirrored(mirror); t.SetBold(bold); board.Add(t); return t


def rounded_rect_pts(x0, y0, x1, y1, r, n=10):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def zone(board, net, layer, pts, prio=0, name='', connect='thermal', clearance=0.25, minw=0.2):
    z = pcbnew.ZONE(board); z.SetLayer(layer)
    if net:
        z.SetNet(board.FindNet(net))
    ol = z.Outline(); ol.NewOutline()
    for p in pts:
        ol.Append(MM(OX + p[0]), MM(OY + p[1]))
    z.SetAssignedPriority(prio); z.SetZoneName(name)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if connect == 'full' else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetLocalClearance(MM(clearance)); z.SetMinThickness(MM(minw))
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z); return z


def keepout(board, pts, layers, tracks=True, vias=True, pours=True, pads=False, fps=False, name=''):
    z = pcbnew.ZONE(board); z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    ol = z.Outline(); ol.NewOutline()
    for p in pts:
        ol.Append(MM(OX + p[0]), MM(OY + p[1]))
    z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowZoneFills(pours)
    z.SetDoNotAllowPads(pads); z.SetDoNotAllowFootprints(fps); z.SetZoneName(name)
    board.Add(z); return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def via(board, net, at, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board); v.SetPosition(V(*at)); v.SetDrill(MM(drill)); v.SetWidth(MM(d))
    v.SetNet(board.FindNet(net)); v.SetViaType(pcbnew.VIATYPE_THROUGH); board.Add(v); return v


def track(board, net, a, b, w, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(board); t.SetStart(V(*a)); t.SetEnd(V(*b)); t.SetWidth(MM(w)); t.SetLayer(layer)
    t.SetNet(board.FindNet(net)); board.Add(t); return t


def pad_pos(fp, num):
    out = []
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition(); out.append((pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY))
    return out


# ---------------------------------------------------------------- build
def build():
    board = pcbnew.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    board.SetLayerName(pcbnew.In1_Cu, 'In1.Cu'); board.SetLayerName(pcbnew.In2_Cu, 'In2.Cu')
    # inner layers are solid planes (GND / 12 V): mark them 'power' so the autorouter keeps off them
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER); board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)

    for n in design.nets():
        board.Add(pcbnew.NETINFO_ITEM(board, n))

    fpdir = os.path.join(PRJ, 'lucht.pretty')
    fps = {}
    for p in design.parts:
        name = libs.fp_name(p['fp'])
        fp = pcbnew.FootprintLoad(fpdir, name)
        assert fp is not None, name
        fp.SetFPID(pcbnew.LIB_ID('lucht', name))
        fp.SetReference(p['ref']); fp.SetValue(p['value'])
        x, y, rot = p['at']
        fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
        fp.SetPath(pcbnew.KIID_PATH('/' + sym_uuid(p['ref'], 1)))
        fp.SetProperties if False else None
        for prop, val in (('MPN', p['mpn']),):
            if val:
                f = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, prop) if hasattr(pcbnew, 'FIELD_T_USER') else None
                if f is not None:
                    f.SetText(val); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab); fp.Add(f)
        board.Add(fp)
        if p['side'] == 'B':                         # flip only after the footprint is on the board
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for pad in fp.Pads():
            net = p['pins'].get(pad.GetNumber())
            if net:
                pad.SetNet(board.FindNet(net))
        fps[p['ref']] = fp
        # small, tidy reference text
        r = fp.Reference(); r.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8))); r.SetTextThickness(MM(0.12))

    # ---------------- outline: rounded rectangle
    edge = OUTLINE['edge']
    for a, b in zip(edge, edge[1:] + edge[:1]):
        if a != b:
            shape_line(board, pcbnew.Edge_Cuts, a, b, 0.1)
    inner = OUTLINE['inner']
    allcu = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

    # ---------------- internal slots (heat barrier + SHT45 tongue), drawn as closed oblongs on Edge.Cuts
    for path in design.SLOTS:
        pts = slot_outline(path, design.SLOT_W / 2)
        for p0, p1 in zip(pts, pts[1:] + pts[:1]):
            shape_line(board, pcbnew.Edge_Cuts, p0, p1, 0.1)
        m = design.SLOT_W / 2 + 0.4
        for (ax, ay), (bx, by) in zip(path, path[1:]):
            keepout(board, rect(min(ax, bx) - m, min(ay, by) - m, max(ax, bx) + m, max(ay, by) + m), allcu, name='sleuf')

    # SHT45 tongue: no copper pours, so the ESP/regulator heat does not reach the sensor through the planes
    tx0, ty0, tx1, ty1 = design.TONGUE
    keepout(board, rect(tx0 - 1, ty0, tx1, ty1), [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu], tracks=False, vias=False, pours=True,
            name='SHT45 tong: geen koper (alleen het GND-vlak, voor de vias)')
    # free corridor (no pours) from the board into the tongue, under the end of the slot
    keepout(board, rect(33.5, 36.0, tx0 + 1, Y1 + 1), [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu], tracks=False, vias=False, pours=True,
            name='SHT45 doorgang')

    # ---------------- NFC antenna: rectangular spiral on F.Cu, outer end = AC0, inner end = AC1 (bridge on B.Cu)
    nfc_coil(board)

    # ---------------- planes: In1 = GND, In2 = 3.3 V
    zone(board, 'GND', pcbnew.In1_Cu, inner, prio=0, name='GND plane', connect='full')
    zone(board, '3V3', pcbnew.In2_Cu, inner, prio=0, name='3V3 plane', connect='full')

    # thermal / ground vias inside the exposed pads (ESP32, SCD41, BQ24075)
    for ref, num, pitch in (('U5', '21', 1.6), ('U7', '17', 1.0)):   # the ESP32 footprint has its own thermal vias
        for p in fps[ref].Pads():
            if p.GetNumber() != num:
                continue
            bb = p.GetBoundingBox()
            x0_, y0_ = pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetY()) - OY
            w_, h_ = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
            nx, ny = max(1, int((w_ - 0.6) / pitch) + 1), max(1, int((h_ - 0.6) / pitch) + 1)
            for i in range(nx):
                for j in range(ny):
                    via(board, 'GND', (x0_ + w_ / 2 + (i - (nx - 1) / 2) * pitch, y0_ + h_ / 2 + (j - (ny - 1) / 2) * pitch), d=0.45, drill=0.2)
    # SHT45 (0.8 mm DFN on the tongue): SDA / SCL get a short stub + via, so the router can reach them from the front side
    ux_, uy_ = pcbnew.ToMM(fps['U6'].GetPosition().x) - OX, pcbnew.ToMM(fps['U6'].GetPosition().y) - OY
    for q in fps['U6'].Pads():
        if q.GetNumber() in ('1', '2'):
            qx, qy = pcbnew.ToMM(q.GetPosition().x) - OX, pcbnew.ToMM(q.GetPosition().y) - OY
            sx_ = 1 if qx > ux_ else -1
            vy = qy + (-1.0 if q.GetNumber() == '1' else 1.0)
            track(board, q.GetNetname(), (qx, qy), (qx + sx_ * 0.9, qy), 0.2, layer=pcbnew.B_Cu)
            track(board, q.GetNetname(), (qx + sx_ * 0.9, qy), (qx + sx_ * 1.6, vy), 0.2, layer=pcbnew.B_Cu)
            via(board, q.GetNetname(), (qx + sx_ * 1.6, vy), d=0.45, drill=0.2)
    # TPS61023 EN is the middle pin of a 0.5 mm SOT-563: give it a short stub + via so the router can reach it
    for q in fps['U9'].Pads():
        if q.GetNumber() == '2':
            qx, qy = pcbnew.ToMM(q.GetPosition().x) - OX, pcbnew.ToMM(q.GetPosition().y) - OY
            ux_ = pcbnew.ToMM(fps['U9'].GetPosition().x) - OX
            sx_ = 1 if qx > ux_ else -1
            track(board, 'DISP_ON', (qx, qy), (qx + sx_ * 1.4, qy), 0.15, layer=pcbnew.B_Cu)
            via(board, 'DISP_ON', (qx + sx_ * 1.4, qy), d=0.45, drill=0.2)
    # no copper pours in the small board tabs next to the screen-header notch (they would be islands)
    nx0, ny0, nx1, ny1 = design.NOTCH
    for ya, yb in ((Y0 - 1, ny0), (ny1, ny1 + 4.6)):
        keepout(board, rect(nx0 - 0.5, ya, X1 + 1, yb), [pcbnew.F_Cu, pcbnew.B_Cu], tracks=False, vias=False, pours=True, name='tab')
    fanout(board, {'GND', '3V3'}, {})

    # ---------------- artwork
    F, B = pcbnew.F_SilkS, pcbnew.B_SilkS
    # where the screen module goes (Fab) + its tall 2x20 header
    for a_, b_ in (((-53, -44), (53, -44)), ((53, -44), (53, 24)), ((53, 24), (-53, 24)), ((-53, 24), (-53, -44))):
        shape_line(board, pcbnew.F_Fab, a_, b_, 0.1)
    text(board, F, 'SCHERM 4.3" (Waveshare 16249): M2-schroeven in de afstandsbussen van het scherm', (0.0, -30.0), size=1.0)
    text(board, F, 'FFC naar het scherm (pin 1 rechts)', (-9.0, -3.0), size=0.7)
    text(board, F, 'NFC', (-12.0, 34.3), size=1.5, bold=True)
    text(board, F, 'LICHT', (31.5, 39.0), size=0.6)
    text(board, B, 'USB-C', (-44.5, -6.0), size=0.7, rot=90, mirror=True)
    text(board, B, 'WEKKEN', (16.0, -38.9), size=0.6, mirror=True)
    text(board, B, 'RESET', (23.0, -38.9), size=0.6, mirror=True)
    text(board, B, 'CO2', (26.0, -0.6), size=0.9, bold=True, mirror=True)
    text(board, B, 'TEMP', (47.0, 27.5), size=0.7, bold=True, mirror=True)
    text(board, B, 'U.FL antenne', (0.0, -42.0), size=0.6, mirror=True)
    back_art(board)
    silk_cleanup(board)
    board.SetFileName(os.path.join(PRJ, NAME + '.kicad_pcb'))
    pcbnew.SaveBoard(os.path.join(PRJ, NAME + '.kicad_pcb'), board)
    write_project()
    return board


# ---------------------------------------------------------------- plane fan-out
def _pt_in_poly(px, py, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def _dist_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy or 1e-12
    t = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / L))
    return math.hypot(a[0] + t * dx - px, a[1] + t * dy - py)


def _edge_dist(px, py):
    e = OUTLINE['edge']
    return min(_dist_seg(px, py, a, b) for a, b in zip(e, e[1:] + e[:1]))


def _rect_seg_hit(r, a, b, m):
    """segment a-b within m of rectangle r=(x0,y0,x1,y1)?"""
    x0, y0, x1, y1 = r[0] - m, r[1] - m, r[2] + m, r[3] + m
    for i in range(21):
        t = i / 20; x = a[0] + (b[0] - a[0]) * t; y = a[1] + (b[1] - a[1]) * t
        if x0 < x < x1 and y0 < y < y1:
            return True
    return False


def fanout(board, plane_nets, regions):
    """Drop a via (+ short track) next to every SMD pad of a plane net that is not already on its own copper."""
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            r = (pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetY()) - OY, pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY)
            pads.append((p, r, p.GetNetname(), p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD))
    vias = [(pcbnew.ToMM(v.GetPosition().x) - OX, pcbnew.ToMM(v.GetPosition().y) - OY, pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2, v.GetNetname())
            for v in board.GetTracks() if v.GetClass() == 'PCB_VIA']
    blocked = []                         # (poly, allowed_net)
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():
            blocked.append(([(pcbnew.ToMM(z.Outline().CVertex(i).x) - OX, pcbnew.ToMM(z.Outline().CVertex(i).y) - OY)
                             for i in range(z.Outline().TotalVertices())], None))
        elif not z.GetIsRuleArea() and z.GetLayer() == pcbnew.F_Cu:
            blocked.append(([(pcbnew.ToMM(z.Outline().CVertex(i).x) - OX, pcbnew.ToMM(z.Outline().CVertex(i).y) - OY)
                             for i in range(z.Outline().TotalVertices())], z.GetNetname()))
    fps_under = []                       # no vias under the CM5 connectors themselves
    n_ok, n_fail = 0, []
    for p, r, net, smd in pads:
        if net not in plane_nets or not smd:
            continue
        lay = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        if net in regions and not _pt_in_poly(cx, cy, regions[net]):
            continue
        if any(_pt_in_poly(cx, cy, poly) for poly, an in blocked if an == net):
            continue                     # pad sits on its own copper zone already
        ref = p.GetParentFootprint().GetReference()
        if ref == 'U6':
            continue                     # SHT45: tiny pads, the router connects them
        big = False
        vd, vdr, tw = (0.6, 0.3, 0.6) if big else (0.45, 0.2, 0.3)
        hw, hh = (r[2] - r[0]) / 2, (r[3] - r[1]) / 2
        cands = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            for extra in (0.45, 0.75, 1.1, 1.6, 2.2):
                d = (abs(math.cos(a)) * hw + abs(math.sin(a)) * hh) + vd / 2 + extra
                cands.append((extra, k, cx + d * math.cos(a), cy + d * math.sin(a)))
        cands.sort()
        done = False
        for extra, k, vx, vy in cands:
            if _edge_dist(vx, vy) < vd / 2 + 0.5:
                continue
            if any(_pt_in_poly(vx, vy, poly) and an != net for poly, an in blocked):
                continue
            if any(math.hypot(vx - x, vy - y) < rr + vd / 2 + 0.2 for x, y, rr, nn in vias):
                continue
            bad = False
            for q, rq, nq, sq in pads:
                if q is p:
                    continue
                if nq == net and not big:
                    m = 0.05
                else:
                    m = 0.2
                # via body
                if rq[0] - m - vd / 2 < vx < rq[2] + m + vd / 2 and rq[1] - m - vd / 2 < vy < rq[3] + m + vd / 2:
                    bad = True; break
                if nq != net and _rect_seg_hit(rq, (cx, cy), (vx, vy), 0.18 + tw / 2):
                    bad = True; break
            if bad:
                continue
            track(board, net, (cx, cy), (vx, vy), tw, layer=lay)
            via(board, net, (vx, vy), d=vd, drill=vdr)
            vias.append((vx, vy, vd / 2, net)); n_ok += 1; done = True
            break
        if not done:
            n_fail.append((ref, p.GetNumber(), net))
    print('fan-out vias:', n_ok, 'failed:', n_fail)


def slot_outline(path, r, n=8):
    """closed outline of a slot of half-width r along an axis-parallel polyline (straight or L): round ends, square corners"""
    def normal(a, b, sign):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        return (-(b[1] - a[1]) / L * sign * r, (b[0] - a[0]) / L * sign * r)

    def side(sign):
        out = []
        for i, (x, y) in enumerate(path):
            ns = [normal(path[k], path[k + 1], sign) for k in (i - 1, i) if 0 <= k < len(path) - 1]
            if len(ns) == 2 and abs(ns[0][0] * ns[1][0] + ns[0][1] * ns[1][1]) < 1e-9:
                n = (ns[0][0] + ns[1][0], ns[0][1] + ns[1][1])      # square corner (90 deg)
            else:
                n = ns[0]
            out.append((x + n[0], y + n[1]))
        return out
    left, right = side(1), side(-1)
    pts = left[:]
    (ax, ay), (bx, by) = path[-2], path[-1]
    ang = math.atan2(by - ay, bx - ax)
    pts += [(bx + r * math.cos(ang + math.pi / 2 - math.pi * i / n), by + r * math.sin(ang + math.pi / 2 - math.pi * i / n)) for i in range(1, n)]
    pts += right[::-1]
    (ax, ay), (bx, by) = path[1], path[0]
    ang = math.atan2(by - ay, bx - ax)
    pts += [(bx + r * math.cos(ang + math.pi / 2 - math.pi * i / n), by + r * math.sin(ang + math.pi / 2 - math.pi * i / n)) for i in range(1, n)]
    return pts


def oblong(a, b, r, n=8):
    """closed slot outline around segment a-b with radius r"""
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); pts = []
    for c, a0 in ((b, ang - math.pi / 2), (a, ang + math.pi / 2)):
        for i in range(n + 1):
            t = a0 + math.pi * i / n; pts.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return pts


def silk_cleanup(board):
    """Only connectors and buttons keep a visible reference (JLC places the rest)."""
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        fp.Reference().SetVisible(ref in ('J1', 'J2', 'J3'))


def back_art(board):
    B = pcbnew.B_SilkS
    # LiPo goes here (top-left of the back, no parts)
    for a_, b_ in (((12, -38), (39, -38)), ((39, -38), (39, -15)), ((39, -15), (12, -15)), ((12, -15), (12, -38))):
        shape_line(board, B, a_, b_, 0.15)
    text(board, B, 'LUCHTMETER', (25.5, -32.0), size=2.4, th=0.38, mirror=True, bold=True)
    text(board, B, 'LiPo 300 mAh hier', (25.5, -28.0), size=0.9, th=0.15, mirror=True)
    text(board, B, 'CO2 · temp · vocht · licht · NFC', (25.5, -25.5), size=0.8, th=0.14, mirror=True)
    text(board, B, 'Kobe Vanrobaeys & varol56 · 2026', (25.5, -23.0), size=0.8, th=0.14, mirror=True)
    leaf(board, B, (25.5, -18.5), 0.3)


def nfc_coil(board):
    """the coil itself is the net-tie footprint ANT1 (lucht:NFC_Coil); here only the copper-free area around it"""
    c = design.NFC
    x0, y0, x1, y1 = c['x0'], c['y0'], c['x1'], c['y1']
    keepout(board, rect(x0 - 1.0, y0 - 1.0, x1 + 1.0, min(y1 + 1.0, Y1 - 0.2)), [pcbnew.F_Cu],
            tracks=True, vias=True, pours=False, name='NFC antenne: geen sporen')
    # B.Cu bridge from the inner end (PTH pad 2 of ANT1) out of the coil
    p_ = c['w'] + c['s']; k = c['turns'] - 1
    ex, ey = x0 + k * p_ + p_, y0 + k * p_ + p_
    ant = [q for q in board.GetFootprints() if q.GetReference() == 'ANT1'][0]
    pad2 = [q for q in ant.Pads() if q.GetNumber() == '2'][0]
    ex, ey = pcbnew.ToMM(pad2.GetPosition().x) - OX, pcbnew.ToMM(pad2.GetPosition().y) - OY
    track(board, 'NFC_AC1', (ex, ey), (x1 + 2.0, ey), 0.4, layer=pcbnew.B_Cu)
    # copper-free under and around the coil (no planes = no eddy currents)
    keepout(board, rect(x0 - 1.5, y0 - 1.5, x1 + 1.5, min(y1 + 1.5, Y1 - 0.2)), [pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu, pcbnew.F_Cu],
            tracks=False, vias=False, pours=True, name='NFC antenne: geen koper')


def leaf(board, layer, c, s):
    """simple leaf (clean air) on the back"""
    cx, cy = c
    pts = [(cx + 6 * s * math.sin(math.pi * i / 24) * (1 if k == 0 else -1), cy - 8 * s + 16 * s * i / 24)
           for k in (0, 1) for i in (range(25) if k == 0 else range(24, -1, -1))]
    for p0, p1 in zip(pts, pts[1:] + pts[:1]):
        shape_line(board, layer, p0, p1, 0.3)
    shape_line(board, layer, (cx, cy - 8 * s), (cx, cy + 10 * s), 0.3)
    for i in range(1, 5):
        y = cy - 6 * s + 3 * s * i
        shape_line(board, layer, (cx, y), (cx + 3.5 * s, y - 2.5 * s), 0.2)
        shape_line(board, layer, (cx, y), (cx - 3.5 * s, y - 2.5 * s), 0.2)


if __name__ == '__main__':
    build()
    print('board written')
    sys.stdout.flush(); os._exit(0)   # KiCad's SWIG objects can crash Python at shutdown
