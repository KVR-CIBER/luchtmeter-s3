"""Screen content of the Luchtmeter (800x480 drawn at 2x) for every frame of the film -> video/ui/0001.png ..."""
import os, math
from PIL import Image, ImageDraw, ImageFont
import timeline as T

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'ui')
W, H = 1600, 960
F = lambda w, s: ImageFont.truetype(os.path.join(HERE, 'fonts', f'Inter-{w}.ttf'), s)
BIG, MID, SM, XS, LBL = F('SemiBold', 210), F('Medium', 56), F('Medium', 40), F('Regular', 30), F('SemiBold', 34)
BG, CARD, GREY, WHITE = (8, 10, 14), (22, 26, 33), (138, 146, 158), (240, 243, 247)


def level(c):
    if c < 800:
        return (46, 204, 113), 'Goede lucht'
    if c < 1200:
        return (243, 156, 18), 'Matig · zet een raam open'
    return (231, 76, 60), 'Slecht · verluchten!'


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def frame(f):
    s = T.ui_state(f)
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    col, word = level(s['co2'])
    # top bar: clock, wifi, Home Assistant, battery
    d.text((60, 44), '14:32', font=SM, fill=WHITE)
    x = W - 60
    bw = 70; d.rounded_rectangle((x - bw, 50, x, 84), 7, outline=GREY, width=3)
    d.rectangle((x - bw + 6, 56, x - bw + 6 + int((bw - 12) * s['bat'] / 100), 78), fill=WHITE)
    d.text((x - bw - 16, 46), f"{s['bat']}%", font=XS, fill=GREY, anchor='ra')
    x -= bw + 120
    for i, r in enumerate((14, 26, 38)):                                  # wifi arcs
        a = 255 if not s['sending'] or (f // 6 + i) % 3 else 120
        d.arc((x - r, 92 - r, x + r, 92 + r), 225, 315, fill=mix(BG, WHITE, a / 255), width=5)
    d.ellipse((x - 5, 86, x + 5, 96), fill=WHITE)
    ha = (65, 189, 245) if s['sending'] else GREY
    d.text((x - 60, 46), 'Home Assistant', font=XS, fill=ha, anchor='ra')
    # CO2 ring + big number
    cx, cy, R = 470, 500, 300
    d.arc((cx - R, cy - R, cx + R, cy + R), 135, 405, fill=CARD, width=34)
    frac = T.clamp((s['co2'] - 400) / 1600)
    d.arc((cx - R, cy - R, cx + R, cy + R), 135, 135 + 270 * frac, fill=col, width=34)
    d.text((cx, cy - 10), f"{s['co2']:.0f}", font=BIG, fill=WHITE, anchor='mm')
    d.text((cx, cy + 140), 'CO₂  ppm', font=MID, fill=GREY, anchor='mm')
    d.text((cx, cy + 300), word, font=LBL, fill=col, anchor='mm')
    # right: three tiles + history graph
    tiles = [('Temperatuur', f"{s['temp']:.1f} °C"), ('Vochtigheid', f"{s['hum']:.0f} %"), ('Licht', f"{s['lux']} lux")]
    for i, (k, v) in enumerate(tiles):
        y = 150 + i * 165
        d.rounded_rectangle((900, y, W - 60, y + 140), 26, fill=CARD)
        d.text((940, y + 22), k, font=XS, fill=GREY)
        d.text((940, y + 58), v, font=MID, fill=WHITE)
    gy0, gy1 = 660, 900
    d.rounded_rectangle((900, gy0, W - 60, gy1), 26, fill=CARD)
    d.text((940, gy0 + 24), 'CO₂ laatste uur', font=XS, fill=GREY)
    base = [600 + 25 * math.sin(i * 0.7) for i in range(30)]
    n = s['hist_n']
    vals = base[n:] + [612 + (s['co2'] - 612) * (j + 1) / max(n, 1) for j in range(n)]
    pts = [(940 + i * (W - 60 - 40 - 940) / 29, gy1 - 30 - (v - 400) / 1200 * (gy1 - gy0 - 100)) for i, v in enumerate(vals)]
    d.line(pts, fill=col, width=6, joint='curve')
    d.ellipse((pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10), fill=col)
    if s['woke']:
        d.rounded_rectangle((560, 60, 1040, 120), 30, fill=(28, 70, 120))
        d.text((800, 90), 'Gewekt via NFC', font=XS, fill=WHITE, anchor='mm')
    if s['bright'] < 1:
        im = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), im, s['bright'])
    return im


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in range(1, T.N + 1):
        frame(f).save(os.path.join(OUT, f'{f:04d}.png'), optimize=False, compress_level=3)
    print('ui frames', T.N)
