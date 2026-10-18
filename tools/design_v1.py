"""LUCHTMETER S3: ESP32-S3 air-quality meter with a 2.8" SPI touchscreen. Single source of truth for parts, nets, placement.

Board coordinates in mm, origin = board centre, +y = down in KiCad.
Portrait board 58 x 124 mm:
  * top 86 mm  : the 2.8" ILI9341 + XPT2046 touch module (MSP2807, 50 x 86 mm) sits 11 mm above the board on a
                 1x14 female header + 4x M3 standoffs; the ESP32-S3, USB-C and 3.3 V regulator live underneath it.
  * power: USB-C -> BQ24075 charger/power path -> 18650 cell(s) soldered to BAT+/BAT- (DW01A protection),
             XC6220 3.3 V LDO (8 uA), display + sensors on a switched rail (3V3_SW) for deep sleep.
  * bottom 35 mm: sensor zone, away from the heat of the ESP32/regulator:
                 SCD41 (real CO2 + RH/T), SHT45 (+-0.1 C) on a slotted, copper-free tongue, LTR-303ALS light
                 sensor just below the screen (looks through a window in the case), Qwiic, RESET/BOOT.

Each part: ref, symbol (lib:name), footprint (lib:name), value, pin->net, (x, y, rot), extra.
Pins not listed are no-connect.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_W, BOARD_H, CORNER_R = 58.0, 124.0, 4.0
BOARD_Y = (-62.0, 62.0)
ESP = (0.0, -49.25)            # module flush with the top edge, antenna (top 6 mm) kept copper-free

# 2.8" display module (MSP2807): 50 x 86 mm, holes 44 x 76.08 mm (3 mm from the top), header 2 mm from the bottom
LCD_X0, LCD_Y0 = -25.0, -59.0                          # top-left corner of the module
LCD_HOLES = [(LCD_X0 + 3 + dx, LCD_Y0 + 3 + dy) for dy in (0, 76.08) for dx in (0, 44)]
LCD_HDR = (LCD_X0 + 8.49, LCD_Y0 + 84.0)              # pin 1 (VCC), pins run to +x at 2.54 mm
LCD_STANDOFF = 11.0                                    # board top -> module PCB bottom (2.5 mm male + 8.5 mm female header)

# heat barrier + thermally isolated tongue for the SHT45 (slots are Edge.Cuts, 1.0 mm wide)
SLOTS = [[(-14.0, 35.5), (14.0, 35.5)],               # under the light sensor: blocks heat from the top half
         [(13.0, 57.0), (13.0, 45.0), (26.0, 45.0)]]   # L-shaped slot around the SHT45 tongue
SLOT_W = 1.0
TONGUE = (13.6, 45.6, 29.0, 62.0)                      # copper-free except the SHT45 traces

parts = []


def P(ref, sym, fp, value, pins, at, mpn='', lcsc='', group='', dnp=False, side='F'):
    parts.append(dict(ref=ref, sym=sym, fp=fp, value=value, pins={str(k): v for k, v in pins.items()},
                      at=at, mpn=mpn, lcsc=lcsc, group=group, dnp=dnp, side=side))


R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
USBC = 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12'
KMR2 = 'Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2'


def R(ref, val, a, b, at, g, mpn=''):
    P(ref, 'Device:R', R0603, val, {1: a, 2: b}, at, mpn=mpn or f'0603 {val} 1%', group=g)


def C(ref, val, a, b, at, g, fp=C0603, mpn=''):
    size = fp.split(':')[1].split('_')[1]
    kind = 'X7R' if val.endswith(('n', 'p')) or val == '100n' else 'X5R'
    P(ref, 'Device:C', fp, val, {1: a, 2: b}, at, mpn=mpn or f'{size} {val} {kind} ceramic', group=g)


# ---------------------------------------------------------------- ESP32-S3 (pin numbers of the WROOM-1 module)
# LCD on its own SPI pins (bottom row of the module), touch controller on separate pins (no shared MISO trouble)
G = 'ESP32-S3'
P('U1', 'RF_Module:ESP32-S3-WROOM-1', 'RF_Module:ESP32-S3-WROOM-1', 'ESP32-S3-WROOM-1-N16R8',
  {1: 'GND', 40: 'GND', 41: 'GND', 2: '3V3', 3: 'ESP_EN', 27: 'ESP_IO0', 13: 'USB_DM', 14: 'USB_DP',
   17: 'LCD_DC', 18: 'LCD_CS', 19: 'LCD_MOSI', 20: 'LCD_SCK', 21: 'LCD_MISO', 22: 'LCD_RST', 23: 'LCD_BL',
   5: 'T_DO', 6: 'T_DIN', 7: 'T_CLK', 24: 'T_CS', 25: 'T_IRQ',
   39: 'SDA', 38: 'SCL', 34: 'ALS_INT', 35: 'LED_ST',
   4: 'WAKE', 11: 'PWR_EN', 12: 'VBAT_SENSE', 8: 'CHG', 9: 'PGOOD'},
  (ESP[0], ESP[1], 0), mpn='ESP32-S3-WROOM-1-N16R8', group=G)
C('C1', '22u', '3V3', 'GND', (-12.4, -53.0, 90), G, fp=C0805)
C('C2', '100n', '3V3', 'GND', (-14.4, -53.0, 90), G)
R('R1', '10k', '3V3', 'ESP_EN', (-12.4, -47.6, 90), G)
C('C3', '1u', 'ESP_EN', 'GND', (-14.2, -47.6, 90), G)
R('R2', '10k', '3V3', 'ESP_IO0', (12.4, -38.5, 90), G)
R('R3', '1k', 'LED_ST', 'LED_ST_A', (12.4, -44.0, 90), G)
P('D1', 'Device:LED', 'LED_SMD:LED_0603_1608Metric', 'groen', {1: 'GND', 2: 'LED_ST_A'}, (14.4, -44.0, 270),
  mpn='LED 0603 green (status)', group=G)

R('R10', '100k', '3V3', 'WAKE', (-12.4, -43.4, 90), G)
C('C14', '100n', 'WAKE', 'GND', (-14.2, -43.4, 90), G)

# ---------------------------------------------------------------- USB-C (charging + native USB for flashing / serial)
G = 'USB-C'
P('J2', 'Connector:USB_C_Receptacle_USB2.0_16P', USBC, 'USB-C',
  {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND', 'A4': 'VBUS', 'A9': 'VBUS',
   'B4': 'VBUS', 'B9': 'VBUS', 'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP',
   'A7': 'USB_DM', 'B7': 'USB_DM'}, (-25.2, -36.0, 270), mpn='HRO TYPE-C-31-M-12', group=G)
R('R4', '5k1', 'CC1', 'GND', (-16.6, -41.4, 0), G)
R('R5', '5k1', 'CC2', 'GND', (-16.6, -30.6, 0), G)
P('U2', 'Power_Protection:USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6', 'USBLC6-2SC6',
  {1: 'USB_DP', 6: 'USB_DP', 3: 'USB_DM', 4: 'USB_DM', 2: 'GND', 5: 'VBUS'}, (-16.0, -36.0, 90), mpn='USBLC6-2SC6', group=G)

# ---------------------------------------------------------------- Li-ion charger with power path (TI BQ24075)
# USB present: the board runs from USB and the cell charges at ~250 mA (ISET 3.6k, for a 300 mAh LiPo), input limited to 1.4 A (ILIM 1.1k).
# No USB: the cell feeds OUT (= VSYS) through the internal FET. Safety timers on (TMR open), TS = fixed 10k (no NTC).
G = 'Laden (BQ24075)'
CH = (-14.0, -21.0)
P('U7', 'Battery_Management:BQ24075RGT', 'Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm', 'BQ24075',
  {1: 'CH_TS', 2: 'VBAT', 3: 'VBAT', 4: 'GND', 5: 'VSYS', 6: 'GND', 7: 'PGOOD', 8: 'GND', 9: 'CHG', 10: 'VSYS',
   11: 'VSYS', 12: 'CH_ILIM', 13: 'VBUS', 15: 'GND', 16: 'CH_ISET', 17: 'GND'},
  (CH[0], CH[1], 0), mpn='TI BQ24075RGTR (1.5 A Li-ion charger + power path)', group=G)
C('C15', '4u7', 'VBUS', 'GND', (CH[0] - 5.0, CH[1] - 2.0, 90), G, fp=C0805)
C('C16', '10u', 'VSYS', 'GND', (CH[0] + 4.6, CH[1] - 2.0, 90), G, fp=C0805)
C('C17', '4u7', 'VBAT', 'GND', (CH[0] + 4.6, CH[1] + 2.4, 90), G, fp=C0805)
R('R11', '3.6k', 'CH_ISET', 'GND', (CH[0] - 5.0, CH[1] + 2.4, 90), G, mpn='0603 3.6k 1% (charge current ~250 mA for a 300 mAh LiPo; 1k = 0.9 A for bigger cells)')
R('R12', '1.1k', 'CH_ILIM', 'GND', (CH[0] - 3.2, CH[1] + 4.2, 90), G, mpn='0603 1.1k 1% (input limit ~1.4 A)')
R('R13', '10k', 'CH_TS', 'GND', (CH[0] - 1.4, CH[1] + 4.2, 90), G, mpn='0603 10k 1% (TS: no NTC, fixed 10k)')
R('R14', '100k', 'CHG', '3V3', (CH[0] + 0.4, CH[1] + 4.2, 90), G)
R('R15', '100k', 'PGOOD', '3V3', (CH[0] + 2.2, CH[1] + 4.2, 90), G)
R('R16', '1k', 'VSYS', 'LED_CHG_A', (CH[0] - 6.8, CH[1] + 2.4, 90), G)
P('D2', 'Device:LED', 'LED_SMD:LED_0603_1608Metric', 'rood laden', {1: 'CHG', 2: 'LED_CHG_A'}, (CH[0] - 8.6, CH[1] + 2.4, 270),
  mpn='LED 0603 red (charging)', group=G)

# ---------------------------------------------------------------- battery pads + protection (DW01A, 2x AO3400A)
# 18650 cell(s) in parallel, soldered to the BAT+ / BAT- pads. Over-discharge (2.4 V), over-charge and short protection.
G = 'Batterij + beveiliging'
BP = (12.0, -21.0)
P('J4', 'Connector_Generic:Conn_01x02', 'lucht:SolderWire_2pad_P6mm_D1.6mm_BAT', 'BATTERIJ',
  {1: 'VBAT', 2: 'BATN'}, (BP[0] + 3.0, BP[1] + 9.0, 0), mpn='solder pads for the 18650 leads (18 AWG)', group=G)
P('U8', 'Battery_Management:DW01A', 'Package_TO_SOT_SMD:SOT-23-6', 'DW01A',
  {1: 'DW_OD', 2: 'DW_CS', 3: 'DW_OC', 5: 'DW_VCC', 6: 'BATN'}, (BP[0], BP[1] - 2.5, 0), mpn='DW01A (Li-ion protection)', group=G)
R('R17', '100', 'VBAT', 'DW_VCC', (BP[0] + 3.6, BP[1] - 2.5, 90), G)
C('C18', '100n', 'DW_VCC', 'BATN', (BP[0] + 5.4, BP[1] - 2.5, 90), G)
R('R18', '1k', 'DW_CS', 'GND', (BP[0] - 3.6, BP[1] - 2.5, 90), G)
P('Q3', 'Transistor_FET:AO3400A', SOT23, 'AO3400A', {1: 'DW_OD', 2: 'BATN', 3: 'BAT_MID'}, (BP[0] - 2.0, BP[1] + 2.5, 0),
  mpn='AO3400A (discharge FET)', group=G)
P('Q4', 'Transistor_FET:AO3400A', SOT23, 'AO3400A', {1: 'DW_OC', 2: 'GND', 3: 'BAT_MID'}, (BP[0] + 2.5, BP[1] + 2.5, 0),
  mpn='AO3400A (charge FET)', group=G)
R('R19', '1M', 'VBAT', 'VBAT_SENSE', (BP[0] + 8.0, BP[1] - 2.5, 90), G, mpn='0603 1M 1% (battery voltage)')
R('R20', '1M', 'VBAT_SENSE', 'GND', (BP[0] + 9.8, BP[1] - 2.5, 90), G, mpn='0603 1M 1%')
C('C19', '100n', 'VBAT_SENSE', 'GND', (BP[0] + 11.6, BP[1] - 2.5, 90), G)

# ---------------------------------------------------------------- 3.3 V: XC6220 LDO (1 A, 8 uA quiescent, 100 mV dropout @ 200 mA)
G = '3,3 V + schakelbare voeding'
P('U3', 'Regulator_Linear:XC6220B331MR', 'Package_TO_SOT_SMD:SOT-23-5', 'XC6220B331MR',
  {1: 'VSYS', 2: 'GND', 3: 'VSYS', 5: '3V3'}, (0.0, -24.0, 0), mpn='Torex XC6220B331MR-G', group=G)
C('C4', '10u', 'VSYS', 'GND', (-3.6, -24.0, 90), G, fp=C0805)
C('C5', '22u', '3V3', 'GND', (3.6, -24.0, 90), G, fp=C0805)
C('C6', '100n', '3V3', 'GND', (5.4, -24.0, 90), G)
# 3V3_SW: display + sensors, switched off in deep sleep (PWR_EN low = on). 10k + 47n soft-start against brown-out.
P('Q2', 'Transistor_FET:AO3401A', SOT23, 'AO3401A', {1: 'PWR_G', 2: '3V3', 3: '3V3_SW'}, (0.0, -15.0, 0),
  mpn='AO3401A (load switch display + sensors)', group=G)
R('R21', '100k', 'PWR_G', '3V3', (3.6, -15.0, 90), G)
R('R22', '10k', 'PWR_EN', 'PWR_G', (5.4, -15.0, 90), G)
C('C20', '47n', 'PWR_G', '3V3', (7.2, -15.0, 90), G)
C('C21', '10u', '3V3_SW', 'GND', (-3.6, -15.0, 90), G, fp=C0805)

# ---------------------------------------------------------------- display + touch (MSP2807 header)
G = 'Scherm 2.8" ILI9341 + touch'
LCD_PINS = ['3V3_SW', 'GND', 'LCD_CS', 'LCD_RST', 'LCD_DC', 'LCD_MOSI', 'LCD_SCK', 'LCD_LED', 'LCD_MISO',
            'T_CLK', 'T_CS', 'T_DIN', 'T_DO', 'T_IRQ']
LCD_NAMES = ['VCC', 'GND', 'CS', 'RST', 'DC', 'MOSI', 'SCK', 'LED', 'MISO', 'T_CLK', 'T_CS', 'T_DIN', 'T_DO', 'T_IRQ']
P('J1', 'Connector_Generic:Conn_01x14', 'Connector_PinSocket_2.54mm:PinSocket_1x14_P2.54mm_Vertical', 'SCHERM',
  {i + 1: n for i, n in enumerate(LCD_PINS)}, (LCD_HDR[0], LCD_HDR[1], 90),
  mpn='1x14 female header 2.54 mm, 8.5 mm high (for the MSP2807 2.8" SPI touch module)', group=G)
C('C7', '10u', '3V3_SW', 'GND', (-12.0, 19.5, 0), G, fp=C0805)
C('C8', '100n', '3V3_SW', 'GND', (-8.4, 19.5, 0), G)
# backlight: P-MOSFET high side, 10k pull-up keeps it dark until the firmware drives LCD_BL low (PWM, active low)
P('Q1', 'Transistor_FET:AO3401A', SOT23, 'AO3401A', {1: 'LCD_BL', 2: '3V3_SW', 3: 'LCD_LED'}, (2.0, 18.5, 0),
  mpn='AO3401A (P-MOSFET, backlight)', group=G)
R('R6', '10k', 'LCD_BL', '3V3_SW', (5.6, 18.5, 90), G)

# ---------------------------------------------------------------- sensors (I2C: SCD41 0x62, SHT45 0x44, LTR-303 0x29)
G = 'Sensoren (I2C)'
P('U4', 'Sensor_Optical:LTR-303ALS-01', 'OptoDevice:Lite-On_LTR-303ALS-01', 'LTR-303ALS-01',
  {1: '3V3_SW', 3: 'GND', 4: 'SCL', 5: 'ALS_INT', 6: 'SDA'}, (0.0, 31.0, 0), mpn='LTR-303ALS-01 (ambient light)', group=G)
C('C9', '100n', '3V3_SW', 'GND', (3.4, 31.0, 90), G)
C('C10', '1u', '3V3_SW', 'GND', (5.2, 31.0, 90), G)
R('R7', '10k', 'ALS_INT', '3V3_SW', (-3.4, 31.0, 90), G)
R('R8', '4k7', 'SDA', '3V3_SW', (8.0, 31.0, 90), G)
R('R9', '4k7', 'SCL', '3V3_SW', (9.8, 31.0, 90), G)
P('U5', 'Sensor_Gas:SCD41-D-R2', 'Sensor:Sensirion_SCD4x-1EP_10.1x10.1mm_P1.25mm_EP4.8x4.8mm', 'SCD41-D-R2',
  {6: 'GND', 20: 'GND', 21: 'GND', 7: '3V3_SW', 19: '3V3_SW', 9: 'SCL', 10: 'SDA'}, (-8.0, 47.0, 0),
  mpn='Sensirion SCD41-D-R2 (photoacoustic CO2 400-5000 ppm + RH/T)', group=G)
C('C11', '10u', '3V3_SW', 'GND', (0.6, 44.0, 90), G, fp=C0805)
C('C12', '100n', '3V3_SW', 'GND', (2.6, 44.0, 90), G)
P('U6', 'Sensor_Humidity:SHT4x', 'Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad', 'SHT45',
  {1: 'SDA', 2: 'SCL', 3: '3V3_SW', 4: 'GND'}, (21.0, 53.5, 0), mpn='Sensirion SHT45-AD1B-R2 (+-0.1 C, +-1 %RH)', group=G)
C('C13', '100n', '3V3_SW', 'GND', (21.0, 56.4, 0), G)
P('J3', 'Connector_Generic_MountingPin:Conn_01x04_MountingPin', 'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
  'I2C', {1: 'GND', 2: '3V3_SW', 3: 'SDA', 4: 'SCL', 'MP': 'GND'}, (-24.5, 40.0, 90),
  mpn='JST SM04B-SRSS-TB (Qwiic / STEMMA QT: extra sensors, e.g. a particle sensor)', group=G)
P('SW1', 'Switch:SW_Push', KMR2, 'RESET', {1: 'ESP_EN', 2: 'GND'}, (-4.0, 57.5, 0), mpn='CK KMR221G (4.2x2.8 tact)', group=G)
P('SW3', 'Switch:SW_Push', KMR2, 'WEKKEN', {1: 'WAKE', 2: 'GND'}, (-13.0, 57.5, 0), mpn='CK KMR221G (4.2x2.8 tact): wake from deep sleep', group=G)
P('SW2', 'Switch:SW_Push', KMR2, 'BOOT', {1: 'ESP_IO0', 2: 'GND'}, (4.0, 57.5, 0), mpn='CK KMR221G (4.2x2.8 tact)', group=G)

# ---------------------------------------------------------------- mounting: the 4 display holes + 2 in the sensor zone
for i, (x, y) in enumerate(LCD_HOLES + [(-24.5, 57.5), (24.5, 39.0)], 1):
    P(f'H{i}', 'Mechanical:MountingHole', 'lucht:MountingHole_3.2mm_M3', 'M3', {}, (x, y, 0), group='Bevestiging')

NETCLASS = {
    'BAT': (['VBUS', 'VSYS', 'VBAT', 'BATN', 'BAT_MID'], 0.4, 0.15),         # charge / battery current (short tracks, fits the QFN pads)
    'PWR': (['3V3', '3V3_SW', 'GND'], 0.25, 0.15),                           # planes carry the current; thin enough for the 0.8 mm sensor pads
    'USB': (['USB_DP', 'USB_DM'], 0.25, 0.15),
}

DNP = set()


def nets():
    s = set()
    for p in parts:
        s |= set(p['pins'].values())
    return sorted(s)


def outline(inset=0.0, n=10):
    """rounded rectangle (closed), optionally inset"""
    import math
    x0, y0, x1, y1 = -BOARD_W / 2 + inset, BOARD_Y[0] + inset, BOARD_W / 2 - inset, BOARD_Y[1] - inset
    r = CORNER_R - inset; pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)))
    return pts + pts[:1]


if __name__ == '__main__':
    json.dump({'edge': outline(), 'inner': outline(0.3)}, open(os.path.join(HERE, 'outline.json'), 'w'))
    print('outline.json written')
