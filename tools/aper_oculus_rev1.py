# ---------------------------------------------------------------------------
# Aper-Oculus carrier, PCB APT-KRIA-FMC Rev 1.00 (ApotheoTech LLC)
#
# Single source of truth for the Vivado board files, the master XDC and the
# pinout doc. Every row below was pulled from the KiCad netlist
# (APT-KRIA-FMC.xml, Eeschema 5.1.10) and resolved to an FPGA ball through
# AMD's Kria_K26_SOM_Rev1.xdc. tools/check_board_files.py re-checks the
# table against those two files, so run it after any edit.
#
# To make a new carrier variant: copy this file, edit the tables, then
#   python3 tools/gen_board_files.py --carrier <new_module_name>
# ---------------------------------------------------------------------------

BOARD = {
    'vendor':        'apotheotech.com',
    'vendor_display': 'ApotheoTech',
    'base_name':     'aper_oculus',
    'display_name':  'Aper-Oculus',
    'pcb':           'APT-KRIA-FMC',
    'pcb_rev':       '1.00',
    'file_version':  '1.0',
    'url':           'https://www.apotheotech.com',
    'description':   ('ApotheoTech Aper-Oculus Kria carrier (APT-KRIA-FMC Rev 1.00): '
                      'FMC (LA00-33, 4 TX / 2 RX GTH), FRAMOS SLVS-EC (2 lanes), '
                      '2x 4-lane MIPI CSI-2, mini DisplayPort, USB 3.0, SATA, microSD, '
                      'IMU + barometer, quad USB-UART/JTAG.'),
    # Board picture shown in Vivado's board selection page. 'source' is relative
    # to the repo root (any format Pillow reads, alpha is flattened onto
    # 'background'); the generator writes it into every board directory as an
    # RGB JPEG named 'name', resized to at most 'max_width' pixels wide.
    # Set to None to build without an image.
    'image': {
        'source':      'images/aper-oculus_still.png',
        'name':        'aper_oculus_board.jpg',
        'display':     'Aper-Oculus',
        'description': 'Aper-Oculus Kria K26 carrier',
        'max_width':   1280,
        'background':  (0, 0, 0),
    },
}

# One board directory is generated per SOM. Same carrier, different part.
SOMS = [
    {'suffix': 'k26c', 'som': 'K26C', 'part': 'xck26-sfvc784-2LV-c'},
    {'suffix': 'k26i', 'som': 'K26I', 'part': 'xck26-sfvc784-2LVI-i'},
]

# PL bank supplies on this carrier (from the SOM XDC VCCO pins + netlist).
BANKS = {
    66:  ('HPA', 'PL_1V2',   1.2, 'MIPI cameras, 200 MHz oscillator'),
    45:  ('HDA', 'PL_3V3',   3.3, 'Camera 0 GPIO, DP power switch, SOM power alert'),
    44:  ('HDC', 'PL_3V3',   3.3, 'IMU, barometer, fan, camera resets, alerts'),
    65:  ('HPB', 'VADJ_FMC', 1.8, 'FMC LA00-LA17 + LA19/LA20, CLK1_M2C'),
    64:  ('HPC', 'VADJ_FMC', 1.8, 'FMC LA18, LA21-LA29, LA31, CLK0_M2C; SLVS-EC control'),
    43:  ('HDB', 'VADJ_FMC', 1.8, 'FMC LA30, LA32, LA33 (single-ended only)'),
    224: ('GTH', 'SOM',      None, 'GTH quad: FMC DP0-DP3, SLVS-EC lanes, 2 refclks'),
}

# ---------------------------------------------------------------------------
# PL / GTH signal table
#   name        : port name used in part0_pins.xml, the board interfaces and the XDC
#   loc         : FPGA package ball
#   iostd       : IOSTANDARD ('' for GT pins)
#   bank        : FPGA bank
#   som         : SOM240 connector pin
#   net         : carrier schematic net name
#   desc        : one-line description for the XDC / docs
# ---------------------------------------------------------------------------
def _s(name, loc, iostd, bank, som, net, desc=''):
    return {'name': name, 'loc': loc, 'iostd': iostd, 'bank': bank,
            'som': som, 'net': net, 'desc': desc}

