"""Fabrication outputs for JLCPCB: gerbers + drill (zip), BOM and CPL (pick & place), PDF schematic, renders."""
import os, csv, subprocess, zipfile, shutil, collections
import design

PRJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KC = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PCB = os.path.join(PRJ, 'luchtmeter.kicad_pcb')
SCH = os.path.join(PRJ, 'luchtmeter.kicad_sch')
FAB = os.path.join(PRJ, 'fab')


# JLCPCB / LCSC part numbers, checked for stock on 2026-10-17 (tools/jlc_stock.py)
LCSC = {'ESP32-S3-WROOM-1-N16R8': 'C2913202', '22u': 'C29277', '100n': 'C14663', '10k': 'C25804', '1u': 'C15849',
        '1k': 'C21190', 'groen': 'C12624', 'rood laden': 'C2286', '100k': 'C25803', 'USB-C': 'C165948', '5k1': 'C23186',
        'USBLC6-2SC6': 'C2687116', 'BQ24075': 'C15464', '4u7': 'C132173', '10u': 'C15850', '1.1k': 'C22764', '3.6k': 'C22980',
        'DW01A': 'C351410', '100': 'C22775', 'AO3400A': 'C20917', 'AO3401A': 'C15127', '1M': 'C22935',
        'XC6220B331MR': 'C86534', '47n': 'C107093', 'SCHERM': 'C41417326', 'LTR-303ALS-01': 'C364577', '4k7': 'C23162',
        'SCD41-D-R2': 'C3659294', 'SHT45': 'C5221601', 'I2C': 'C160404', 'RESET': 'C72443', 'BOOT': 'C72443',
        'WEKKEN': 'C72443', 'BATTERIJ': '(solder pads, no part)',
        'ESP32-S3-WROOM-1U-N16R8': 'C3013946', 'SCHERM': 'C202114', 'TPS61023': 'C919459', '1uH': 'C408332',
        '732k': 'C23239', 'ST25DV04K': 'C155601', '10p': 'C1634', 'groen USB': 'C12624', 'NFC antenne': '(PCB copper, no part)'}


def lcsc(value):
    return LCSC.get(value, '')


def run(*a):
    r = subprocess.run([KC, *a], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
    return r


def main():
    shutil.rmtree(FAB, ignore_errors=True)
    g = os.path.join(FAB, 'gerbers'); os.makedirs(g)
    layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
    run('pcb', 'export', 'gerbers', '--layers', layers, '--subtract-soldermask', '--no-protel-ext', '-o', g + '/', PCB)
    run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2',
        '-o', g + '/', PCB)
    with zipfile.ZipFile(os.path.join(FAB, 'luchtmeter_gerbers_JLCPCB.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(g)):
            z.write(os.path.join(g, f), f)
    # pick & place
    pos = os.path.join(FAB, 'pos_raw.csv')
    run('pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '--exclude-dnp', '-o', pos, PCB)
    with open(pos) as f, open(os.path.join(FAB, 'luchtmeter_CPL_JLCPCB.csv'), 'w', newline='') as o:
        w = csv.writer(o); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in csv.DictReader(f):
            if r['Ref'].startswith('H') or r['Ref'] in design.DNP:
                continue
            w.writerow([r['Ref'], r['PosX'] + 'mm', r['PosY'] + 'mm', 'Top' if r['Side'] == 'top' else 'Bottom', r['Rot']])
    os.remove(pos)
    # BOM grouped by value + footprint + MPN
    groups = collections.OrderedDict()
    for p in design.parts:
        if p['ref'].startswith('H') or p['dnp']:
            continue
        k = (p['value'], p['fp'].split(':')[1], p['mpn'])
        groups.setdefault(k, []).append(p['ref'])
    with open(os.path.join(FAB, 'luchtmeter_BOM_JLCPCB.csv'), 'w', newline='') as o:
        w = csv.writer(o); w.writerow(['Comment', 'Designator', 'Footprint', 'Quantity', 'MPN / note', 'LCSC Part #'])
        for (v, fp, mpn), refs in groups.items():
            w.writerow([v, ','.join(refs), fp, len(refs), mpn, lcsc(v)])
    run('sch', 'export', 'pdf', '-o', os.path.join(FAB, 'luchtmeter_schema.pdf'), SCH)
    for side in ('top', 'bottom'):
        run('pcb', 'render', '--side', side, '--width', '2400', '--height', '1400', '--quality', 'high',
            '--background', 'opaque', '-o', os.path.join(FAB, f'render_{side}.png'), PCB)
    run('pcb', 'render', '--side', 'top', '--rotate', '-35,0,25', '--zoom', '1.1', '--width', '2400', '--height', '1500',
        '--quality', 'high', '--background', 'opaque', '-o', os.path.join(FAB, 'render_3d.png'), PCB)
    print('fab outputs in', FAB, sorted(os.listdir(FAB)))


if __name__ == '__main__':
    main()
