#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Vivado board file generator for ApotheoTech Kria carriers
#
#   python3 tools/gen_board_files.py                      # Aper-Oculus Rev 1.00
#   python3 tools/gen_board_files.py --carrier <module>   # another carrier table
#
# Reads a carrier description module (see aper_oculus_rev1.py) and writes, for
# every SOM listed in it:
#   board_files/<base>_<som>/<file_version>/board.xml
#   board_files/<base>_<som>/<file_version>/part0_pins.xml
#   board_files/<base>_<som>/<file_version>/preset.xml
#   board_files/<base>_<som>/<file_version>/xitem.json
#   board_files/<base>_<som>/<file_version>/changelog.txt
# plus xdc/<Display>-Master.xdc and docs/PINOUT.md.
#
# Output is deterministic, so a git diff of the generated files is a clean
# review of any table change.
# ---------------------------------------------------------------------------
import argparse
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from k26_som_ps_preset import K26_SOM_PS_PARAMS  # noqa: E402

FMC_ROW_OFFSET = {'A': 0, 'B': 40, 'C': 80, 'D': 120, 'E': 160,
                  'F': 200, 'G': 240, 'H': 280, 'J': 320, 'K': 360}

LICENSE_HEADER = """<!--
  Copyright (C) {year} ApotheoTech LLC. Licensed under the Apache License, Version 2.0.
  The PS base configuration in preset.xml is derived from AMD's Kria K26 SOM board
  files (Copyright (C) 2023 Advanced Micro Devices, Inc., Apache License 2.0).
  GENERATED FILE: edit tools/{carrier}.py and re-run tools/gen_board_files.py.
-->"""

YEAR = 2026


def esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def fmc_index(pos):
    return FMC_ROW_OFFSET[pos[0]] + int(pos[1:])


# ---------------------------------------------------------------------------
# Pin index plan for part0_pins.xml
#   chip components first, in COMPONENTS order, each block contiguous;
#   then every FMC pin.
# ---------------------------------------------------------------------------
def build_pin_plan(c):
    sig = {s['name']: s for s in c.SIGNALS}
    plan = []          # list of signal dicts with 'index'
    comp_range = {}    # component name -> (first, last)
    idx = 0
    for comp in c.COMPONENTS:
        first = idx
        for pname in comp['pins']:
            s = dict(sig[pname])
            s['index'] = idx
            plan.append(s)
            idx += 1
        comp_range[comp['name']] = (first, idx - 1)
    fmc_plan = []
    for f in c.FMC:
        s = dict(f)
        s['index'] = idx
        s['desc'] = f"FMC {f['pos']}"
        plan.append(s)
        fmc_plan.append(s)
        idx += 1
    return plan, comp_range, fmc_plan


# ---------------------------------------------------------------------------
# part0_pins.xml
# ---------------------------------------------------------------------------
def emit_part0_pins(c, som, plan):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
           LICENSE_HEADER.format(year=YEAR, carrier=c.__name__),
           f'<part_info part_name="{som["part"]}">',
           '  <pins>']
    for s in plan:
        attrs = f'index="{s["index"]}" name="{s["name"]}"'
        if s['iostd']:
            attrs += f' iostandard="{s["iostd"]}"'
        attrs += f' loc="{s["loc"]}"'
        out.append(f'    <pin {attrs}/> <!-- {esc(s["net"])} / {s["som"]} / bank {s["bank"]} -->')
    out += ['  </pins>', '</part_info>', '']
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# board.xml interface emitters
# ---------------------------------------------------------------------------
def _pm(logical, physical, direction, pins, vector):
    lines = []
    lr = f' left="{len(pins) - 1}" right="0"' if vector else ''
    lines.append(f'            <port_map logical_port="{logical}" physical_port="{physical}" dir="{direction}"{lr}>')
    lines.append('              <pin_maps>')
    for i, p in enumerate(pins):
        lines.append(f'                <pin_map port_index="{i}" component_pin="{p}"/>')
    lines.append('              </pin_maps>')
    lines.append('            </port_map>')
    return lines