SIGNALS = [
    # ---- 200 MHz LVDS oscillator U7 (SG5032VAN), bank 66 --------------------
    _s('sys_clk_200_p', 'C3', 'DIFF_SSTL12', 66, 'som240_1_a6', 'HPA_CLK0_P', '200 MHz LVDS osc U7 (GC pin)'),
    _s('sys_clk_200_n', 'C2', 'DIFF_SSTL12', 66, 'som240_1_a7', 'HPA_CLK0_N', '200 MHz LVDS osc U7 (GC pin)'),

    # ---- MIPI CSI-2 camera 0, J13 (22-pin 4-lane), bank 66 -----------------
    _s('cam0_clk_p', 'G1', 'MIPI_DPHY_DCI', 66, 'som240_1_c3',  'HPA00_CC_MIPI_A0_CLK_P', 'CAM0 J13 clock lane'),
    _s('cam0_clk_n', 'F1', 'MIPI_DPHY_DCI', 66, 'som240_1_c4',  'HPA00_CC_MIPI_A0_CLK_N', 'CAM0 J13 clock lane'),
    _s('cam0_d0_p',  'E1', 'MIPI_DPHY_DCI', 66, 'som240_1_d7',  'HPA01_MIPI_A0_D0_P', 'CAM0 J13 data lane 0'),
    _s('cam0_d0_n',  'D1', 'MIPI_DPHY_DCI', 66, 'som240_1_d8',  'HPA01_MIPI_A0_D0_N', 'CAM0 J13 data lane 0'),
    _s('cam0_d1_p',  'F2', 'MIPI_DPHY_DCI', 66, 'som240_1_d4',  'HPA02_MIPI_A0_D1_P', 'CAM0 J13 data lane 1'),
    _s('cam0_d1_n',  'E2', 'MIPI_DPHY_DCI', 66, 'som240_1_d5',  'HPA02_MIPI_A0_D1_N', 'CAM0 J13 data lane 1'),
    _s('cam0_d2_p',  'G3', 'MIPI_DPHY_DCI', 66, 'som240_1_c6',  'HPA03_MIPI_A0_D2_P', 'CAM0 J13 data lane 2'),
    _s('cam0_d2_n',  'F3', 'MIPI_DPHY_DCI', 66, 'som240_1_c7',  'HPA03_MIPI_A0_D2_N', 'CAM0 J13 data lane 2'),
    _s('cam0_d3_p',  'E4', 'MIPI_DPHY_DCI', 66, 'som240_1_b4',  'HPA04_MIPI_A0_D3_P', 'CAM0 J13 data lane 3'),
    _s('cam0_d3_n',  'E3', 'MIPI_DPHY_DCI', 66, 'som240_1_b5',  'HPA04_MIPI_A0_D3_N', 'CAM0 J13 data lane 3'),

    # ---- MIPI CSI-2 camera 1, J14 (22-pin 4-lane), bank 66 -----------------
    _s('cam1_clk_p', 'C1', 'MIPI_DPHY_DCI', 66, 'som240_1_b1',  'HPA05_CC_MIPI_A1_CLK_P', 'CAM1 J14 clock lane'),
    _s('cam1_clk_n', 'B1', 'MIPI_DPHY_DCI', 66, 'som240_1_b2',  'HPA05_CC_MIPI_A1_CLK_N', 'CAM1 J14 clock lane'),
    _s('cam1_d0_p',  'A2', 'MIPI_DPHY_DCI', 66, 'som240_1_a3',  'HPA06_MIPI_A1_D0_P', 'CAM1 J14 data lane 0'),
    _s('cam1_d0_n',  'A1', 'MIPI_DPHY_DCI', 66, 'som240_1_a4',  'HPA06_MIPI_A1_D0_N', 'CAM1 J14 data lane 0'),
    _s('cam1_d1_p',  'B3', 'MIPI_DPHY_DCI', 66, 'som240_1_b7',  'HPA07_MIPI_A1_D1_P', 'CAM1 J14 data lane 1'),
    _s('cam1_d1_n',  'A3', 'MIPI_DPHY_DCI', 66, 'som240_1_b8',  'HPA07_MIPI_A1_D1_N', 'CAM1 J14 data lane 1'),
    _s('cam1_d2_p',  'B4', 'MIPI_DPHY_DCI', 66, 'som240_1_c9',  'HPA08_MIPI_A1_D2_P', 'CAM1 J14 data lane 2'),
    _s('cam1_d2_n',  'A4', 'MIPI_DPHY_DCI', 66, 'som240_1_c10', 'HPA08_MIPI_A1_D2_N', 'CAM1 J14 data lane 2'),
    _s('cam1_d3_p',  'D4', 'MIPI_DPHY_DCI', 66, 'som240_1_d10', 'HPA09_MIPI_A1_D3_P', 'CAM1 J14 data lane 3'),
    _s('cam1_d3_n',  'C4', 'MIPI_DPHY_DCI', 66, 'som240_1_d11', 'HPA09_MIPI_A1_D3_N', 'CAM1 J14 data lane 3'),

    # ---- Camera control (3.3 V) --------------------------------------------
    # CAMx_RESET_N go to the PIC18 supervisor (U4), which drives the camera
    # connector CAM_GPIO0 (pin 17). CAMx_GPIO1 go straight to connector pin 18.
    _s('cam0_reset_n', 'W14',  'LVCMOS33', 44, 'som240_2_b54', 'HDC14_CAM0_RESET_N', 'CAM0 reset request to PIC U4 (J13 pin 17)'),
    _s('cam0_gpio1',   'F10',  'LVCMOS33', 45, 'som240_1_d17', 'HDA01_CAM0_GPIO_1',  'CAM0 J13 pin 18 (CAM_GPIO1)'),
    _s('cam1_reset_n', 'AG13', 'LVCMOS33', 44, 'som240_2_c54', 'HDC06_CAM1_RESET_N', 'CAM1 reset request to PIC U4 (J14 pin 17)'),
    _s('cam1_gpio1',   'AB13', 'LVCMOS33', 44, 'som240_2_b53', 'HDC13_CAM1_GPIO_1',  'CAM1 J14 pin 18 (CAM_GPIO1)'),

    # ---- GTH reference clock 0: Si570 U3 (570BAB001614DGR) -----------------
    _s('gth_refclk0_p', 'Y6', '', 224, 'som240_2_c3', 'GTH_REFCLK0_C2M_P', 'Si570 U3 -> MGTREFCLK0P_224 (I2C mux ch2)'),
    _s('gth_refclk0_n', 'Y5', '', 224, 'som240_2_c4', 'GTH_REFCLK0_C2M_N', 'Si570 U3 -> MGTREFCLK0N_224'),

    # ---- SLVS-EC sensor I2C (1.8 V, 2.21k pull-ups to PL_1V8 on the carrier)
    _s('slvs_ec_scl', 'AF7', 'LVCMOS18', 64, 'som240_2_d27', 'HPC09_P_I2C_SCL_SLVS',    'Sensor I2C SCL / SPI SCK, J21 pin 16'),
    _s('slvs_ec_sda', 'AB3', 'LVCMOS18', 64, 'som240_2_c36', 'HPC12_N_I2C_SLVS_EC_SDA', 'Sensor I2C SDA / SPI SDI, J21 pin 15'),

    # ---- SLVS-EC sensor control GPIO (1.8 V), bit order = slvs_ec_ctrl[14:0]
    _s('slvs_ec_rst_n',            'AG8', 'LVCMOS18', 64, 'som240_2_b28', 'HPC06_N_SLVS_EC_RST_0',     'Sensor reset (XCLR), J21 pin 33, pulled up'),
    _s('slvs_ec_xce',              'AF6', 'LVCMOS18', 64, 'som240_2_d28', 'HPC09_N_XCE_SLVS_EC',       'Sensor serial chip enable XCE, J21 pin 18'),
    _s('slvs_ec_xmaster',          'AE8', 'LVCMOS18', 64, 'som240_2_d31', 'HPC01_N_XMASTER',           'Sensor master/slave select, J21 pin 22'),
    _s('slvs_ec_xhs',              'AB8', 'LVCMOS18', 64, 'som240_2_d36', 'HPC02_P_XHS',               'Horizontal sync XHS, J21 pin 28'),
    _s('slvs_ec_xvs',              'AC8', 'LVCMOS18', 64, 'som240_2_d37', 'HPC02_N_XVS',               'Vertical sync XVS, J21 pin 30'),
    _s('slvs_ec_trig1',            'AD9', 'LVCMOS18', 64, 'som240_2_d34', 'HPC00_CC_N_TRIG1',          'Trigger 1, J21 pin 26'),
    _s('slvs_ec_gpio7_trig2',      'AC9', 'LVCMOS18', 64, 'som240_2_d33', 'HPC00_CC_P_GPIO7_TRIG2',    'GPIO7 / trigger 2, J21 pin 24'),
    _s('slvs_ec_tout0',            'AC3', 'LVCMOS18', 64, 'som240_2_c33', 'HPC11_N_TOUT0',             'Sensor TOUT0, J21 pin 19'),
    _s('slvs_ec_tout1',            'AC4', 'LVCMOS18', 64, 'som240_2_c32', 'HPC11_P_TOUT1',             'Sensor TOUT1, J21 pin 21'),
    _s('slvs_ec_tout2',            'AD4', 'LVCMOS18', 64, 'som240_2_c30', 'HPC10_CC_N_TOUT2',          'Sensor TOUT2, J21 pin 23'),
    _s('slvs_ec_gpio6',            'AE9', 'LVCMOS18', 64, 'som240_2_d30', 'HPC01_P_GPIO6',             'GPIO6, J21 pin 20'),
    _s('slvs_ec_gpio10_omode_fsm', 'AE3', 'LVCMOS18', 64, 'som240_2_c26', 'HPC17_P_GPIO10_OMODE_FSM',  'GPIO10 / OMODE_FSM, J21 pin 29'),
    _s('slvs_ec_gpio14_slamode2',  'AF3', 'LVCMOS18', 64, 'som240_2_c27', 'HPC17_N_GPIO14_SLAMODE2',   'GPIO14 / SLAMODE2, J21 pin 27'),
    _s('slvs_ec_gpio16_slamode1',  'AF8', 'LVCMOS18', 64, 'som240_2_b27', 'HPC06_P_GPIO16_SLAMODE1',   'GPIO16 / SLAMODE1, J21 pin 25'),
    _s('slvs_ec_miso',             'AB4', 'LVCMOS18', 64, 'som240_2_c35', 'HPC12_P_MISO_SLVS_EC',      'Sensor SPI SDO (4-wire mode), J21 pin 17'),

    # ---- IMU U9 (TDK ICM-42688-P), SPI, 3.3 V ------------------------------
    _s('imu_sclk', 'AH13', 'LVCMOS33', 44, 'som240_2_c55', 'HDC07_SCLK_ICM_42688', 'IMU SPI SCLK (U9 pin 13)'),
    _s('imu_mosi', 'AE15', 'LVCMOS33', 44, 'som240_2_d54', 'HDC02_SDI_ICM_42688',  'IMU SPI SDI (U9 pin 14)'),
    _s('imu_miso', 'AD14', 'LVCMOS33', 44, 'som240_2_d53', 'HDC01_SDO_ICM_42688',  'IMU SPI SDO (U9 pin 1)'),
    _s('imu_cs_n', 'AC14', 'LVCMOS33', 44, 'som240_2_c56', 'HDC08_CS_ICM_42688',   'IMU SPI CS (U9 pin 12), pulled up'),
    _s('imu_int1', 'AD15', 'LVCMOS33', 44, 'som240_2_d52', 'HDC00_CC_INT_ICM_42688', 'IMU INT1 (U9 pin 4)'),
    _s('imu_int2', 'AE14', 'LVCMOS33', 44, 'som240_2_d56', 'HDC03_CLK_ICM_42688',  'IMU INT2/FSYNC/CLKIN (U9 pin 9)'),

    # ---- Barometer IC22 (TE MS5611-01BA03), SPI when PS=0, 3.3 V ------------
    _s('baro_sclk', 'AH14', 'LVCMOS33', 44, 'som240_2_d58', 'HDC05_SCL_MS5611',     'Baro SCLK / SCL (IC22 pin 8)'),
    _s('baro_mosi', 'AG14', 'LVCMOS33', 44, 'som240_2_d57', 'HDC04_SDA_SDI_MS5611', 'Baro SDI / SDA (IC22 pin 7)'),
    _s('baro_miso', 'AE13', 'LVCMOS33', 44, 'som240_2_c59', 'HDC10_SDO_MS5611',     'Baro SDO (IC22 pin 6)'),
    _s('baro_cs_n', 'AF13', 'LVCMOS33', 44, 'som240_2_c60', 'HDC11_CS_MS5611',      'Baro CSB (IC22 pins 4/5), pulled up'),

    # ---- Board control outputs, bit order = board_ctrl[2:0] -----------------
    _s('dp_pwr_en', 'J11',  'LVCMOS33', 45, 'som240_1_d18', 'HDA02_DP_PWR_EN',   'DP connector power switch IC23 enable (high = on)'),
    _s('fan_pwm_n', 'AC13', 'LVCMOS33', 44, 'som240_2_c58', 'HDC09_FAN_PWM',     'Fan control, active low: 0/float = fan on, 1 = fan off (Q15 inverts into Q16)'),
    _s('baro_ps',   'AA12', 'LVCMOS33', 44, 'som240_2_a60', 'HDC23_MODE_MS5611', 'Baro protocol select PS (0 = SPI, 1 = I2C)'),

    # ---- Board status inputs, bit order = board_status[4:0] -----------------
    _s('fmc_prsnt_m2c_n',    'Y14', 'LVCMOS33', 44, 'som240_2_a54', 'HDC18_PRSNT_M2C_B',  'FMC PRSNT_M2C_B (low = card fitted)'),
    _s('dp_pwr_fault_n',     'E10', 'LVCMOS33', 45, 'som240_1_d20', 'HDA12_DP_PWR_FAULT', 'DP power switch IC23 fault flag (low = fault)'),
    _s('som_5v_alert_n',     'A10', 'LVCMOS33', 45, 'som240_1_c23', 'HDA19_ALERT_INA260', 'INA260 IC15 (SOM 5 V) alert'),
    _s('vadj_imon_alert_n',  'Y13', 'LVCMOS33', 44, 'som240_2_a55', 'HDC19_INA226_ALERT', 'INA226 IC1 (VADJ current) alert'),
    _s('vadj_pmbus_alert_n', 'W12', 'LVCMOS33', 44, 'som240_2_a56', 'HDC20_VADJ_ALERT',   'MAX15301 U2 (VADJ regulator) SMBALERT'),
]

