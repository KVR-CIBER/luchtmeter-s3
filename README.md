# Luchtmeter S3 (v1.0)

ESP32-S3 air-quality meter with a 2.8" touchscreen, a LiPo battery and Home Assistant (ESPHome).

| Block | Part |
|---|---|
| Brain | ESP32-S3-WROOM-1-N16R8 (WiFi, native USB) |
| CO2 | Sensirion **SCD41** (real photoacoustic CO2, 400-5000 ppm) |
| Temperature / humidity | Sensirion **SHT45** (+-0.1 C) on a slotted, thermally isolated tongue |
| Light | Lite-On **LTR-303ALS** (just below the screen, behind a window in the case) |
| Screen | 2.8" ILI9341 + XPT2046 touch module **MSP2807** on a 1x14 female header, 11 mm standoffs |
| Charging | TI **BQ24075** (power path: runs on USB while charging), **~250 mA** for a 300 mAh LiPo (R11 3.6k; 1k = 0.9 A) |
| Battery | LiPo soldered to **BAT+ / BAT-**, extra protection DW01A + 2x AO3400A |
| 3.3 V | Torex XC6220 LDO (8 uA quiescent) |
| Sleep | screen + sensors on a switched rail (3V3_SW, IO18 low = on), WEKKEN button on IO4 wakes it |

Board 58 x 124 mm, 4 layers (F / GND / 3V3 / B), all parts on the top side. Checks: DRC 0, unconnected 0, ERC 0, parity 0.

## Pins
| GPIO | | GPIO | |
|---|---|---|---|
| 1 / 2 | I2C SDA / SCL | 41 | light sensor INT |
| 12 / 11 / 13 | LCD SCK / MOSI / MISO | 10 / 9 / 14 | LCD CS / DC / RST |
| 21 | backlight (low = on, PWM) | 7 / 6 / 5 | touch CLK / DIN / DO |
| 47 / 48 | touch CS / IRQ | 18 | PWR_EN (low = screen + sensors on) |
| 4 | WEKKEN button (wake) | 8 | battery voltage (x 2) |
| 15 / 16 | CHG / PGOOD (low = charging / USB) | 42 | green status LED |

## Firmware
`firmware/luchtmeter.yaml` (ESPHome, not tested on hardware yet): wakes every 5 min, measures, sends to Home Assistant,
shows CO2 (green / orange / red), sleeps. Stays awake on USB. Before deep sleep the rail is switched off.
Estimate with a 300 mAh LiPo: about a week at 5 min, about 3 weeks at 15 min (screen use costs the most).

## Files
`tools/design.py` is the single source of truth; `tools/build_all.sh` rebuilds everything. JLC files in `fab/`.