def _preferred(ips):
    lines = ['          <preferred_ips>']
    for order, ip in enumerate(ips):
        lines.append(f'            <preferred_ip vendor="xilinx.com" library="ip" name="{ip}" order="{order}"/>')
    lines.append('          </preferred_ips>')
    return lines


def emit_interface(itf, comps):
    k = itf['kind']
    n = itf['name']
    comp = comps[itf['component']]
    type_map = {
        'diff_clock': ('slave',  'xilinx.com:interface:diff_clock_rtl:1.0'),
        'mipi':       ('slave',  'xilinx.com:interface:mipi_phy_rtl:1.0'),
        'gpio_out':   ('master', 'xilinx.com:interface:gpio_rtl:1.0'),
        'gpio_in':    ('master', 'xilinx.com:interface:gpio_rtl:1.0'),
        'gpio_io':    ('master', 'xilinx.com:interface:gpio_rtl:1.0'),
        'iic':        ('master', 'xilinx.com:interface:iic_rtl:1.0'),
        'spi':        ('master', 'xilinx.com:interface:spi_rtl:1.0'),
    }
    mode, itype = type_map[k]
    preset = f' preset_proc="{itf["preset"]}"' if itf.get('preset') else ''
    L = [f'        <interface mode="{mode}" name="{n}" type="{itype}" of_component="{itf["component"]}"{preset}>',
         f'          <description>{esc(itf["description"])}</description>']
    if k == 'diff_clock':
        L += ['          <parameters>',
              f'            <parameter name="frequency" value="{comp["frequency"]}"/>',
              '          </parameters>']
        L += _preferred(itf['preferred'])
        L.append('          <port_maps>')
        L += _pm('CLK_P', itf['ports'][0], 'in', [itf['ports'][0]], False)
        L += _pm('CLK_N', itf['ports'][1], 'in', [itf['ports'][1]], False)
    elif k == 'mipi':
        L += _preferred(['mipi_csi2_rx_subsystem', 'mipi_dphy'])
        L.append('          <port_maps>')
        L += _pm('CLK_P', f'{n}_clk_p', 'in', [itf['clk'][0]], False)
        L += _pm('CLK_N', f'{n}_clk_n', 'in', [itf['clk'][1]], False)
        L += _pm('DATA_P', f'{n}_data_p', 'in', [d[0] for d in itf['data']], True)
        L += _pm('DATA_N', f'{n}_data_n', 'in', [d[1] for d in itf['data']], True)
    elif k == 'gpio_out':
        L += _preferred(['axi_gpio'])
        L.append('          <port_maps>')
        L += _pm('TRI_O', f'{n}_tri_o', 'out', itf['bits'], True)
    elif k == 'gpio_in':
        L += _preferred(['axi_gpio'])
        L.append('          <port_maps>')
        L += _pm('TRI_I', f'{n}_tri_i', 'in', itf['bits'], True)
    elif k == 'gpio_io':
        L += _preferred(['axi_gpio'])
        L.append('          <port_maps>')
        L += _pm('TRI_I', f'{n}_i', 'inout', itf['bits'], True)
        L += _pm('TRI_O', f'{n}_o', 'inout', itf['bits'], True)
        L += _pm('TRI_T', f'{n}_t', 'inout', itf['bits'], True)
    elif k == 'iic':
        L += _preferred(itf['preferred'])
        L.append('          <port_maps>')
        for sfx in ('I', 'O', 'T'):
            L += _pm(f'SCL_{sfx}', f'{n}_scl_{sfx.lower()}', 'inout', [itf['scl']], False)
        for sfx in ('I', 'O', 'T'):
            L += _pm(f'SDA_{sfx}', f'{n}_sda_{sfx.lower()}', 'inout', [itf['sda']], False)
    elif k == 'spi':
        L += _preferred(['axi_quad_spi'])
        L.append('          <port_maps>')
        for logical, key in (('SCK', 'sck'), ('IO0', 'io0'), ('IO1', 'io1'), ('SS', 'ss')):
            for sfx in ('I', 'O', 'T'):
                L += _pm(f'{logical}_{sfx}', f'{n}_{key}_io', 'inout', [itf[key]], False)
    else:
        raise ValueError(k)
    L += ['          </port_maps>', '        </interface>']
    return L


