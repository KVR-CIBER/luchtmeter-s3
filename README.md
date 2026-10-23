# Luchtmeter S3 (v2.0)

By **Kobe Vanrobaeys** ([@KVR-CIBER](https://github.com/KVR-CIBER)) and co-inventor **[@varol56](https://github.com/varol56)**.

ESP32-S3 air-quality meter behind a **4.3" 800x480 IPS capacitive touchscreen**, LiPo battery, deep sleep, NFC tag and
Home Assistant (ESPHome). The front is only the screen, a small light window and the NFC spot; every part sits on the back.

| Block | Part |
|---|---|
| Brain | **ESP32-S3-WROOM-1U-N16R8**: external 2.4 GHz antenna (U.FL) at the top of the case, the best WiFi possible |
| Screen | **Waveshare 4.3inch Capacitive Touch LCD** (art. 16249, IPS 800x480, GT911): screwed (M2) onto its own 4.1 mm standoffs; 40-pin FFC to J1 |
| CO2 | Sensirion **SCD41** (photoacoustic, 400-5000 ppm), behind the back vents |
| Temperature / humidity | Sensirion **SHT45** (+-0.1 C) on a slotted, copper-free tongue (no heat from the ESP/charger) |
| Light | **LTR-303ALS** on the front, behind a light pipe in the case |
| NFC | **ST25DV04K** + 8-turn antenna coil on the board (3.5 uH + 10 pF). A phone tap can wake the meter (GPO -> IO16) |
| Charging | TI **BQ24075**, ~250 mA for the 300 mAh LiPo (R5 3.6k), power path: works while charging. Red LED = charging, green = USB |
| Battery | LiPo soldered to **BAT+ / BAT-**, extra DW01A protection |
| 3.3 V / 5 V | XC6220 LDO (8 uA) / TPS61023 boost for the screen (off in deep sleep) |
| Test points | **TP1-TP13** on the back, 1.5 mm pads in one row with the net name in silkscreen: GND, VBUS, VBAT, VSYS, 3V3, 3V3_SW, V5D, TP_3V3, SDA0, SCL0, SDA1, SCL1, GND (issue #1) |
| Probe connector | **J3** (1x4, 2.54 mm, not assembled) at the left edge next to the USB-C: GND / 3V3 / SDA1 / SCL1 (Qwiic order) on the second I2C bus, for an external SHT4x probe (issue #2). 3V3 = TP_3V3, the screen's 3.3 V, the same rail as the I2C1 pull-ups |

Board 106 x 88 mm, 4 layers, notch on the right for the screen's 2x20 header. Checks: **DRC 0, unconnected 0, ERC 0, parity 0**.
(All routed by the tools: Freerouting + `tools/finisher.py`. Freerouting runs multithreaded and is not deterministic;
if `build_all.sh` ends with open connections, run it again.)

## Check before ordering
1. **FFC cable** between the screen (H1) and J1: J1 is turned so pin 1 is on the same side as on the screen; the cable makes
   a U-fold. Check with the cable that comes with the screen (same-side or opposite-side contacts) before soldering.
2. **NFC tuning**: C23 = 10 pF is calculated; the best value can be 8-15 pF (test with the ST "NFC Tap" app).

## Probe on J3 (issue #2)
J3 is on the touch bus (I2C1, GPIO7/8, GT911 at 0x5D) and not on the sensor bus, because an SHT45 probe has the same fixed
address (0x44) as U6. Its 3V3 pin is the screen's own 3.3 V (TP_3V3), so the probe is only powered while the screen is on,
and a powered-down probe is never fed through SDA/SCL. Solder the 4 wires straight onto J3 (a standard 8.5 mm header would
touch the back plate) and lay the cable into the notch in the left wall of the case. Firmware: uncomment the `sht4x`
block on `bus_touch` in `firmware/luchtmeter.yaml`.

## Case (`case/`)
`build_case.py` (CadQuery) -> `case/out/`: `luchtmeter_voorkant.stl` (print face-down), `luchtmeter_achterplaat.stl`,
`luchtmeter_standaard.stl` (desk stand, 20 deg), STEP files, and photo renders (`foto_*.png`, KiCad raytracer).
111.6 x 93.6 x 25.6 mm. 2x M3 x 12 self-tapping screws hold back plate + PCB; 4x M2 x 5 screws hold the PCB to the screen.
The left wall has the USB-C opening and a 5 mm cable notch for the probe on J3 (`render_linkerwand.png`). `render.py`
(trimesh + matplotlib + networkx) makes the shaded case renders.

## Firmware
`firmware/luchtmeter.yaml` (ESPHome, not yet tested on hardware; `esphome config` + `esphome compile` ok with ESPHome
2026.10.0): RGB565 screen (rpi_dpi_rgb), GT911 touch, SCD41 single-shot, SHT45, LTR-303, battery %, deep sleep 5 min,
wake on WEKKEN button or NFC tap. Before 3V3_SW (GPIO15) or the screen (GPIO17) goes off, the SDA/SCL pins of that bus
(GPIO4/5, GPIO7/8) become inputs without pull-up, so the ESP32 never feeds the powered-down chips through its I/O pins;
the ESP32's internal I2C pull-ups are off (the 4k7 pull-ups on the board are on the switched rails). Optional: external
SHT4x probe on J3 (commented out). Needs a `firmware/secrets.yaml` with `wifi_ssid` / `wifi_password`.

## Files
`tools/design.py` = single source of truth; `tools/build_all.sh` rebuilds everything. JLC files in `fab/`.

## Build environment
The board files are **KiCad 10**. Tool paths come from `tools/env.sh` / `tools/kienv.py`: on macOS the defaults are
KiCad.app and brew's openjdk, anything can be overridden with `KICAD_PY`, `KICAD_CLI`, `KICAD_SHARE`, `VENV_PY`, `JAVA`.

Linux (tested on Debian 13 trixie, which only ships KiCad 9):
```sh
apt install flatpak openjdk-25-jre-headless python3-venv          # freerouting 2.4.1 needs Java 25
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.kicad.KiCad                            # KiCad 10; tools/flatpak/ wraps kicad-cli + its python
# default global library tables (normally made on the first GUI start; without them ERC warns about 'power')
flatpak run --command=sh org.kicad.KiCad -c 'cp -n /app/extensions/Library/template/*-lib-table $XDG_CONFIG_HOME/kicad/10.0/'
python3 -m venv .venv && .venv/bin/pip install numpy shapely matplotlib cadquery trimesh networkx
python3 -m venv .venv-esphome && .venv-esphome/bin/pip install esphome
tools/build_all.sh                                                 # board + schematic + routing + checks + fab/
.venv/bin/python case/build_case.py && .venv/bin/python case/render.py
cd firmware && ../.venv-esphome/bin/esphome compile luchtmeter.yaml
```
The flatpak sandbox has its own `/tmp`: give kicad-cli output paths inside the repo.

## Authors
- Kobe Vanrobaeys ([@KVR-CIBER](https://github.com/KVR-CIBER))
- [@varol56](https://github.com/varol56), co-inventor
