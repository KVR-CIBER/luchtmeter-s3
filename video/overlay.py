"""Titles + part labels over the rendered frames: frames/NNNN.png + labels.json -> final/NNNN.png"""
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import timeline as T

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, DST = os.path.join(HERE, 'frames'), os.path.join(HERE, 'final')
LAB = json.load(open(os.path.join(HERE, 'labels.json')))
F = lambda w, s: ImageFont.truetype(os.path.join(HERE, 'fonts', f'Inter-{w}.ttf'), s)
TITLE, SUB, LBL, LBS, END1, END2 = F('SemiBold', 120), F('Regular', 56), F('SemiBold', 50), F('Regular', 38), F('Bold', 170), F('Medium', 60)
WHITE, GREY, CYAN = (245, 247, 250), (170, 178, 190), (90, 200, 255)

CAPTIONS = [  # first, last frame, title, subtitle
    (12, 140, 'Luchtmeter S3', 'CO₂ · temperatuur · vocht · licht'),
    (178, 322, 'Alles zit achter het scherm', '4,3" touchscreen · ESP32-S3 · LiPo 300 mAh'),
    (338, 505, 'De sensoren', 'Elk onderdeel op de achterkant van de print'),
    (520, 622, 'Dicht en klaar', 'Geen schroef of knop aan de voorkant'),
    (640, 772, 'Live naar Home Assistant', 'Via wifi met ESPHome, wordt rood als je moet verluchten'),
    (790, 866, 'Diepe slaap', 'Scherm en sensoren uit, wakker om de 5 minuten'),
    (880, 984, 'Tik met je gsm', 'De NFC-tag wekt het scherm meteen'),
]
LABELS = [  # anchor, first, last, text, detail
    ('ESP32-S3', 350, 500, 'ESP32-S3', 'wifi + bluetooth, externe antenne'),
    ('SCD41', 364, 500, 'SCD41', 'CO₂, fotoakoestisch'),
    ('SHT45', 378, 500, 'SHT45', 'temperatuur + vocht'),
    ('NFC-chip', 392, 500, 'ST25DV', 'NFC-tag'),
    ('Laadchip', 406, 500, 'BQ24075', 'laden via USB-C'),
    ('USB-C', 420, 500, 'USB-C', 'opladen + flashen'),
    ('LiPo', 250, 322, 'LiPo 300 mAh', ''),
    ('NFC', 895, 980, 'NFC', ''),
]


def fade(f, a, b, n=12):
    return T.clamp(min((f - a) / n, (b - f) / n))


def text_shadow(layer, xy, s, font, fill, alpha, anchor='la'):
    sh = Image.new('RGBA', layer.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((xy[0] + 3, xy[1] + 4), s, font=font,
                                                                              fill=(0, 0, 0, int(160 * alpha)), anchor=anchor)
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(layer).text(xy, s, font=font, fill=(*fill, int(255 * alpha)), anchor=anchor)


def frame(f):
    im = Image.open(os.path.join(SRC, f'{f:04d}.png')).convert('RGBA'); W, H = im.size
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for a, b, t, s in CAPTIONS:
        al = fade(f, a, b)
        if al > 0:
            dy = int(30 * (1 - al))
            d.rectangle((150, 170 + dy, 160, 380 + dy), fill=(*CYAN, int(255 * al)))
            text_shadow(lay, (200, 160 + dy), t, TITLE, WHITE, al)
            text_shadow(lay, (204, 310 + dy), s, SUB, (205, 212, 222), al)
    for anc, a, b, t, s in LABELS:
        al = fade(f, a, b, 10)
        p = LAB[str(f)].get(anc)
        if al <= 0 or not p or p[2] <= 0:
            continue
        x, y = p[0] * W, p[1] * H
        dx, dy = x - W * 0.5, y - H * 0.45; n = math.hypot(dx, dy) or 1
        lx, ly = x + dx / n * 260, y + dy / n * 200 - 60
        right = lx >= x
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=(*CYAN, int(255 * al)))
        d.ellipse((x - 22, y - 22, x + 22, y + 22), outline=(*CYAN, int(140 * al)), width=3)
        ex = lx + (30 if right else -30)
        d.line([(x, y), (lx, ly), (ex, ly)], fill=(*WHITE, int(220 * al)), width=4)
        anchor = 'ls' if right else 'rs'
        tx = ex + (14 if right else -14)
        bb = [d.textbbox((tx, ly - 6), t, font=LBL, anchor=anchor)]
        if s:
            bb.append(d.textbbox((tx, ly + 48), s, font=LBS, anchor=anchor))
        x0, y0 = min(q[0] for q in bb) - 22, min(q[1] for q in bb) - 16
        x1, y1 = max(q[2] for q in bb) + 22, max(q[3] for q in bb) + 18
        d.rounded_rectangle((x0, y0, x1, y1), 18, fill=(8, 10, 14, int(185 * al)))
        text_shadow(lay, (ex + (14 if right else -14), ly - 6), t, LBL, WHITE, al, anchor)
        if s:
            text_shadow(lay, (ex + (14 if right else -14), ly + 48), s, LBS, (200, 208, 218), al, anchor)
    if 890 <= f <= 940 and LAB[str(f)]['NFC'][2] > 0:                       # NFC waves at the tap
        x, y = LAB[str(f)]['NFC'][0] * W, LAB[str(f)]['NFC'][1] * H
        for k in range(3):
            r = ((f - 890) * 9 + k * 70) % 260 + 30
            d.ellipse((x - r, y - r, x + r, y + r), outline=(*CYAN, int(200 * (1 - r / 290))), width=6)
    if f >= T.END[0]:
        al = fade(f, T.END[0] + 4, T.N + 40, 20)
        veil = Image.new('RGBA', im.size, (4, 5, 8, int(200 * al))); lay = Image.alpha_composite(veil, lay); d = ImageDraw.Draw(lay)
        text_shadow(lay, (W / 2, H / 2 - 90), 'LUCHTMETER S3', END1, WHITE, al, 'mm')
        text_shadow(lay, (W / 2, H / 2 + 70), 'Kobe Van Robaeys  &  varol56', END2, CYAN, al, 'mm')
        text_shadow(lay, (W / 2, H / 2 + 170), 'ESP32-S3 · ESPHome · Home Assistant', SUB, GREY, al, 'mm')
    return Image.alpha_composite(im, lay).convert('RGB')


if __name__ == '__main__':
    os.makedirs(DST, exist_ok=True)
    fs = [int(a) for a in sys.argv[1:]] or range(1, T.N + 1)
    for f in fs:
        frame(f).save(os.path.join(DST, f'{f:04d}.png'), compress_level=1)
    print('overlay done', len(fs))