def emit_board_xml(c, som, comp_range, fmc_plan):
    B = c.BOARD
    name = f'{B["base_name"]}_{som["suffix"]}'
    disp = f'{B["display_name"]} + {som["som"]} SOM'
    comps = {cp['name']: cp for cp in c.COMPONENTS}
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
         LICENSE_HEADER.format(year=YEAR, carrier=c.__name__),
         f'<board schema_version="2.2" vendor="{B["vendor"]}" name="{name}" display_name="{esc(disp)}" '
         f'url="{B["url"]}" preset_file="preset.xml">',
         '  <compatible_board_revisions>',
         f'    <revision id="0">{B["pcb_rev"]}</revision>',
         '  </compatible_board_revisions>',
         f'  <file_version>{B["file_version"]}</file_version>',
         f'  <description>{esc(B["description"])} SOM: Kria {som["som"]} ({som["part"]}).</description>',
         '  <components>',
         f'    <component name="part0" display_name="Kria {som["som"]} SOM on {esc(B["display_name"])}" type="fpga" '
         f'part_name="{som["part"]}" pin_map_file="part0_pins.xml" vendor="xilinx" '
         'spec_url="https://www.amd.com/en/products/system-on-modules/kria/k26.html">',
         f'      <description>Kria {som["som"]} SOM ({som["part"]}) on the {esc(B["display_name"])} carrier '
         f'({B["pcb"]} Rev {B["pcb_rev"]})</description>',
         '      <interfaces>',
         f'        <interface mode="master" name="ps8_fixedio" type="xilinx.com:zynq_ultra_ps_e:fixedio_rtl:1.0" '
         f'of_component="ps8_fixedio" preset_proc="{B["base_name"]}_mpsoc_preset">',
         '          <description>Zynq UltraScale+ PS: SOM DDR4/QSPI/eMMC plus carrier UART, I2C, SD, USB 3.0, DP, SATA</description>',
         '          <preferred_ips>',
         '            <preferred_ip vendor="xilinx.com" library="ip" name="zynq_ultra_ps_e" order="0"/>',
         '          </preferred_ips>',
         '        </interface>']
    for itf in c.INTERFACES:
        L += emit_interface(itf, comps)
    L += ['      </interfaces>', '    </component>', '',
          f'    <component name="ps8_fixedio" display_name="PS8 Fixed IO" type="chip" sub_type="fixed_io" major_group=""/>']
    for cp in c.COMPONENTS:
        extra = ''
        if cp.get('part_name'):
            extra += f' part_name="{esc(cp["part_name"])}"'
        if cp.get('vendor'):
            extra += f' vendor="{esc(cp["vendor"])}"'
        L.append(f'    <component name="{cp["name"]}" display_name="{esc(cp["display"])}" type="chip" '
                 f'sub_type="{cp["sub_type"]}" major_group="{esc(cp["major_group"])}"{extra}>')
        L.append(f'      <description>{esc(cp["description"])}</description>')
        if cp.get('modes'):
            L.append('      <component_modes>')
            for mname, mdisp in cp['modes']:
                L += [f'        <component_mode name="{mname}" display_name="{esc(mdisp)}">',
                      '          <interfaces>',
                      f'            <interface name="{mname}"/>',
                      '          </interfaces>',
                      '          <preferred_ips>',
                      '            <preferred_ip vendor="xilinx.com" library="ip" name="mipi_csi2_rx_subsystem" order="0"/>',
                      '            <preferred_ip vendor="xilinx.com" library="ip" name="mipi_dphy" order="1"/>',
                      '          </preferred_ips>',
                      '        </component_mode>']
            L.append('      </component_modes>')
        if cp.get('frequency'):
            L += ['      <parameters>',
                  f'        <parameter name="frequency" value="{cp["frequency"]}"/>',
                  '      </parameters>']
        L.append('    </component>')
    # FMC connector
    L += ['',
          '    <component name="fmc" display_name="FMC J1" type="connector" sub_type="fmc_hpc">',
          '      <description>FMC J1 (HPC footprint). Wired: LA00-LA33, CLK0/CLK1_M2C, GBTCLK0_M2C, '
          'DP0-DP1 (TX+RX), DP2-DP3 (TX only). VADJ is 1.8 V max (HP banks 64/65). '
          'LA30/LA32/LA33 are on HD bank 43 and single-ended only; LA32 and LA33 are not on P/N pairs.</description>',
          '      <pins>']
    for f in sorted(fmc_plan, key=lambda x: fmc_index(x['pos'])):
        L.append(f'        <pin index="{fmc_index(f["pos"])}" name="{f["name"]}"/> <!-- {f["pos"]} -->')
    L += ['      </pins>', '    </component>', '  </components>', '',
          '  <jtag_chains>',
          '    <jtag_chain name="chain1">',
          '      <position name="0" component="part0"/>',
          '    </jtag_chain>',
          '  </jtag_chains>', '',
          '  <connections>']
    for cp in c.COMPONENTS:
        a, b = comp_range[cp['name']]
        L += [f'    <connection name="part0_{cp["name"]}" component1="part0" component2="{cp["name"]}">',
              f'      <connection_map name="part0_{cp["name"]}_1" typical_delay="5" '
              f'c1_st_index="{a}" c1_end_index="{b}" c2_st_index="0" c2_end_index="{b - a}"/>',
              '    </connection>']
    L.append('    <connection name="part0_fmc" component1="part0" component2="fmc">')
    for f in fmc_plan:
        fi = fmc_index(f['pos'])
        L.append(f'      <connection_map name="part0_{f["name"]}" typical_delay="5" '
                 f'c1_st_index="{f["index"]}" c1_end_index="{f["index"]}" c2_st_index="{fi}" c2_end_index="{fi}"/>')
    L += ['    </connection>', '  </connections>', '</board>', '']
    return '\n'.join(L)