# Signals that are wired on the carrier but deliberately not in any board
# interface. They still go in the master XDC and the pinout doc.
XDC_ONLY_SIGNALS = [
    # SLVS-EC high-speed lanes on GTH RX. Vivado has no stock IP that consumes a
    # receive-only GT board interface, so these live in the XDC only.
    _s('slvs_ec_rx0_p', 'P2', '', 224, 'som240_2_d5', 'GTH_DP3_C2M_SLVS_EC_RX_LANE0_P', 'SLVS-EC lane 0, MGTHRXP3_224 (GTHE4_CHANNEL_X0Y3)'),
    _s('slvs_ec_rx0_n', 'P1', '', 224, 'som240_2_d6', 'GTH_DP3_C2M_SLVS_EC_RX_LANE0_N', 'SLVS-EC lane 0, MGTHRXN3_224'),
    _s('slvs_ec_rx1_p', 'V2', '', 224, 'som240_2_d1', 'GTH_DP1_C2M_SLVS_EC_RX_LANE1_P', 'SLVS-EC lane 1, MGTHRXP1_224 (GTHE4_CHANNEL_X0Y1)'),
    _s('slvs_ec_rx1_n', 'V1', '', 224, 'som240_2_d2', 'GTH_DP1_C2M_SLVS_EC_RX_LANE1_N', 'SLVS-EC lane 1, MGTHRXN1_224'),

    _s('slvs_ec_mclk', 'AD5', 'LVCMOS18', 64, 'som240_2_c29', 'HPC10_CC_P_MCLK_0_SLVS', 'Sensor INCK/MCLK output, J21 pin 35 (drive from an MMCM/ODDR)'),
]

# ---------------------------------------------------------------------------
# FMC J1 (Samtec ASP-134486-01, HPC footprint). Only the pins that reach the
# FPGA are listed. Position letters/numbers are VITA 57.1.
#   (fmc_pos, name, loc, bank, som, net)
# ---------------------------------------------------------------------------
def _f(pos, name, loc, bank, som, net):
    return {'pos': pos, 'name': name, 'loc': loc, 'bank': bank, 'som': som, 'net': net,
            'iostd': '' if bank == 224 else 'LVCMOS18'}

