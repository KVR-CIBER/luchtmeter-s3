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

Board 106 x 88 mm, 4 layers, notch on the right for the screen's 2x20 header. Checks: **DRC 0, unconnected 0, ERC 0, parity 0**.
(The last 3V3_SW link at the SHT45 tongue was added by hand after the routers; regenerating re-routes.)

## Check before ordering
1. **FFC cable** between the screen (H1) and J1: J1 is turned so pin 1 is on the same side as on the screen; the cable makes
   a U-fold. Check with the cable that comes with the screen (same-side or opposite-side contacts) before soldering.
2. **NFC tuning**: C23 = 10 pF is calculated; the best value can be 8-15 pF (test with the ST "NFC Tap" app).

## Case (`case/`)
`build_case.py` (CadQuery) -> `case/out/`: `luchtmeter_voorkant.stl` (print face-down), `luchtmeter_achterplaat.stl`,
`luchtmeter_standaard.stl` (desk stand, 20 deg), STEP files, and photo renders (`foto_*.png`, KiCad raytracer).
111.6 x 93.6 x 25.6 mm. 2x M3 x 12 self-tapping screws hold back plate + PCB; 4x M2 x 5 screws hold the PCB to the screen.

## Firmware
`firmware/luchtmeter.yaml` (ESPHome, not yet tested): RGB565 screen (rpi_dpi_rgb), GT911 touch, SCD41 single-shot, SHT45,
LTR-303, battery %, deep sleep 5 min, wake on WEKKEN button or NFC tap.

## Files
`tools/design.py` = single source of truth; `tools/build_all.sh` rebuilds everything. JLC files in `fab/`.

## Authors
- Kobe Vanrobaeys ([@KVR-CIBER](https://github.com/KVR-CIBER))
- [@varol56](https://github.com/varol56), co-inventor