# ---------------------------------------------------------------------------
# preset.xml
# ---------------------------------------------------------------------------
def merged_ps_params(c):
    merged = {}
    order = []
    for k, v in list(K26_SOM_PS_PARAMS) + list(c.CARRIER_PS_PARAMS):
        if k not in merged:
            order.append(k)
        merged[k] = v
    return [(k, merged[k]) for k in order]


def _ip_preset(proc, ip, ip_interface, params):
    itf = f' ip_interface="{ip_interface}"' if ip_interface else ''
    L = [f'  <ip_preset preset_proc_name="{proc}">',
         f'    <ip vendor="xilinx.com" library="ip" name="{ip}"{itf}>',
         '      <user_parameters>']
    for k, v in params:
        L.append(f'        <user_parameter name="CONFIG.{k}" value="{esc(v)}"/>')
    L += ['      </user_parameters>', '    </ip>', '  </ip_preset>']
    return L


def emit_preset_xml(c):
    B = c.BOARD
    L = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
         LICENSE_HEADER.format(year=YEAR, carrier=c.__name__),
         '<ip_presets schema="1.0">',
         f'  <ip_preset preset_proc_name="{B["base_name"]}_mpsoc_preset">',
         '    <ip vendor="xilinx.com" library="ip" name="zynq_ultra_ps_e" version="*">',
         '      <user_parameters>']
    # Two blocks in sequence, exactly like Vivado applying AMD's SOM preset and
    # then a carrier preset (KV260/KR260 flow). Some SOM keys depend on order
    # (ACPU__FRAC_ENABLED before the 1333.333 MHz ACPU clock), so the SOM block
    # is kept verbatim, duplicates included. Carrier values come last and win.
    L.append('        <!-- ===== K26 SOM base: AMD k26c 1.4 preset "mpsoc_preset_vsom", verbatim ===== -->')
    for k, v in K26_SOM_PS_PARAMS:
        L.append(f'        <user_parameter name="CONFIG.{k}" value="{esc(v)}"/>')
    L.append(f'        <!-- ===== {esc(B["display_name"])} carrier ({B["pcb"]} Rev {B["pcb_rev"]}) ===== -->')
    for k, v in c.CARRIER_PS_PARAMS:
        L.append(f'        <user_parameter name="CONFIG.{k}" value="{esc(v)}"/>')
    L += ['      </user_parameters>', '    </ip>', '  </ip_preset>', '']

    # MIPI CSI-2 RX presets
    for itf in c.INTERFACES:
        if itf['kind'] != 'mipi':
            continue
        cam = itf['component']
        locs = c.MIPI_LOCS[cam]
        p = [('CMN_NUM_LANES', str(itf['lanes'])),
             ('CMN_PXL_FORMAT', c.MIPI_DEFAULT_PIXEL_FORMAT),
             ('CMN_INC_IIC', 'false'),
             ('DPY_LINE_RATE', str(c.MIPI_DEFAULT_LINE_RATE)),
             ('HP_IO_BANK_SELECTION', '66'),
             ('CLK_LANE_IO_LOC', locs['clk'])]
        for i in range(itf['lanes']):
            p.append((f'DATA_LANE{i}_IO_LOC', locs['data'][i]))
        L += _ip_preset(itf['preset'], 'mipi_csi2_rx_subsystem', 'mipi_phy_if', p)
        L.append('')

    # GPIO presets
    for itf in c.INTERFACES:
        if not itf['kind'].startswith('gpio'):
            continue
        width = str(len(itf['bits']))
        if itf['kind'] == 'gpio_out':
            p = [('C_GPIO_WIDTH', width), ('C_ALL_OUTPUTS', '1'), ('C_ALL_INPUTS', '0')]
            if itf['name'] == 'board_ctrl_3bits':
                p.append(('C_DOUT_DEFAULT', '0x00000001'))   # DP power on, fan on (active low), baro SPI
        elif itf['kind'] == 'gpio_in':
            p = [('C_GPIO_WIDTH', width), ('C_ALL_INPUTS', '1'), ('C_ALL_OUTPUTS', '0'),
                 ('C_INTERRUPT_PRESENT', '1')]
        else:
            p = [('C_GPIO_WIDTH', width), ('C_ALL_INPUTS', '0'), ('C_ALL_OUTPUTS', '0')]
        L += _ip_preset(itf['preset'], 'axi_gpio', 'GPIO', p)
        L.append('')

    # Shared presets
    L += _ip_preset('iic_400k_preset', 'axi_iic', 'IIC',
                    [('IIC_FREQ_KHZ', '400'), ('TEN_BIT_ADR', '7_bit')])
    L.append('')
    L += _ip_preset('spi_1ss_preset', 'axi_quad_spi', 'SPI_0',
                    [('C_SPI_MODE', '0'), ('C_NUM_SS_BITS', '1'),
                     ('C_USE_STARTUP', '0'), ('C_USE_STARTUP_INT', '0')])
    L.append('')
    L += _ip_preset('gt_refclk_preset', 'util_ds_buf', None,
                    [('C_BUF_TYPE', 'IBUFDSGTE'), ('C_SIZE', '1')])
    L += ['', '</ip_presets>', '']
    return '\n'.join(L)