FMC = [
    _f('G6',  'fmc_la00_cc_p', 'K4',   65, 'som240_2_c11', 'HPB09_LA00_CC_P'),
    _f('G7',  'fmc_la00_cc_n', 'K3',   65, 'som240_2_c12', 'HPB09_LA00_CC_N'),
    _f('D8',  'fmc_la01_cc_p', 'J5',   65, 'som240_2_a11', 'HPB15_CC_LA01_CC_P'),
    _f('D9',  'fmc_la01_cc_n', 'J4',   65, 'som240_2_a12', 'HPB15_CC_LA01_CC_N'),
    _f('H7',  'fmc_la02_p',    'L7',   65, 'som240_2_b12', 'HPB10_CC_LA02_P'),
    _f('H8',  'fmc_la02_n',    'L6',   65, 'som240_2_b13', 'HPB10_CC_LA02_N'),
    _f('G9',  'fmc_la03_p',    'K2',   65, 'som240_2_b15', 'HPB07_LA03_P'),
    _f('G10', 'fmc_la03_n',    'J2',   65, 'som240_2_b16', 'HPB07_LA03_N'),
    _f('H10', 'fmc_la04_p',    'H4',   65, 'som240_2_a14', 'HPB08_LA04_P'),
    _f('H11', 'fmc_la04_n',    'H3',   65, 'som240_2_a15', 'HPB08_LA04_N'),
    _f('D11', 'fmc_la05_p',    'N9',   65, 'som240_2_c14', 'HPB14_LA05_P'),
    _f('D12', 'fmc_la05_n',    'N8',   65, 'som240_2_c15', 'HPB14_LA05_N'),
    _f('C10', 'fmc_la06_p',    'U9',   65, 'som240_2_d12', 'HPB01_LA06_P'),
    _f('C11', 'fmc_la06_n',    'V9',   65, 'som240_2_d13', 'HPB01_LA06_N'),
    _f('H13', 'fmc_la07_p',    'U8',   65, 'som240_2_c17', 'HPB02_LA07_P'),
    _f('H14', 'fmc_la07_n',    'V8',   65, 'som240_2_c18', 'HPB02_LA07_N'),
    _f('G12', 'fmc_la08_p',    'W8',   65, 'som240_2_d15', 'HPB00_CC_LA08_P'),
    _f('G13', 'fmc_la08_n',    'Y8',   65, 'som240_2_d16', 'HPB00_CC_LA08_N'),
    _f('D14', 'fmc_la09_p',    'N7',   65, 'som240_2_a17', 'HPB12_LA09_P'),
    _f('D15', 'fmc_la09_n',    'N6',   65, 'som240_2_a18', 'HPB12_LA09_N'),
    _f('C14', 'fmc_la10_p',    'L1',   65, 'som240_2_b18', 'HPB05_CC_LA10_P'),
    _f('C15', 'fmc_la10_n',    'K1',   65, 'som240_2_b19', 'HPB05_CC_LA10_N'),
    _f('H16', 'fmc_la11_p',    'P7',   65, 'som240_2_c20', 'HPB13_LA11_P'),
    _f('H17', 'fmc_la11_n',    'P6',   65, 'som240_2_c21', 'HPB13_LA11_N'),
    _f('G15', 'fmc_la12_p',    'R7',   65, 'som240_2_d21', 'HPB04_LA12_P'),
    _f('G16', 'fmc_la12_n',    'T7',   65, 'som240_2_d22', 'HPB04_LA12_N'),
    _f('D17', 'fmc_la13_p',    'J1',   65, 'som240_2_a20', 'HPB06_LA13_P'),
    _f('D18', 'fmc_la13_n',    'H1',   65, 'som240_2_a21', 'HPB06_LA13_N'),
    _f('C18', 'fmc_la14_p',    'M6',   65, 'som240_2_b21', 'HPB11_LA14_P'),
    _f('C19', 'fmc_la14_n',    'L5',   65, 'som240_2_b22', 'HPB11_LA14_N'),
    _f('H19', 'fmc_la15_p',    'K9',   65, 'som240_2_c23', 'HPB18_LA15_P'),
    _f('H20', 'fmc_la15_n',    'J9',   65, 'som240_2_c24', 'HPB18_LA15_N'),
    _f('G18', 'fmc_la16_p',    'J7',   65, 'som240_2_a23', 'HPB16_LA16_P'),
    _f('G19', 'fmc_la16_n',    'H7',   65, 'som240_2_a24', 'HPB16_LA16_N'),
    _f('D20', 'fmc_la17_cc_p', 'K8',   65, 'som240_2_d24', 'HPB17_LA17_CC_P'),
    _f('D21', 'fmc_la17_cc_n', 'K7',   65, 'som240_2_d25', 'HPB17_LA17_CC_N'),
    _f('C22', 'fmc_la18_cc_p', 'AG6',  64, 'som240_2_a29', 'HPC08_LA18_CC_P'),
    _f('C23', 'fmc_la18_cc_n', 'AG5',  64, 'som240_2_a30', 'HPC08_LA18_CC_N'),
    _f('H22', 'fmc_la19_p',    'H9',   65, 'som240_2_a26', 'HPB19_LA19_P'),
    _f('H23', 'fmc_la19_n',    'H8',   65, 'som240_2_a27', 'HPB19_LA19_N'),
    _f('G21', 'fmc_la20_p',    'R8',   65, 'som240_2_b24', 'HPB03_LA20_P'),
    _f('G22', 'fmc_la20_n',    'T8',   65, 'som240_2_b25', 'HPB03_LA20_N'),
    _f('H25', 'fmc_la21_p',    'AG3',  64, 'som240_2_b33', 'HPC16_LA21_P'),
    _f('H26', 'fmc_la21_n',    'AH3',  64, 'som240_2_b34', 'HPC16_LA21_N'),
    _f('G24', 'fmc_la22_p',    'AH2',  64, 'som240_2_a32', 'HPC19_LA22_P'),
    _f('G25', 'fmc_la22_n',    'AH1',  64, 'som240_2_a33', 'HPC19_LA22_N'),
    _f('D23', 'fmc_la23_p',    'AD2',  64, 'som240_2_b30', 'HPC13_LA23_P'),
    _f('D24', 'fmc_la23_n',    'AD1',  64, 'som240_2_b31', 'HPC13_LA23_N'),
    _f('H28', 'fmc_la24_p',    'AG9',  64, 'som240_2_c38', 'HPC05_CC_LA24_P'),
    _f('H29', 'fmc_la24_n',    'AH9',  64, 'som240_2_c39', 'HPC05_CC_LA24_N'),
    _f('G27', 'fmc_la25_p',    'AG4',  64, 'som240_2_a38', 'HPC15_CC_LA25_P'),
    _f('G28', 'fmc_la25_n',    'AH4',  64, 'som240_2_a39', 'HPC15_CC_LA25_N'),
    _f('D26', 'fmc_la26_p',    'AB2',  64, 'som240_2_a35', 'HPC14_LA26_P'),
    _f('D27', 'fmc_la26_n',    'AC2',  64, 'som240_2_a36', 'HPC14_LA26_N'),
    _f('C26', 'fmc_la27_p',    'AH8',  64, 'som240_2_b36', 'HPC07_LA27_P'),
    _f('C27', 'fmc_la27_n',    'AH7',  64, 'som240_2_b37', 'HPC07_LA27_N'),
    _f('H31', 'fmc_la28_p',    'AB7',  64, 'som240_2_d39', 'HPC04_LA28_P'),
    _f('H32', 'fmc_la28_n',    'AC7',  64, 'som240_2_d40', 'HPC04_LA28_N'),
    _f('G30', 'fmc_la29_p',    'AE2',  64, 'som240_2_b39', 'HPC18_LA29_P'),
    _f('G31', 'fmc_la29_n',    'AF2',  64, 'som240_2_b40', 'HPC18_LA29_N'),
    _f('H34', 'fmc_la30_p',    'W10',  43, 'som240_2_a46', 'HDB18_LA30_P'),
    _f('H35', 'fmc_la30_n',    'Y10',  43, 'som240_2_a47', 'HDB19_LA30_N'),
    _f('G33', 'fmc_la31_p',    'AD7',  64, 'som240_2_a41', 'HPC03_LA31_P'),
    _f('G34', 'fmc_la31_n',    'AE7',  64, 'som240_2_a42', 'HPC03_LA31_N'),
    _f('H37', 'fmc_la32_p',    'AA10', 43, 'som240_2_b48', 'HDB15_LA32_P'),
    _f('H38', 'fmc_la32_n',    'AB11', 43, 'som240_2_b49', 'HDB16_CC_LA32_N'),
    _f('G36', 'fmc_la33_p',    'AA8',  43, 'som240_2_a50', 'HDB21_LA33_P'),
    _f('G37', 'fmc_la33_n',    'AB10', 43, 'som240_2_a51', 'HDB22_LA33_N'),
    _f('H4',  'fmc_clk0_m2c_p', 'AE5', 64, 'som240_2_c41', 'HPC_CLK0_CLK0_M2C_P'),
    _f('H5',  'fmc_clk0_m2c_n', 'AF5', 64, 'som240_2_c42', 'HPC_CLK0_CLK0_M2C_N'),
    _f('G2',  'fmc_clk1_m2c_p', 'L3',  65, 'som240_2_d18', 'HPB_CLK0_CLK1_M2C_P'),
    _f('G3',  'fmc_clk1_m2c_n', 'L2',  65, 'som240_2_d19', 'HPB_CLK0_CLK1_M2C_N'),
    _f('D4',  'fmc_gbtclk0_m2c_p', 'V6', 224, 'som240_2_a7', 'GTH_REFCLK1_C2M_GBTCLK0_M2C_P'),
    _f('D5',  'fmc_gbtclk0_m2c_n', 'V5', 224, 'som240_2_a8', 'GTH_REFCLK1_C2M_GBTCLK0_M2C_N'),
    _f('C2',  'fmc_dp0_c2m_p', 'R4', 224, 'som240_2_b5',  'GTH_DP2_M2C_TX_DP0_C2M_P'),
    _f('C3',  'fmc_dp0_c2m_n', 'R3', 224, 'som240_2_b6',  'GTH_DP2_M2C_TX_DP0_C2M_N'),
    _f('C6',  'fmc_dp0_m2c_p', 'T2', 224, 'som240_2_b1',  'GTH_DP2_C2M_RX_DP0_M2C_P'),
    _f('C7',  'fmc_dp0_m2c_n', 'T1', 224, 'som240_2_b2',  'GTH_DP2_C2M_RX_DP0_M2C_N'),
    _f('A22', 'fmc_dp1_c2m_p', 'W4', 224, 'som240_2_d9',  'GTH_DP0_M2C_TX_DP1_C2M_P'),
    _f('A23', 'fmc_dp1_c2m_n', 'W3', 224, 'som240_2_d10', 'GTH_DP0_M2C_TX_DP1_C2M_N'),
    _f('A2',  'fmc_dp1_m2c_p', 'Y2', 224, 'som240_2_b9',  'GTH_DP0_C2M_RX_DP1_M2C_P'),
    _f('A3',  'fmc_dp1_m2c_n', 'Y1', 224, 'som240_2_b10', 'GTH_DP0_C2M_RX_DP1_M2C_N'),
    _f('A26', 'fmc_dp2_c2m_p', 'N4', 224, 'som240_2_a3',  'GTH_DP3_M2C_TX_DP2_C2M_P'),
    _f('A27', 'fmc_dp2_c2m_n', 'N3', 224, 'som240_2_a4',  'GTH_DP3_M2C_TX_DP2_C2M_N'),
    _f('A30', 'fmc_dp3_c2m_p', 'U4', 224, 'som240_2_c7',  'GTH_DP1_M2C_TX_DP3_C2M_P'),
    _f('A31', 'fmc_dp3_c2m_n', 'U3', 224, 'som240_2_c8',  'GTH_DP1_M2C_TX_DP3_C2M_N'),
]

