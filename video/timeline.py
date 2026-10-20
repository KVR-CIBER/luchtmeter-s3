"""Shared timeline of the Luchtmeter S3 film (30 fps, 36 s): used by the screen UI, the Blender scene and the overlays."""
FPS, N = 30, 1080

# scene blocks (first frame, last frame)
HERO = (1, 150)          # assembled, slow orbit, screen on
EXPLODE = (150, 330)     # turn to the back, case opens, parts separate
SENSORS = (330, 510)     # close-up of the back: sensors light up
CLOSE = (510, 630)       # parts go back together, camera to the front
LIVE = (630, 780)        # values change, CO2 rises -> red, data to Home Assistant
SLEEP = (780, 870)       # screen goes dark, deep sleep
TAP = (870, 990)         # phone taps the NFC spot -> wakes up
END = (990, 1080)        # end card


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ramp(f, a, b):
    """0 before frame a, 1 after frame b, smooth in between"""
    return ease((f - a) / float(b - a))


def ui_state(f):
    """what the screen shows at frame f"""
    co2 = 612.0
    co2 += 728.0 * ramp(f, LIVE[0] + 10, LIVE[1] - 10)                 # 612 -> 1340 ppm
    awake_again = f >= 912
    if awake_again:
        co2 = 1340.0 - 160.0 * ramp(f, 912, 960)                          # fresh measurement after the wake-up
    bright = 1.0 - ramp(f, SLEEP[0] + 6, SLEEP[0] + 24)                   # fades to black
    bright = max(bright, ramp(f, 906, 918))                               # NFC tap wakes it
    temp = 21.4 + 0.6 * ramp(f, LIVE[0], LIVE[1])
    hum = 48 + 4 * ramp(f, LIVE[0], LIVE[1])
    lux = 312
    hist_n = int(clamp((f - LIVE[0]) / 6.0, 0, 30))
    return dict(co2=co2, temp=temp, hum=hum, lux=lux, bright=bright, bat=78, sending=LIVE[0] + 40 < f < LIVE[1],
                hist_n=hist_n, woke=awake_again and f < 990)