# ---------------------------------------------------------------------------
# xitem.json / changelog
# ---------------------------------------------------------------------------
def emit_xitem(c, som):
    B = c.BOARD
    item = {'config': {'items': [{'infra': {
        'name': f'{B["base_name"]}_{som["suffix"]}',
        'display': f'{B["display_name"]} + {som["som"]} SOM',
        'revision': B['file_version'],
        'description': f'{B["display_name"]} Kria carrier ({B["pcb"]} Rev {B["pcb_rev"]}) with {som["som"]} SOM',
        'company': B['vendor'],
        'company_display': B['vendor_display'],
        'author': B['vendor_display'],
        'contributors': [{'group': B['vendor_display'], 'url': B['url']}],
        'category': 'Evaluation Boards',
        'website': B['url'],
        'search-keywords': ['Kria', 'K26', som['som'], 'SOM', B['display_name'], B['pcb'], 'FMC', 'SLVS-EC', 'MIPI'],
    }}]}, '_major': 1, '_minor': 0}
    return json.dumps(item, indent=2) + '\n'


def emit_changelog(c):
    B = c.BOARD
    return (f'######### {B["display_name"]} board files changelog #########\n'
            f'{B["file_version"]} (PCB {B["pcb"]} Rev {B["pcb_rev"]})\n'
            '  Initial release: PS preset (K26 SOM DDR4/QSPI/eMMC + carrier UART1, I2C0, SD1, USB0/USB3,\n'
            '  DisplayPort, SATA), 200 MHz clock, Si570 GTH refclk, 2x MIPI CSI-2 (2/4 lane), camera control,\n'
            '  SLVS-EC sensor I2C/control, IMU SPI, barometer SPI, board control/status GPIO, FMC J1 connector.\n')