# GTH channel ownership, for the docs and XDC comments.
GTH_CHANNELS = [
    # (channel, TX use, RX use)
    ('GTHE4_CHANNEL_X0Y0', 'FMC DP1_C2M (A22/A23)', 'FMC DP1_M2C (A2/A3)'),
    ('GTHE4_CHANNEL_X0Y1', 'FMC DP3_C2M (A30/A31)', 'SLVS-EC lane 1'),
    ('GTHE4_CHANNEL_X0Y2', 'FMC DP0_C2M (C2/C3)',   'FMC DP0_M2C (C6/C7)'),
    ('GTHE4_CHANNEL_X0Y3', 'FMC DP2_C2M (A26/A27)', 'SLVS-EC lane 0'),
]
GTH_REFCLKS = [
    ('MGTREFCLK0_224 (Y6/Y5)', 'Si570 U3, I2C mux ch2, programmable (300 MHz at power-up on the fitted 570BAB001614DGR)'),
    ('MGTREFCLK1_224 (V6/V5)', 'FMC GBTCLK0_M2C (D4/D5), from the mezzanine'),
]

# ---------------------------------------------------------------------------
# Board components and interfaces (PL side)
# kind: diff_clock | mipi | gpio_out | gpio_in | gpio_io | iic | spi
# ---------------------------------------------------------------------------
COMPONENTS = [
    {'name': 'sys_clk_200mhz', 'display': '200 MHz System Clock', 'sub_type': 'system_clock',
     'major_group': 'Clock Sources', 'part_name': 'SG5032VAN 200.000000M-KEGA3', 'vendor': 'Epson',
     'description': '200 MHz LVDS oscillator U7 on HPA_CLK0 (bank 66, global clock pins C3/C2).',
     'frequency': 200000000,
     'pins': ['sys_clk_200_p', 'sys_clk_200_n']},

    {'name': 'gth_refclk0', 'display': 'GTH REFCLK0 (Si570)', 'sub_type': 'mgt_clock',
     'major_group': 'Clock Sources', 'part_name': '570BAB001614DGR', 'vendor': 'Skyworks/Silicon Labs',
     'description': ('Programmable Si570 U3 into MGTREFCLK0_224. Intended for the SLVS-EC lanes; '
                     'any GTH channel can use it. Starts at 300 MHz; reprogram over PS I2C0, mux 0x76 channel 2.'),
     'frequency': 300000000,
     'pins': ['gth_refclk0_p', 'gth_refclk0_n']},

    {'name': 'cam0', 'display': 'MIPI Camera 0 (J13)', 'sub_type': 'chip', 'major_group': 'MIPI',
     'description': ('22-pin 4-lane MIPI CSI-2 connector J13 on bank 66. Camera I2C is on PS I2C0, '
                     'mux 0x76 channel 5. Reset/GPIO are in cam_ctrl_4bits.'),
     'pins': ['cam0_clk_p', 'cam0_clk_n', 'cam0_d0_p', 'cam0_d0_n', 'cam0_d1_p', 'cam0_d1_n',
              'cam0_d2_p', 'cam0_d2_n', 'cam0_d3_p', 'cam0_d3_n'],
     'modes': [('cam0_mipi_4lane', 'MIPI CSI-2, 4 lanes'), ('cam0_mipi_2lane', 'MIPI CSI-2, 2 lanes')]},

    {'name': 'cam1', 'display': 'MIPI Camera 1 (J14)', 'sub_type': 'chip', 'major_group': 'MIPI',
     'description': ('22-pin 4-lane MIPI CSI-2 connector J14 on bank 66. Camera I2C is on PS I2C0, '
                     'mux 0x76 channel 4. Reset/GPIO are in cam_ctrl_4bits.'),
     'pins': ['cam1_clk_p', 'cam1_clk_n', 'cam1_d0_p', 'cam1_d0_n', 'cam1_d1_p', 'cam1_d1_n',
              'cam1_d2_p', 'cam1_d2_n', 'cam1_d3_p', 'cam1_d3_n'],
     'modes': [('cam1_mipi_4lane', 'MIPI CSI-2, 4 lanes'), ('cam1_mipi_2lane', 'MIPI CSI-2, 2 lanes')]},

    {'name': 'cam_ctrl', 'display': 'Camera Reset and GPIO', 'sub_type': 'chip', 'major_group': 'MIPI',
     'description': 'Bits: [0] cam0_reset_n, [1] cam0_gpio1, [2] cam1_reset_n, [3] cam1_gpio1. Resets go through PIC U4.',
     'pins': ['cam0_reset_n', 'cam0_gpio1', 'cam1_reset_n', 'cam1_gpio1']},

    {'name': 'slvs_ec_iic', 'display': 'SLVS-EC Sensor I2C', 'sub_type': 'chip', 'major_group': 'SLVS-EC',
     'description': 'Sensor I2C on bank 64 (VADJ, must be 1.8 V), 2.21k pull-ups to PL_1V8.',
     'pins': ['slvs_ec_scl', 'slvs_ec_sda']},

    {'name': 'slvs_ec_ctrl', 'display': 'SLVS-EC Sensor Control', 'sub_type': 'chip', 'major_group': 'SLVS-EC',
     'description': ('Bits: [0] rst_n, [1] xce, [2] xmaster, [3] xhs, [4] xvs, [5] trig1, [6] gpio7_trig2, '
                     '[7] tout0, [8] tout1, [9] tout2, [10] gpio6, [11] gpio10_omode_fsm, '
                     '[12] gpio14_slamode2, [13] gpio16_slamode1, [14] miso.'),
     'pins': ['slvs_ec_rst_n', 'slvs_ec_xce', 'slvs_ec_xmaster', 'slvs_ec_xhs', 'slvs_ec_xvs',
              'slvs_ec_trig1', 'slvs_ec_gpio7_trig2', 'slvs_ec_tout0', 'slvs_ec_tout1', 'slvs_ec_tout2',
              'slvs_ec_gpio6', 'slvs_ec_gpio10_omode_fsm', 'slvs_ec_gpio14_slamode2',
              'slvs_ec_gpio16_slamode1', 'slvs_ec_miso']},

    {'name': 'imu', 'display': 'IMU (ICM-42688-P)', 'sub_type': 'chip', 'major_group': 'Sensors',
     'part_name': 'ICM-42688-P', 'vendor': 'TDK InvenSense',
     'description': '6-axis IMU U9 on SPI (bank 44, 3.3 V). Mode 0 or 3, up to 24 MHz.',
     'pins': ['imu_sclk', 'imu_mosi', 'imu_miso', 'imu_cs_n']},

    {'name': 'imu_int', 'display': 'IMU Interrupts', 'sub_type': 'chip', 'major_group': 'Sensors',
     'description': 'Bits: [0] INT1, [1] INT2/FSYNC/CLKIN. Tri-state so INT2 can be driven as FSYNC/CLKIN.',
     'pins': ['imu_int1', 'imu_int2']},

    {'name': 'baro', 'display': 'Barometer (MS5611)', 'sub_type': 'chip', 'major_group': 'Sensors',
     'part_name': 'MS561101BA03-50', 'vendor': 'TE Connectivity',
     'description': 'Barometric pressure sensor IC22 on SPI (bank 44, 3.3 V). Hold board_ctrl[2] (baro_ps) low for SPI.',
     'pins': ['baro_sclk', 'baro_mosi', 'baro_miso', 'baro_cs_n']},

    {'name': 'board_ctrl', 'display': 'Board Control', 'sub_type': 'chip', 'major_group': 'General Purpose Input or Output',
     'description': ('Bits: [0] dp_pwr_en, [1] fan_pwm_n (active low), [2] baro_ps. Preset defaults to 0b001: '
                     'DP power on, fan on, barometer in SPI mode.'),
     'pins': ['dp_pwr_en', 'fan_pwm_n', 'baro_ps']},

    {'name': 'board_status', 'display': 'Board Status', 'sub_type': 'chip', 'major_group': 'General Purpose Input or Output',
     'description': ('Bits (all active low): [0] fmc_prsnt_m2c_n, [1] dp_pwr_fault_n, [2] som_5v_alert_n, '
                     '[3] vadj_imon_alert_n, [4] vadj_pmbus_alert_n. Preset enables the GPIO interrupt.'),
     'pins': ['fmc_prsnt_m2c_n', 'dp_pwr_fault_n', 'som_5v_alert_n', 'vadj_imon_alert_n', 'vadj_pmbus_alert_n']},
]

