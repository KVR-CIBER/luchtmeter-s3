"""LUCHTMETER S3 v2: ESP32-S3 air-quality meter behind a 4.3" 800x480 IPS capacitive touchscreen.
Single source of truth for parts, nets and placement.

Board coordinates in mm, origin = board centre, seen FROM THE FRONT (screen side), +y = down.
Board 106 x 88 mm (landscape):
  * y -44..24 : behind the Waveshare 4.3" Capacitive Touch LCD (art. 16249, 106 x 68 mm). The board is screwed (M2) straight
                onto the module's own 4.1 mm standoffs; a notch on the right clears the module's 8.4 mm 2x20 header.
                The module's 40-pin FFC (RGB565 + touch, its connector H1 is left of centre) plugs into J1 on the front side.
  * y 24..44  : visible strip under the screen: LTR-303 light sensor + the NFC antenna coil (front side).
  * every other part sits on the BACK side: ESP32-S3-WROOM-1U (U.FL antenna on top of the case for the best WiFi),
    USB-C, BQ24075 charger, LiPo protection, 3.3 V LDO, 5 V boost for the screen, SCD41 + SHT45 (behind back vents).
Each part: ref, symbol, footprint, value, pin->net, (x, y, rot), extra. side='B' = mounted on the back.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_W, BOARD_H, CORNER_R = 106.0, 88.0, 6.2
BOARD_Y = (-44.0, 44.0)
LCD_CY = -10.0                                         # centre of the 106 x 68 screen module
LCD_HOLES = [(sx * 49.0, LCD_CY + sy * 30.0) for sy in (-1, 1) for sx in (-1, 1)]   # M2, 4 mm from the module edges
LCD_STANDOFF = 4.1                                     # the module's own standoffs (measured in Waveshare's STEP)
NOTCH = (40.5, -37.0, 53.0, 17.5)                      # board cut-out for the module's 8.4 mm 2x20 header (right side)

# NFC antenna: rectangular spiral on F.Cu in the strip under the screen (ST25DV04K, 13.56 MHz)
NFC = dict(x0=-43.0, y0=26.0, x1=24.0, y1=42.6, turns=8, w=0.4, s=0.35)   # ~3.5 uH

# thermally isolated tongue for the SHT45 (back side, left edge), L-shaped slot
SLOTS = [[(40.5, 36.5), (40.5, 21.5), (50.5, 21.5)]]   # neck at the bottom-left for the 4 SHT45 wires
SLOT_W = 1.0
TONGUE = (41.1, 22.1, 53.0, 44.0)

parts = []


def P(ref, sym, fp, value, pins, at, mpn='', lcsc='', group='', dnp=False, side='B'):
    parts.append(dict(ref=ref, sym=sym, fp=fp, value=value, pins={str(k): v for k, v in pins.items()},
                      at=at, mpn=mpn, lcsc=lcsc, group=group, dnp=dnp, side=side))


R0603 = 'Resistor_SMD:R_0603_1608Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
C0805 = 'Capacitor_SMD:C_0805_2012Metric'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'
USBC = 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12'
KMR2 = 'Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2'


def R(ref, val, a, b, at, g, mpn='', side='B'):
    P(ref, 'Device:R', R0603, val, {1: a, 2: b}, at, mpn=mpn or f'0603 {val} 1%', group=g, side=side)


def C(ref, val, a, b, at, g, fp=C0603, mpn='', side='B'):
    size = fp.split(':')[1].split('_')[1]
    kind = 'C0G' if val.endswith('p') else ('X7R' if val.endswith('n') or val == '100n' else 'X5R')
    P(ref, 'Device:C', fp, val, {1: a, 2: b}, at, mpn=mpn or f'{size} {val} {kind} ceramic', group=g, side=side)


# ---------------------------------------------------------------- ESP32-S3-WROOM-1U (external antenna)
# 20 pins for the RGB565 screen, two I2C buses (sensors+NFC / touch), the rest for power management.
G = 'ESP32-S3 (U.FL antenne)'
RGB = {'R3': 34, 'R4': 35, 'R5': 36, 'R6': 37, 'R7': 11,
       'G2': 26, 'G3': 16, 'G4': 15, 'G5': 31, 'G6': 32, 'G7': 33,
       'B3': 21, 'B4': 22, 'B5': 23, 'B6': 24, 'B7': 25}
P('U1', 'RF_Module:ESP32-S3-WROOM-1', 'RF_Module:ESP32-S3-WROOM-1U', 'ESP32-S3-WROOM-1U-N16R8',
  {1: 'GND', 40: 'GND', 41: 'GND', 2: '3V3', 3: 'ESP_EN', 27: 'ESP_IO0', 13: 'USB_DM', 14: 'USB_DP',
   17: 'PCLK', 18: 'DE', 19: 'HSYNC', 20: 'VSYNC', **{n: 'LCD_' + s for s, n in RGB.items()},
   39: 'VBAT_SENSE', 38: 'BL_PWM', 4: 'SDA0', 5: 'SCL0', 6: 'TP_INT', 7: 'SDA1', 12: 'SCL1',
   8: 'PWR_EN', 9: 'NFC_GPO', 10: 'DISP_ON'},
  (0.0, -31.0, 0), mpn='ESP32-S3-WROOM-1U-N16R8 (U.FL; use a 2.4 GHz flex/dipole antenna at the top of the case)', group=G)
C('C1', '22u', '3V3', 'GND', (-12.0, -37.0, 90), G, fp=C0805)
C('C2', '100n', '3V3', 'GND', (-12.0, -33.6, 90), G)
R('R1', '10k', '3V3', 'ESP_EN', (-12.0, -30.2, 90), G)
C('C3', '1u', 'ESP_EN', 'GND', (-13.8, -30.2, 90), G)
R('R2', '10k', '3V3', 'ESP_IO0', (11.5, -12.5, 0), G)
P('SW1', 'Switch:SW_Push', KMR2, 'WEKKEN', {1: 'ESP_IO0', 2: 'GND'}, (16.0, -41.4, 0),
  mpn='CK KMR221G: wake from deep sleep (= BOOT when held at reset)', group=G)
P('SW2', 'Switch:SW_Push', KMR2, 'RESET', {1: 'ESP_EN', 2: 'GND'}, (23.0, -41.4, 0), mpn='CK KMR221G', group=G)

# ---------------------------------------------------------------- USB-C
G = 'USB-C'
P('J2', 'Connector:USB_C_Receptacle_USB2.0_16P', USBC, 'USB-C',
  {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND', 'A4': 'VBUS', 'A9': 'VBUS',
   'B4': 'VBUS', 'B9': 'VBUS', 'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP',
   'A7': 'USB_DM', 'B7': 'USB_DM'}, (-49.2, -6.0, 90), mpn='HRO TYPE-C-31-M-12', group=G)
R('R3', '5k1', 'CC1', 'GND', (-43.0, -12.6, 90), G)
R('R4', '5k1', 'CC2', 'GND', (-43.0, 0.6, 90), G)
P('U2', 'Power_Protection:USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6', 'USBLC6-2SC6',
  {1: 'USB_DP', 6: 'USB_DP', 3: 'USB_DM', 4: 'USB_DM', 2: 'GND', 5: 'VBUS'}, (-41.2, -6.0, 0), mpn='USBLC6-2SC6', group=G)

# ---------------------------------------------------------------- charger: TI BQ24075 (power path), 250 mA for the 300 mAh LiPo
G = 'Laden (BQ24075)'
CH = (-32.0, 9.0)
P('U7', 'Battery_Management:BQ24075RGT', 'Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm', 'BQ24075',
  {1: 'CH_TS', 2: 'VBAT', 3: 'VBAT', 4: 'GND', 5: 'VSYS', 6: 'GND', 7: 'PGOOD', 8: 'GND', 9: 'CHG', 10: 'VSYS',
   11: 'VSYS', 12: 'CH_ILIM', 13: 'VBUS', 15: 'GND', 16: 'CH_ISET', 17: 'GND'},
  (CH[0], CH[1], 0), mpn='TI BQ24075RGTR (Li-ion charger + power path)', group=G)
C('C4', '4u7', 'VBUS', 'GND', (CH[0] + 5.0, CH[1] - 2.0, 90), G, fp=C0805)
C('C5', '10u', 'VSYS', 'GND', (CH[0] - 4.6, CH[1] - 2.0, 90), G, fp=C0805)
C('C6', '4u7', 'VBAT', 'GND', (CH[0] - 4.6, CH[1] + 2.4, 90), G, fp=C0805)
R('R5', '3.6k', 'CH_ISET', 'GND', (CH[0] + 5.0, CH[1] + 2.4, 90), G, mpn='0603 3.6k 1% (charge ~250 mA; 1k = 0.9 A)')
R('R6', '1.1k', 'CH_ILIM', 'GND', (CH[0] + 3.2, CH[1] + 4.2, 90), G, mpn='0603 1.1k 1% (input limit ~1.4 A)')
R('R7', '10k', 'CH_TS', 'GND', (CH[0] + 1.4, CH[1] + 4.2, 90), G, mpn='0603 10k 1% (TS: fixed 10k, no NTC)')
R('R8', '1k', 'VSYS', 'LED_CHG_A', (CH[0] - 0.4, CH[1] + 4.2, 90), G)
P('D1', 'Device:LED', 'LED_SMD:LED_0603_1608Metric', 'rood laden', {1: 'CHG', 2: 'LED_CHG_A'}, (CH[0] - 2.2, CH[1] + 4.2, 90),
  mpn='LED 0603 red (charging)', group=G)
R('R9', '1k', 'VBUS', 'LED_PG_A', (CH[0] - 4.0, CH[1] + 5.8, 90), G)
P('D2', 'Device:LED', 'LED_SMD:LED_0603_1608Metric', 'groen USB', {1: 'PGOOD', 2: 'LED_PG_A'}, (CH[0] - 5.8, CH[1] + 5.8, 90),
  mpn='LED 0603 green (USB power)', group=G)

# ---------------------------------------------------------------- LiPo pads + protection (DW01A + 2x AO3400A)
G = 'Batterij + beveiliging'
BP = (-34.0, -20.0)
P('J4', 'Connector_Generic:Conn_01x02', 'lucht:SolderWire_2pad_P6mm_D1.6mm_BAT', 'BATTERIJ',
  {1: 'VBAT', 2: 'BATN'}, (BP[0] - 3.0, BP[1] - 9.0, 0), mpn='solder pads for the LiPo leads', group=G)
P('U8', 'Battery_Management:DW01A', 'Package_TO_SOT_SMD:SOT-23-6', 'DW01A',
  {1: 'DW_OD', 2: 'DW_CS', 3: 'DW_OC', 5: 'DW_VCC', 6: 'BATN'}, (BP[0], BP[1] + 2.5, 0), mpn='DW01A (Li-ion protection)', group=G)
R('R10', '100', 'VBAT', 'DW_VCC', (BP[0] + 3.6, BP[1] + 2.5, 90), G)
C('C7', '100n', 'DW_VCC', 'BATN', (BP[0] + 5.4, BP[1] + 2.5, 90), G)
R('R11', '1k', 'DW_CS', 'GND', (BP[0] - 3.6, BP[1] + 2.5, 90), G)
P('Q3', 'Transistor_FET:AO3400A', SOT23, 'AO3400A', {1: 'DW_OD', 2: 'BATN', 3: 'BAT_MID'}, (BP[0] - 2.2, BP[1] - 2.0, 0),
  mpn='AO3400A (discharge FET)', group=G)
P('Q4', 'Transistor_FET:AO3400A', SOT23, 'AO3400A', {1: 'DW_OC', 2: 'GND', 3: 'BAT_MID'}, (BP[0] + 2.4, BP[1] - 2.0, 0),
  mpn='AO3400A (charge FET)', group=G)
R('R12', '1M', 'VBAT', 'VBAT_SENSE', (BP[0] + 7.4, BP[1] - 2.0, 90), G, mpn='0603 1M 1% (battery voltage / 2)')
R('R13', '1M', 'VBAT_SENSE', 'GND', (BP[0] + 9.2, BP[1] - 2.0, 90), G, mpn='0603 1M 1%')
C('C8', '100n', 'VBAT_SENSE', 'GND', (BP[0] + 11.0, BP[1] - 2.0, 90), G)

# ---------------------------------------------------------------- 3.3 V (XC6220, 8 uA) + switched sensor rail
G = '3,3 V + sensorvoeding'
P('U3', 'Regulator_Linear:XC6220B331MR', 'Package_TO_SOT_SMD:SOT-23-5', 'XC6220B331MR',
  {1: 'VSYS', 2: 'GND', 3: 'VSYS', 5: '3V3'}, (-18.0, -12.0, 0), mpn='Torex XC6220B331MR-G', group=G)
C('C9', '10u', 'VSYS', 'GND', (-21.6, -12.0, 90), G, fp=C0805)
C('C10', '22u', '3V3', 'GND', (-14.4, -12.0, 90), G, fp=C0805)
C('C11', '100n', '3V3', 'GND', (-12.6, -12.0, 90), G)
P('Q2', 'Transistor_FET:AO3401A', SOT23, 'AO3401A', {1: 'PWR_G', 2: '3V3', 3: '3V3_SW'}, (-6.0, -10.0, 0),
  mpn='AO3401A (load switch: sensors + NFC)', group=G)
R('R14', '100k', 'PWR_G', '3V3', (-2.4, -10.0, 90), G)
R('R15', '10k', 'PWR_EN', 'PWR_G', (-0.6, -10.0, 90), G)
C('C12', '47n', 'PWR_G', '3V3', (1.2, -10.0, 90), G)
C('C13', '10u', '3V3_SW', 'GND', (-9.6, -10.0, 90), G, fp=C0805)

# ---------------------------------------------------------------- 5 V boost for the screen (TPS61023, datasheet fig. 8-1)
G = 'Scherm 5 V (TPS61023)'
BB = (-15.0, 3.0)
P('U9', 'lucht:TPS61023', 'Package_TO_SOT_SMD:SOT-563', 'TPS61023',
  {1: 'BST_FB', 2: 'DISP_ON', 3: 'VSYS', 4: 'GND', 5: 'BST_SW', 6: 'V5D'}, (BB[0], BB[1], 0),
  mpn='TI TPS61023DRLR (3.7 A boost, 0.1 uA shutdown)', group=G)
P('L1', 'Device:L', 'Inductor_SMD:L_Sunlord_MWSA0402S', '1uH', {1: 'VSYS', 2: 'BST_SW'}, (BB[0] - 5.4, BB[1], 90),
  mpn='Sunlord MWSA0402S-1R0MT (1 uH)', group=G)
C('C14', '10u', 'VSYS', 'GND', (BB[0] - 9.4, BB[1], 90), G, fp=C0805)
C('C15', '22u', 'V5D', 'GND', (BB[0] + 3.8, BB[1] - 1.0, 90), G, fp=C0805)
C('C16', '22u', 'V5D', 'GND', (BB[0] + 6.4, BB[1] - 1.0, 90), G, fp=C0805)
R('R16', '732k', 'V5D', 'BST_FB', (BB[0] + 0.6, BB[1] + 3.4, 0), G, mpn='0603 732k 1%')
R('R17', '100k', 'BST_FB', 'GND', (BB[0] + 0.6, BB[1] + 5.2, 0), G)
R('R18', '100k', 'DISP_ON', 'GND', (BB[0] - 5.4, BB[1] + 5.0, 0), G, mpn='0603 100k (screen off at boot / in sleep)')

# ---------------------------------------------------------------- screen FFC (front side) + touch
G = 'Scherm 4.3" (FFC)'
FFC = {1: 'V5D', 2: 'V5D', 3: 'GND', 4: 'TP_3V3', 5: 'GND', 6: 'GND', 7: 'GND',
       8: 'LCD_R3', 9: 'LCD_R4', 10: 'LCD_R5', 11: 'LCD_R6', 12: 'LCD_R7', 13: 'GND', 14: 'GND',
       15: 'LCD_G2', 16: 'LCD_G3', 17: 'LCD_G4', 18: 'LCD_G5', 19: 'LCD_G6', 20: 'LCD_G7', 21: 'GND', 22: 'GND', 23: 'GND',
       24: 'LCD_B3', 25: 'LCD_B4', 26: 'LCD_B5', 27: 'LCD_B6', 28: 'LCD_B7', 29: 'GND', 30: 'PCLK',
       32: 'HSYNC', 33: 'VSYNC', 34: 'DE', 35: 'BL_PWM', 36: 'GND', 37: 'SDA1', 38: 'SCL1', 39: 'TP_RST', 40: 'TP_INT',
       'MP': 'GND'}
# J1 is turned 180 deg: opening towards the screen's own connector H1 (10 mm higher on the module back), pin 1 on the right
# like H1, so a short 40p 0.5 mm FFC makes a U-fold. CHECK the cable type (same-side / opposite-side contacts) before use.
P('J1', 'Connector_Generic_MountingPin:Conn_01x40_MountingPin', 'Connector_FFC-FPC:Hirose_FH12-40S-0.5SH_1x40-1MP_P0.50mm_Horizontal',
  'SCHERM', FFC, (-9.0, -8.0, 180),
  mpn='Hirose FH12-40S-0.5SH(55): 40-pin 0.5 mm FFC to the Waveshare 4.3in Capacitive Touch LCD (RGB cable interface)',
  group=G, side='F')
R('R19', '10k', 'TP_3V3', 'TP_RST', (-6.0, 5.0, 90), G, mpn='0603 10k (GT911 power-on reset)')
C('C17', '1u', 'TP_RST', 'GND', (-4.2, 5.0, 90), G)
R('R20', '10k', 'TP_INT', 'GND', (-2.4, 5.0, 90), G, mpn='0603 10k (INT low at reset -> GT911 address 0x5D)')
R('R21', '4k7', 'SDA1', 'TP_3V3', (-0.6, 5.0, 90), G)
R('R22', '4k7', 'SCL1', 'TP_3V3', (1.2, 5.0, 90), G)

# ---------------------------------------------------------------- sensors (I2C0 on the switched rail)
G = 'Sensoren + NFC (I2C0)'
P('U4', 'Sensor_Optical:LTR-303ALS-01', 'OptoDevice:Lite-On_LTR-303ALS-01', 'LTR-303ALS-01',
  {1: '3V3_SW', 3: 'GND', 4: 'SCL0', 6: 'SDA0'}, (31.5, 36.5, 0), mpn='LTR-303ALS-01 (ambient light, front window)',
  group=G, side='F')
C('C18', '100n', '3V3_SW', 'GND', (28.6, 36.5, 90), G, side='F')
R('R23', '4k7', 'SDA0', '3V3_SW', (28.4, 34.6, 90), G)
R('R24', '4k7', 'SCL0', '3V3_SW', (30.2, 34.6, 90), G)
P('U5', 'Sensor_Gas:SCD41-D-R2', 'Sensor:Sensirion_SCD4x-1EP_10.1x10.1mm_P1.25mm_EP4.8x4.8mm', 'SCD41-D-R2',
  {6: 'GND', 20: 'GND', 21: 'GND', 7: '3V3_SW', 19: '3V3_SW', 9: 'SCL0', 10: 'SDA0'}, (26.0, 6.0, 0),
  mpn='Sensirion SCD41-D-R2 (CO2 400-5000 ppm + RH/T), behind the back vents', group=G)
C('C19', '10u', '3V3_SW', 'GND', (33.6, 3.0, 90), G, fp=C0805)
C('C20', '100n', '3V3_SW', 'GND', (35.4, 3.0, 90), G)
P('U6', 'Sensor_Humidity:SHT4x', 'Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad', 'SHT45',
  {1: 'SDA0', 2: 'SCL0', 3: '3V3_SW', 4: 'GND'}, (47.0, 31.0, 0), mpn='Sensirion SHT45-AD1B-R2 (+-0.1 C)', group=G)
C('C21', '100n', '3V3_SW', 'GND', (47.0, 34.4, 0), G)
# NFC tag: ST25DV04K (I2C 0x53/0x57 + 0x2D), coil on the front strip, GPO wakes the ESP32 when a phone taps
P('U10', 'RF_NFC:ST25DV04K-IER8C3', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'ST25DV04K',
  {2: 'NFC_AC0', 3: 'NFC_AC1', 4: 'GND', 5: 'SDA0', 6: 'SCL0', 7: 'NFC_GPO', 8: '3V3_SW'}, (34.0, 28.0, 90),
  mpn='ST ST25DV04K-IER6S3 (dynamic NFC tag, I2C)', group=G)
C('C22', '100n', '3V3_SW', 'GND', (36.0, 32.6, 0), G)
P('ANT1', 'Device:L', 'lucht:NFC_Coil', 'NFC antenne', {1: 'NFC_AC0', 2: 'NFC_AC1'}, (0.0, 0.0, 0),
  mpn='PCB loop antenna (copper on the board, no part)', group=G, side='F')
C('C23', '10p', 'NFC_AC0', 'NFC_AC1', (29.4, 28.0, 90), G, mpn='0603 10p C0G (3.5 uH coil + 28.5 pF internal + 10 pF = 13.6 MHz; tune 8-15 pF)')
R('R25', '100k', 'NFC_GPO', '3V3', (29.4, 31.6, 0), G)

# ---------------------------------------------------------------- mounting: 4x M2 screen standoffs + 2x M3 case screws
for i, (x, y) in enumerate(LCD_HOLES, 1):
    P(f'H{i}', 'Mechanical:MountingHole', 'lucht:MountingHole_2.2mm_M2', 'M2', {}, (x, y, 0), group='Bevestiging', side='F')
for i, (x, y) in enumerate([(-48.5, 38.5), (46.5, 40.6)], 5):
    P(f'H{i}', 'Mechanical:MountingHole', 'lucht:MountingHole_3.2mm_M3', 'M3', {}, (x, y, 0), group='Bevestiging', side='F')

NETCLASS = {
    'BAT': (['VBUS', 'VSYS', 'VBAT', 'BATN', 'BAT_MID', 'V5D', 'BST_SW'], 0.3, 0.15),   # <= 0.5 A, fits SOT-563 / QFN pads
    'PWR': (['3V3', '3V3_SW', 'GND', 'TP_3V3'], 0.25, 0.15),
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
    nx0, ny0, nx1, ny1 = NOTCH
    for k, (cx, cy, a0) in enumerate(((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180))):
        if k == 1:                                     # right edge: cut-out for the screen's 2x20 header
            pts += [(x1, ny0 - inset), (nx0 - inset, ny0 - inset), (nx0 - inset, ny1 + inset), (x1, ny1 + inset)]
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); pts.append((round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)))
    return pts + pts[:1]


if __name__ == '__main__':
    json.dump({'edge': outline(), 'inner': outline(0.3)}, open(os.path.join(HERE, 'outline.json'), 'w'))
    print('outline.json written')