# ---------------------------------------------------------------------------
# Master XDC
# ---------------------------------------------------------------------------
def emit_master_xdc(c):
    B = c.BOARD
    L = [f'## {B["display_name"]} ({B["pcb"]} Rev {B["pcb_rev"]}) master constraints, Kria K26C/K26I SOM',
         '## GENERATED by tools/gen_board_files.py. Uncomment the lines you use and rename ports to match your design.',
         '## Port names match the board-file pin names, so board-interface designs and RTL designs share one naming.',
         '##',
         '## Bank supplies:']
    for bank, (short, rail, volts, use) in sorted(c.BANKS.items()):
        v = f'{volts:.1f} V' if volts else 'n/a'
        L.append(f'##   Bank {bank:<3} {short:<4} {rail:<9} {v:<6} {use}')
    L.append('')

    def row(s):
        d = f'{{ PACKAGE_PIN {s["loc"]:<4}' + (f' IOSTANDARD {s["iostd"]}' if s['iostd'] else '') + ' }'
        port = f'[get_ports {{ {s["name"]} }}];'
        return f'#set_property -dict {d:<46} {port:<44} # {s["net"]}, {s["som"]}, {s.get("desc", "")}'

    sig = {s['name']: s for s in list(c.SIGNALS) + list(c.XDC_ONLY_SIGNALS)}
    groups = [
        ('200 MHz system clock (bank 66, 1.2 V)', ['sys_clk_200_p', 'sys_clk_200_n'],
         ['#create_clock -period 5.000 -name sys_clk_200 [get_ports { sys_clk_200_p }]']),
        ('MIPI CSI-2 camera 0, J13 (bank 66). The MIPI CSI-2 RX Subsystem writes its own pin constraints;'
         ' these lines are for reference or for a hand-instantiated D-PHY.',
         [p for p in ['cam0_clk_p', 'cam0_clk_n', 'cam0_d0_p', 'cam0_d0_n', 'cam0_d1_p', 'cam0_d1_n',
                      'cam0_d2_p', 'cam0_d2_n', 'cam0_d3_p', 'cam0_d3_n']], []),
        ('MIPI CSI-2 camera 1, J14 (bank 66)',
         ['cam1_clk_p', 'cam1_clk_n', 'cam1_d0_p', 'cam1_d0_n', 'cam1_d1_p', 'cam1_d1_n',
          'cam1_d2_p', 'cam1_d2_n', 'cam1_d3_p', 'cam1_d3_n'], []),
        ('Camera reset / GPIO (3.3 V)', ['cam0_reset_n', 'cam0_gpio1', 'cam1_reset_n', 'cam1_gpio1'], []),
        ('GTH reference clock 0: Si570 U3 (300 MHz at power-up)', ['gth_refclk0_p', 'gth_refclk0_n'],
         ['#create_clock -period 3.333 -name gth_refclk0 [get_ports { gth_refclk0_p }]']),
        ('FRAMOS SLVS-EC J21: GTH receive lanes (AC-coupled). Lane 0 = GTHE4_CHANNEL_X0Y3, lane 1 = X0Y1.',
         ['slvs_ec_rx0_p', 'slvs_ec_rx0_n', 'slvs_ec_rx1_p', 'slvs_ec_rx1_n'], []),
        ('FRAMOS SLVS-EC J21: sensor I2C and control (bank 64, VADJ = 1.8 V required)',
         ['slvs_ec_scl', 'slvs_ec_sda', 'slvs_ec_rst_n', 'slvs_ec_xce', 'slvs_ec_xmaster', 'slvs_ec_xhs',
          'slvs_ec_xvs', 'slvs_ec_trig1', 'slvs_ec_gpio7_trig2', 'slvs_ec_tout0', 'slvs_ec_tout1',
          'slvs_ec_tout2', 'slvs_ec_gpio6', 'slvs_ec_gpio10_omode_fsm', 'slvs_ec_gpio14_slamode2',
          'slvs_ec_gpio16_slamode1', 'slvs_ec_miso', 'slvs_ec_mclk'], []),
        ('IMU U9 ICM-42688-P, SPI (bank 44, 3.3 V)',
         ['imu_sclk', 'imu_mosi', 'imu_miso', 'imu_cs_n', 'imu_int1', 'imu_int2'], []),
        ('Barometer IC22 MS5611, SPI when baro_ps = 0 (bank 44, 3.3 V)',
         ['baro_sclk', 'baro_mosi', 'baro_miso', 'baro_cs_n', 'baro_ps'], []),
        ('Board control and status (3.3 V). fan_pwm_n is active low: leave it low/unused for full fan speed.',
         ['dp_pwr_en', 'fan_pwm_n', 'fmc_prsnt_m2c_n', 'dp_pwr_fault_n', 'som_5v_alert_n',
          'vadj_imon_alert_n', 'vadj_pmbus_alert_n'], []),
    ]
    for title, names, extra in groups:
        L.append(f'## {title}')
        for nm in names:
            L.append(row(sig[nm]))
        L += extra
        L.append('')

    L.append('## FMC J1, LA pins (banks 65/64 HP, 43 HD; all at VADJ, default 1.8 V).')
    L.append('## LA30/LA32/LA33 are on HD bank 43 and are single-ended only.')
    for f in c.FMC:
        if f['bank'] == 224:
            continue
        s = dict(f)
        s['desc'] = f'FMC {f["pos"]}, bank {f["bank"]}'
        L.append(row(s))
    L.append('#create_clock -period 10.000 -name fmc_clk0_m2c [get_ports { fmc_clk0_m2c_p }]')
    L.append('#create_clock -period 10.000 -name fmc_clk1_m2c [get_ports { fmc_clk1_m2c_p }]')
    L.append('')
    L.append('## FMC J1, GTH lanes and GBTCLK0 (bank 224). Channel map:')
    for ch, tx, rx in c.GTH_CHANNELS:
        L.append(f'##   {ch}: TX = {tx:<24} RX = {rx}')
    for f in c.FMC:
        if f['bank'] != 224:
            continue
        s = dict(f)
        s['desc'] = f'FMC {f["pos"]}'
        L.append(row(s))
    L.append('#create_clock -period 6.400 -name fmc_gbtclk0_m2c [get_ports { fmc_gbtclk0_m2c_p }]')
    L.append('')
    L.append('## Bitstream: the K26 SOM configures over PCAP from the PS, so no SPI-flash settings are needed here.')
    L.append('')
    return '\n'.join(L)