# MIPI byte-group locations used by the MIPI CSI-2 RX Subsystem presets.
MIPI_LOCS = {
    'cam0': {'clk': 'G1', 'data': ['E1', 'F2', 'G3', 'E4']},
    'cam1': {'clk': 'C1', 'data': ['A2', 'B3', 'B4', 'D4']},
}
MIPI_DEFAULT_LINE_RATE = 912   # Mbps per lane; change to suit the sensor
MIPI_DEFAULT_PIXEL_FORMAT = 'RAW10'

INTERFACES = [
    {'name': 'sys_clk_200mhz', 'kind': 'diff_clock', 'component': 'sys_clk_200mhz',
     'ports': ('sys_clk_200_p', 'sys_clk_200_n'), 'preferred': ['clk_wiz'],
     'description': '200 MHz differential system clock'},

    {'name': 'gth_refclk0', 'kind': 'diff_clock', 'component': 'gth_refclk0',
     'ports': ('gth_refclk0_p', 'gth_refclk0_n'), 'preferred': ['util_ds_buf'], 'preset': 'gt_refclk_preset',
     'description': 'GTH reference clock 0 from Si570 U3'},

    {'name': 'cam0_mipi_4lane', 'kind': 'mipi', 'component': 'cam0', 'lanes': 4, 'preset': 'cam0_mipi_4lane_preset',
     'clk': ('cam0_clk_p', 'cam0_clk_n'),
     'data': [('cam0_d0_p', 'cam0_d0_n'), ('cam0_d1_p', 'cam0_d1_n'), ('cam0_d2_p', 'cam0_d2_n'), ('cam0_d3_p', 'cam0_d3_n')],
     'description': 'Camera 0 MIPI CSI-2, 4 lanes'},
    {'name': 'cam0_mipi_2lane', 'kind': 'mipi', 'component': 'cam0', 'lanes': 2, 'preset': 'cam0_mipi_2lane_preset',
     'clk': ('cam0_clk_p', 'cam0_clk_n'),
     'data': [('cam0_d0_p', 'cam0_d0_n'), ('cam0_d1_p', 'cam0_d1_n')],
     'description': 'Camera 0 MIPI CSI-2, 2 lanes (D0, D1)'},
    {'name': 'cam1_mipi_4lane', 'kind': 'mipi', 'component': 'cam1', 'lanes': 4, 'preset': 'cam1_mipi_4lane_preset',
     'clk': ('cam1_clk_p', 'cam1_clk_n'),
     'data': [('cam1_d0_p', 'cam1_d0_n'), ('cam1_d1_p', 'cam1_d1_n'), ('cam1_d2_p', 'cam1_d2_n'), ('cam1_d3_p', 'cam1_d3_n')],
     'description': 'Camera 1 MIPI CSI-2, 4 lanes'},
    {'name': 'cam1_mipi_2lane', 'kind': 'mipi', 'component': 'cam1', 'lanes': 2, 'preset': 'cam1_mipi_2lane_preset',
     'clk': ('cam1_clk_p', 'cam1_clk_n'),
     'data': [('cam1_d0_p', 'cam1_d0_n'), ('cam1_d1_p', 'cam1_d1_n')],
     'description': 'Camera 1 MIPI CSI-2, 2 lanes (D0, D1)'},

    {'name': 'cam_ctrl_4bits', 'kind': 'gpio_out', 'component': 'cam_ctrl', 'preset': 'cam_ctrl_4bits_preset',
     'bits': ['cam0_reset_n', 'cam0_gpio1', 'cam1_reset_n', 'cam1_gpio1'],
     'description': 'Camera resets and GPIO1'},

    {'name': 'slvs_ec_iic', 'kind': 'iic', 'component': 'slvs_ec_iic', 'preset': 'iic_400k_preset',
     'scl': 'slvs_ec_scl', 'sda': 'slvs_ec_sda', 'preferred': ['axi_iic'],
     'description': 'SLVS-EC sensor I2C'},

    {'name': 'slvs_ec_ctrl', 'kind': 'gpio_io', 'component': 'slvs_ec_ctrl', 'preset': 'slvs_ec_ctrl_preset',
     'bits': ['slvs_ec_rst_n', 'slvs_ec_xce', 'slvs_ec_xmaster', 'slvs_ec_xhs', 'slvs_ec_xvs',
              'slvs_ec_trig1', 'slvs_ec_gpio7_trig2', 'slvs_ec_tout0', 'slvs_ec_tout1', 'slvs_ec_tout2',
              'slvs_ec_gpio6', 'slvs_ec_gpio10_omode_fsm', 'slvs_ec_gpio14_slamode2',
              'slvs_ec_gpio16_slamode1', 'slvs_ec_miso'],
     'description': 'SLVS-EC sensor control and sync signals'},

    {'name': 'imu_spi', 'kind': 'spi', 'component': 'imu', 'preset': 'spi_1ss_preset',
     'sck': 'imu_sclk', 'io0': 'imu_mosi', 'io1': 'imu_miso', 'ss': 'imu_cs_n',
     'description': 'ICM-42688-P IMU SPI'},
    {'name': 'imu_int_2bits', 'kind': 'gpio_io', 'component': 'imu_int', 'preset': 'imu_int_2bits_preset',
     'bits': ['imu_int1', 'imu_int2'],
     'description': 'IMU INT1 and INT2/FSYNC'},

    {'name': 'baro_spi', 'kind': 'spi', 'component': 'baro', 'preset': 'spi_1ss_preset',
     'sck': 'baro_sclk', 'io0': 'baro_mosi', 'io1': 'baro_miso', 'ss': 'baro_cs_n',
     'description': 'MS5611 barometer SPI'},

    {'name': 'board_ctrl_3bits', 'kind': 'gpio_out', 'component': 'board_ctrl', 'preset': 'board_ctrl_3bits_preset',
     'bits': ['dp_pwr_en', 'fan_pwm_n', 'baro_ps'],
     'description': 'DP power enable, fan, barometer protocol select'},

    {'name': 'board_status_5bits', 'kind': 'gpio_in', 'component': 'board_status', 'preset': 'board_status_5bits_preset',
     'bits': ['fmc_prsnt_m2c_n', 'dp_pwr_fault_n', 'som_5v_alert_n', 'vadj_imon_alert_n', 'vadj_pmbus_alert_n'],
     'description': 'FMC present, DP power fault and power-monitor alerts'},
]

# ---------------------------------------------------------------------------
# Carrier-specific PS configuration, applied on top of the K26 SOM base
# (tools/k26_som_ps_preset.py). Order matters only for duplicate keys: the
# carrier value wins.
# ---------------------------------------------------------------------------
CARRIER_PS_PARAMS = [
    # UART1 -> FT4232H (IC9) channel, the Linux console. MIO36 TX, MIO37 RX.
    ('PSU__UART1__PERIPHERAL__ENABLE',      '1'),
    ('PSU__UART1__PERIPHERAL__IO',          'MIO 36 .. 37'),

    # I2C0 -> TCA9548A mux (IC16, 0x76): clocks, EEPROM, cameras, FMC, VADJ PMBus.
    ('PSU__I2C0__PERIPHERAL__ENABLE',       '1'),
    ('PSU__I2C0__PERIPHERAL__IO',           'MIO 74 .. 75'),

    # GPIO bank 1 for the loose carrier MIO (MIO44 USB PHY reset via PIC, J16 etc.)
    ('PSU__GPIO1_MIO__PERIPHERAL__ENABLE',  '1'),
    ('PSU__GPIO1_MIO__IO',                  'MIO 26 .. 51'),

    # Mini DisplayPort J4: 2 lanes. GTR1 = DP lane 0, GTR0 = DP lane 1. 27 MHz on REFCLK0.
    ('PSU__DISPLAYPORT__PERIPHERAL__ENABLE', '1'),
    ('PSU__DPAUX__PERIPHERAL__ENABLE',      '1'),
    ('PSU__DPAUX__PERIPHERAL__IO',          'MIO 27 .. 30'),
    ('PSU__DP__LANE_SEL',                   'Dual Lower'),
    ('PSU__DISPLAYPORT__LANE0__ENABLE',     '1'),
    ('PSU__DISPLAYPORT__LANE0__IO',         'GT Lane1'),
    ('PSU__DISPLAYPORT__LANE1__ENABLE',     '1'),
    ('PSU__DISPLAYPORT__LANE1__IO',         'GT Lane0'),
    ('PSU__DP__REF_CLK_SEL',                'Ref Clk0'),
    ('PSU__DP__REF_CLK_FREQ',               '27'),
    ('PSU__CRF_APB__DP_VIDEO_REF_CTRL__SRCSEL', 'VPLL'),
    ('PSU__CRF_APB__DP_AUDIO_REF_CTRL__SRCSEL', 'RPLL'),
    ('PSU__CRF_APB__DP_STC_REF_CTRL__SRCSEL',   'RPLL'),

    # USB 2.0 ULPI PHY USB3320 (IC5) on MIO52-63 + USB 3.0 on GTR2. 26 MHz on REFCLK1.
    ('PSU__USB0__PERIPHERAL__ENABLE',       '1'),
    ('PSU__USB0__PERIPHERAL__IO',           'MIO 52 .. 63'),
    ('PSU__USB3_0__PERIPHERAL__ENABLE',     '1'),
    ('PSU__USB3_0__PERIPHERAL__IO',         'GT Lane2'),
    ('PSU__USB0__REF_CLK_SEL',              'Ref Clk1'),
    ('PSU__USB0__REF_CLK_FREQ',             '26'),
    ('PSU__USB__RESET__MODE',               'Boot Pin'),
    ('PSU__USB0__RESET__ENABLE',            '1'),
    ('PSU__CRL_APB__USB0_BUS_REF_CTRL__SRCSEL', 'IOPLL'),
    ('PSU__CRL_APB__USB0_BUS_REF_CTRL__FREQMHZ', '250'),
    ('PSU__CRL_APB__USB3_DUAL_REF_CTRL__SRCSEL', 'IOPLL'),
    ('PSU__CRL_APB__USB3_DUAL_REF_CTRL__FREQMHZ', '20'),

    # microSD J6 through PI4ULS3V4857 (IC6), SD 3.0 with MIO39 voltage select,
    # MIO45 card detect, MIO43 card power (via PIC U4 and Q8/Q9).
    ('PSU__SD1__PERIPHERAL__ENABLE',        '1'),
    ('PSU__SD1__PERIPHERAL__IO',            'MIO 39 .. 51'),
    ('PSU__SD1__DATA_TRANSFER_MODE',        '8Bit'),
    ('PSU__SD1__SLOT_TYPE',                 'SD 3.0'),
    ('PSU__SD1__GRP_CD__ENABLE',            '1'),
    ('PSU__SD1__GRP_CD__IO',                'MIO 45'),
    ('PSU__SD1__GRP_POW__ENABLE',           '1'),
    ('PSU__SD1__GRP_POW__IO',               'MIO 43'),
    ('PSU__SD1__GRP_WP__ENABLE',            '0'),
    ('PSU__CRL_APB__SDIO1_REF_CTRL__SRCSEL', 'IOPLL'),
    ('PSU__CRL_APB__SDIO1_REF_CTRL__FREQMHZ', '200'),

    # SATA J7 on GTR3 (SATA port 1). GTR REFCLK2 is not connected on this
    # carrier, so SATA uses the 125 MHz Si5332 output on REFCLK3.
    ('PSU__SATA__PERIPHERAL__ENABLE',       '1'),
    ('PSU__SATA__LANE0__ENABLE',            '0'),
    ('PSU__SATA__LANE1__ENABLE',            '1'),
    ('PSU__SATA__LANE1__IO',                'GT Lane3'),
    ('PSU__SATA__REF_CLK_SEL',              'Ref Clk3'),
    ('PSU__SATA__REF_CLK_FREQ',             '125'),
    ('PSU__CRF_APB__SATA_REF_CTRL__SRCSEL', 'IOPLL'),
    ('PSU__CRF_APB__SATA_REF_CTRL__FREQMHZ', '250'),
]