# ---------------------------------------------------------------------------
# PINOUT.md
# ---------------------------------------------------------------------------
def emit_pinout_md(c):
    B = c.BOARD
    L = [f'# {B["display_name"]} pinout ({B["pcb"]} Rev {B["pcb_rev"]})', '',
         'Generated by `tools/gen_board_files.py` from the carrier table. '
         'Every row was checked against the KiCad netlist and AMD\'s K26 SOM XDC.', '',
         '## Bank supplies', '', '| Bank | Name | Rail | VCCO | Used for |', '|---|---|---|---|---|']
    for bank, (short, rail, volts, use) in sorted(c.BANKS.items()):
        L.append(f'| {bank} | {short} | {rail} | {f"{volts:.1f} V" if volts else "n/a"} | {use} |')
    L += ['', '## PS peripherals (configured by the `ps8_fixedio` preset)', '',
          '| Peripheral | Pins | Notes |', '|---|---|---|']
    for p, pins, note in c.PS_SUMMARY:
        L.append(f'| {p} | {pins} | {note} |')
    L += ['', '## PS I2C0 mux (TCA9548A IC16, address 0x76)', '', '| Channel | Devices |', '|---|---|']
    for ch, dev in c.I2C_MUX:
        L.append(f'| {ch} | {dev} |')
    L += ['', '## Board interfaces', '', '| Interface | Type | Pins (bit order) |', '|---|---|---|']
    for itf in c.INTERFACES:
        if itf['kind'] == 'mipi':
            pins = ', '.join([itf['clk'][0]] + [d[0] for d in itf['data']]) + ' (and _n)'
        elif itf['kind'] == 'diff_clock':
            pins = ', '.join(itf['ports'])
        elif itf['kind'] == 'iic':
            pins = f'{itf["scl"]}, {itf["sda"]}'
        elif itf['kind'] == 'spi':
            pins = f'SCK {itf["sck"]}, MOSI {itf["io0"]}, MISO {itf["io1"]}, SS {itf["ss"]}'
        else:
            pins = ', '.join(f'[{i}] {b}' for i, b in enumerate(itf['bits']))
        L.append(f'| `{itf["name"]}` | {itf["kind"]} | {pins} |')
    L.append('| `fmc` connector | fmc_hpc | LA00-LA33, CLK0/1_M2C, GBTCLK0_M2C, DP0-DP3 (see below) |')
    L += ['', '## PL and GTH signals', '', '| Port | Ball | Bank | IOSTANDARD | SOM pin | Carrier net | Notes |',
          '|---|---|---|---|---|---|---|']
    for s in list(c.SIGNALS) + list(c.XDC_ONLY_SIGNALS):
        L.append(f'| `{s["name"]}` | {s["loc"]} | {s["bank"]} | {s["iostd"] or "GT"} | {s["som"]} | {s["net"]} | {s["desc"]} |')
    L += ['', '## FMC J1', '', '| FMC pin | Port | Ball | Bank | SOM pin | Carrier net |', '|---|---|---|---|---|---|']
    for f in sorted(c.FMC, key=lambda x: (x['pos'][0], int(x['pos'][1:]))):
        L.append(f'| {f["pos"]} | `{f["name"]}` | {f["loc"]} | {f["bank"]} | {f["som"]} | {f["net"]} |')
    L += ['', '## GTH quad 224', '', '| Channel | TX | RX |', '|---|---|---|']
    for ch, tx, rx in c.GTH_CHANNELS:
        L.append(f'| {ch} | {tx} | {rx} |')
    L += ['', '| Reference clock | Source |', '|---|---|']
    for rc, src in c.GTH_REFCLKS:
        L.append(f'| {rc} | {src} |')
    L += ['', '## Hardware notes', '']
    for title, body in c.HARDWARE_NOTES:
        L.append(f'**{title}.** {body}')
        L.append('')
    return '\n'.join(L)


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--carrier', default='aper_oculus_rev1', help='carrier description module in tools/')
    ap.add_argument('--out', default=ROOT, help='repo root to write into')
    args = ap.parse_args()
    c = importlib.import_module(args.carrier)
    B = c.BOARD
    plan, comp_range, fmc_plan = build_pin_plan(c)
    written = []
    for som in c.SOMS:
        d = os.path.join(args.out, 'board_files', f'{B["base_name"]}_{som["suffix"]}', B['file_version'])
        os.makedirs(d, exist_ok=True)
        files = {
            'part0_pins.xml': emit_part0_pins(c, som, plan),
            'board.xml': emit_board_xml(c, som, comp_range, fmc_plan),
            'preset.xml': emit_preset_xml(c),
            'xitem.json': emit_xitem(c, som),
            'changelog.txt': emit_changelog(c),
        }
        for fn, text in files.items():
            p = os.path.join(d, fn)
            with open(p, 'w', newline='\n') as fh:
                fh.write(text)
            written.append(p)
    xdc_dir = os.path.join(args.out, 'xdc')
    os.makedirs(xdc_dir, exist_ok=True)
    p = os.path.join(xdc_dir, f'{B["display_name"]}-Master.xdc')
    with open(p, 'w', newline='\n') as fh:
        fh.write(emit_master_xdc(c))
    written.append(p)
    doc_dir = os.path.join(args.out, 'docs')
    os.makedirs(doc_dir, exist_ok=True)
    p = os.path.join(doc_dir, 'PINOUT.md')
    with open(p, 'w', newline='\n') as fh:
        fh.write(emit_pinout_md(c))
    written.append(p)
    for p in written:
        print('wrote', os.path.relpath(p, args.out))


if __name__ == '__main__':
    main()