# PS-side peripheral summary for the docs.
PS_SUMMARY = [
    ('DDR4',        'SOM',            '4 GB, 64-bit, DDR4-2400, non-ECC (AMD K26 SOM settings)'),
    ('QSPI',        'MIO 0-5',        'SOM 512 Mb boot flash'),
    ('eMMC (SD0)',  'MIO 13-22',      'SOM 16 GB eMMC'),
    ('I2C1',        'MIO 24-25',      'SOM I2C (SOM EEPROM etc.). Not routed to carrier devices.'),
    ('UART1',       'MIO 36-37',      'Linux console on the FT4232H (IC9) behind micro-USB J8'),
    ('DP AUX',      'MIO 27-30',      'Mini DisplayPort J4 AUX/HPD through IC2/IC3'),
    ('DisplayPort', 'GTR1, GTR0',     '2 lanes (GTR1 = lane 0, GTR0 = lane 1), 27 MHz REFCLK0'),
    ('SD1',         'MIO 39-51',      'microSD J6, SD 3.0 (1.8 V switching via IC6), CD MIO45, power MIO43'),
    ('USB0',        'MIO 52-63, GTR2', 'USB3320 ULPI + USB 3.0 SuperSpeed on J5, 26 MHz REFCLK1'),
    ('SATA',        'GTR3',           'SATA port 1 on J7, 125 MHz REFCLK3'),
    ('I2C0',        'MIO 74-75',      'Carrier I2C through TCA9548A mux IC16 at 0x76'),
    ('GPIO',        'MIO 12',         'FWUEN push button S2 (active low)'),
    ('PMU',         'MIO 26, 31, 35', 'GPI0 on MIO26 (J16 pin 1, pulled up), GPI5 on MIO31 (pulled down), GPO3 on MIO35 = TPS3430 IC19 watchdog kick (WDO_N on J16 pin 2)'),
    ('GPIO',        'MIO 44',         'USB PHY reset request to the PIC supervisor'),
]

# TCA9548A (IC16) channel map, address 0x76 (A2=1, A1=1, A0=0).
I2C_MUX = [
    (0, 'Si5332 clock generator U21 (GTR refclks 27/26/125 MHz, USB PHY clock); also on header J12'),
    (1, 'USER_SI570 bus: pull-ups only, nothing fitted'),
    (2, 'Si570 U3, GTH REFCLK0'),
    (3, 'M24C64 EEPROM IC20 (0x51) + INA260 IC15 (SOM 5 V monitor)'),
    (4, 'Camera 1 J14 (CCI)'),
    (5, 'Camera 0 J13 (CCI)'),
    (6, 'FMC J1 I2C (C30/C31), shared with PIC U4'),
    (7, 'VADJ PMBus: MAX15301 U2 + INA226 IC1, shared with PIC U4'),
]

HARDWARE_NOTES = [
    ('VADJ must be 1.8 V for SLVS-EC',
     'Banks 43, 64 and 65 all run from VADJ_FMC (default 1.8 V, MAX15301 U2). The SLVS-EC control pins and '
     'sensor I2C pull-ups on bank 64 assume 1.8 V, so leave VADJ at 1.8 V whenever J21 is used. The board files '
     'use LVCMOS18 on every VADJ pin.'),
    ('Fan control is active low',
     'HDC09_FAN_PWM drives Q15, which pulls the gate of the fan switch Q16 low. With the pin low, floating or '
     'unconstrained (R120 pull-down) the fan runs at full speed; driving it high turns the fan off. '
     'The port is named fan_pwm_n and board_ctrl_3bits defaults it to 0. PWM it active low for speed control.'),
    ('FMC LA30, LA32, LA33 are single-ended',
     'They land on HD bank 43. LA32 and LA33 are not on P/N pairs (LA32_P = L9N, LA32_N = L8P; '
     'LA33_P = L11N, LA33_N = L12P), so treat all three as single-ended LVCMOS18.'),
    ('200 MHz clock IO standard',
     'U7 is an LVDS oscillator on HPA_CLK0 (C3/C2). Bank 66 runs at 1.2 V for the MIPI cameras, so the board '
     'files use DIFF_SSTL12, the same choice AMD makes for LVDS oscillators in 1.2 V banks on the ZCU10x boards.'),
    ('200 MHz clock shares a nibble with CAM1 lanes 2/3',
     'C3/C2 are IO_L12P/N_T1U in bank 66, the same nibble as CAM1 D2 (B4/A4) and D3 (D4/C4). '
     'If you use CAM1 in 4-lane mode together with the 200 MHz clock, run placement early to check the '
     'native/component-mode nibble rules.'),
    ('Si570 starts at 300 MHz',
     'The Si570 (570BAB001614DGR) on GTH REFCLK0 powers up at 300 MHz. Reprogram it over PS I2C0 '
     '(mux channel 2) before bringing up GTH channels that need a different reference.'),
    ('Carrier EEPROM location',
     'The carrier EEPROM (M24C64, 0x51) is on PS I2C0 behind the mux (channel 3), not on SOM I2C1 (MIO24/25). '
     'Kria boot firmware does not auto-detect the carrier, so load the carrier device-tree overlay explicitly.'),
    ('Camera resets go through the PIC',
     'cam0_reset_n / cam1_reset_n are requests into PIC U4, which drives CAM_GPIO0 (pin 17) on J13/J14. '
     'The PIC firmware decides the final timing.'),
]
