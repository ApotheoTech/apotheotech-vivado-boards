#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Consistency checks for the generated board files.
#
#   python3 tools/check_board_files.py
#   python3 tools/check_board_files.py --netlist APT-KRIA-FMC.xml --som-xdc Kria_K26_SOM_Rev1.xdc
#
# Always checks: XML parses, pin indices/names/LOCs unique, every interface pin
# exists and belongs to its component's connection range, connection ranges
# line up, FMC connector indices match VITA 57.1 positions, every preset_proc
# exists, IOSTANDARD matches the bank VCCO.
#
# With --netlist (KiCad "generic" XML netlist) and --som-xdc (AMD K26 SOM
# XDC), also checks every table row against the schematic and the SOM pinout,
# and reports PL/GTH SOM pins that are wired on the carrier but missing from
# the table.
# ---------------------------------------------------------------------------
import argparse
import importlib
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FMC_ROW_OFFSET = {'A': 0, 'B': 40, 'C': 80, 'D': 120, 'E': 160,
                  'F': 200, 'G': 240, 'H': 280, 'J': 320, 'K': 360}

IOSTD_VCCO = {
    'LVCMOS33': 3.3, 'LVCMOS18': 1.8, 'LVCMOS12': 1.2,
    'DIFF_SSTL12': 1.2, 'MIPI_DPHY_DCI': 1.2, 'LVDS': 1.8,
}

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def check_generated(c, board_dir):
    bxml = ET.parse(os.path.join(board_dir, 'board.xml')).getroot()
    pxml = ET.parse(os.path.join(board_dir, 'part0_pins.xml')).getroot()
    rxml = ET.parse(os.path.join(board_dir, 'preset.xml')).getroot()

    pins = {}
    by_name = {}
    locs = {}
    for p in pxml.iter('pin'):
        i = int(p.get('index'))
        if i in pins:
            err(f'{board_dir}: duplicate pin index {i}')
        pins[i] = p
        n = p.get('name')
        if n in by_name:
            err(f'{board_dir}: duplicate pin name {n}')
        by_name[n] = i
        loc = p.get('loc')
        if loc in locs:
            err(f'{board_dir}: LOC {loc} used by {locs[loc]} and {n}')
        locs[loc] = n
    if sorted(pins) != list(range(len(pins))):
        err(f'{board_dir}: part0 pin indices are not contiguous from 0')

    # bank voltage check
    banks = c.BANKS
    sig_bank = {s['name']: s['bank'] for s in list(c.SIGNALS) + list(c.FMC)}
    for n, i in by_name.items():
        std = pins[i].get('iostandard')
        bank = sig_bank.get(n)
        if bank is None:
            err(f'{board_dir}: pin {n} not in carrier table')
            continue
        if not std:
            if bank != 224:
                err(f'{board_dir}: pin {n} has no IOSTANDARD but is not a GT pin')
            continue
        need = IOSTD_VCCO.get(std)
        have = banks[bank][2]
        if need is None:
            warn(f'{board_dir}: unknown IOSTANDARD {std} on {n}')
        elif abs(need - have) > 0.01:
            err(f'{board_dir}: {n} is {std} ({need} V) in bank {bank} at {have} V')

    comps = {cp.get('name'): cp for cp in bxml.iter('component')}
    part0 = comps['part0']
    if part0.get('part_name') not in {s['part'] for s in c.SOMS}:
        err(f'{board_dir}: unexpected part {part0.get("part_name")}')

    # connections
    comp_pins = {}
    fmc_map = {}
    for conn in bxml.iter('connection'):
        c1, c2 = conn.get('component1'), conn.get('component2')
        if c1 != 'part0' or c2 not in comps:
            err(f'{board_dir}: connection {conn.get("name")} references unknown component')
            continue
        for cm in conn.iter('connection_map'):
            a, b = int(cm.get('c1_st_index')), int(cm.get('c1_end_index'))
            x, y = int(cm.get('c2_st_index')), int(cm.get('c2_end_index'))
            if b - a != y - x:
                err(f'{board_dir}: {cm.get("name")} c1/c2 range sizes differ')
            for k in range(a, b + 1):
                if k not in pins:
                    err(f'{board_dir}: {cm.get("name")} index {k} not in part0_pins')
                    continue
                comp_pins.setdefault(c2, set()).add(pins[k].get('name'))
            if comps[c2].get('type') == 'connector':
                fmc_map[a] = x

    # FMC connector indices vs VITA position
    fmc_comp = [cp for cp in comps.values() if cp.get('type') == 'connector']
    for fc in fmc_comp:
        cpins = {int(p.get('index')): p.get('name') for p in fc.iter('pin')}
        for f in c.FMC:
            want = FMC_ROW_OFFSET[f['pos'][0]] + int(f['pos'][1:])
            if cpins.get(want) != f['name']:
                err(f'{board_dir}: FMC {f["pos"]} expected {f["name"]} at index {want}, found {cpins.get(want)}')
            pi = by_name.get(f['name'])
            if fmc_map.get(pi) != want:
                err(f'{board_dir}: part0 pin {f["name"]} maps to FMC index {fmc_map.get(pi)}, expected {want}')

    # interfaces
    presets = {p.get('preset_proc_name') for p in rxml.iter('ip_preset')}
    itf_names = set()
    for itf in part0.iter('interface'):
        n = itf.get('name')
        itf_names.add(n)
        oc = itf.get('of_component')
        if oc not in comps:
            err(f'{board_dir}: interface {n} of_component {oc} missing')
        pp = itf.get('preset_proc')
        if pp and pp not in presets:
            err(f'{board_dir}: interface {n} preset_proc {pp} missing from preset.xml')
        for pm in itf.iter('port_map'):
            left = pm.get('left')
            maps = list(pm.iter('pin_map'))
            if left is not None and int(left) + 1 != len(maps):
                err(f'{board_dir}: {n}.{pm.get("logical_port")} width {int(left) + 1} vs {len(maps)} pin_maps')
            for m in maps:
                cpn = m.get('component_pin')
                if cpn not in by_name:
                    err(f'{board_dir}: {n} references unknown pin {cpn}')
                elif cpn not in comp_pins.get(oc, set()):
                    err(f'{board_dir}: {n} pin {cpn} is not connected to component {oc}')
    for cp in comps.values():
        for cm in cp.iter('component_mode'):
            for i in cm.iter('interface'):
                if i.get('name') not in itf_names:
                    err(f'{board_dir}: component_mode {cm.get("name")} lists unknown interface {i.get("name")}')
    # every chip component except ps8_fixedio must have a connection
    for name, cp in comps.items():
        if name in ('part0', 'ps8_fixedio'):
            continue
        if name not in comp_pins:
            err(f'{board_dir}: component {name} has no connection')
    # PS preset sanity: required DDR keys present
    vals = {}
    for up in rxml.iter('user_parameter'):
        vals[up.get('name')] = up.get('value')   # last wins
    for k, v in (('CONFIG.PSU__DDRC__MEMORY_TYPE', 'DDR 4'), ('CONFIG.PSU__DDRC__BUS_WIDTH', '64 Bit'),
                 ('CONFIG.PSU__DDRC__DEVICE_CAPACITY', '8192 MBits'), ('CONFIG.PSU__DDRC__DRAM_WIDTH', '16 Bits'),
                 ('CONFIG.PSU__DDRC__SPEED_BIN', 'DDR4_2400R'), ('CONFIG.PSU__PSS_REF_CLK__FREQMHZ', '33.333'),
                 ('CONFIG.PSU__SATA__REF_CLK_SEL', 'Ref Clk3'), ('CONFIG.PSU__I2C0__PERIPHERAL__IO', 'MIO 74 .. 75')):
        if vals.get(k) != v:
            err(f'{board_dir}: final {k} = {vals.get(k)}, expected {v}')
    return len(pins)


def parse_netlist(path):
    r = ET.parse(path).getroot()
    pin2net = {}
    nets = {}
    for n in r.find('nets'):
        name = n.get('name')
        nodes = [(x.get('ref'), x.get('pin')) for x in n.findall('node')]
        nets[name] = nodes
        for ref, pin in nodes:
            pin2net[(ref, pin)] = name
    return pin2net, nets


def parse_som_xdc(path):
    som = {}
    txt = open(path, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'set_property PACKAGE_PIN (\S+)\s+\[get_ports "(som240_\d_[a-d]\d+)"\] ;# Bank\s+(\d+)', txt):
        som[m.group(2)] = (m.group(1), int(m.group(3)))
    for m in re.finditer(r'#Other net\s+PACKAGE_PIN (\S+)\s+- (som240_\d_[a-d]\d+)\s+Bank\s+(\d+)', txt):
        som.setdefault(m.group(2), (m.group(1), int(m.group(3))))
    return som


def som_to_ref(sp):
    # som240_2_d5 -> ('J3', 'D05') for this carrier's KiCad footprint pin names
    m = re.match(r'som240_(\d)_([a-d])(\d+)', sp)
    conn, row, num = m.group(1), m.group(2).upper(), int(m.group(3))
    return conn, f'{row}{num:02d}', f'{row}{num}'


def check_against_sources(c, netlist, som_xdc, som_refs):
    pin2net, nets = parse_netlist(netlist)
    som = parse_som_xdc(som_xdc)
    rows = list(c.SIGNALS) + list(c.XDC_ONLY_SIGNALS) + list(c.FMC)
    seen_som = set()
    for s in rows:
        sp = s['som']
        seen_som.add(sp)
        if sp not in som:
            err(f'{s["name"]}: {sp} not found in SOM XDC')
            continue
        loc, bank = som[sp]
        if loc != s['loc']:
            err(f'{s["name"]}: table LOC {s["loc"]} but SOM XDC says {loc} for {sp}')
        if bank != s['bank']:
            err(f'{s["name"]}: table bank {s["bank"]} but SOM XDC says {bank}')
        conn, p2, p1 = som_to_ref(sp)
        ref = som_refs[conn]
        net = pin2net.get((ref, p2)) or pin2net.get((ref, p1))
        if net is None:
            err(f'{s["name"]}: {ref}.{p2} not in netlist')
            continue
        if net.split('/')[-1] != s['net']:
            err(f'{s["name"]}: table net {s["net"]} but netlist has {net}')
        if 'pos' in s:
            # direct, or through one AC-coupling capacitor
            on_fmc = any(r == 'J1' and pp == s['pos'] for r, pp in nets[net])
            if not on_fmc:
                for r, pp in nets[net]:
                    if r.startswith('C') and r[1:].isdigit():
                        other = [n for (rr, _), n in pin2net.items() if rr == r and n != net]
                        for o in other:
                            if any(r2 == 'J1' and p2_ == s['pos'] for r2, p2_ in nets[o]):
                                on_fmc = True
            if not on_fmc:
                err(f'{s["name"]}: net {net} does not reach FMC J1.{s["pos"]}')
    # coverage: PL/GTH SOM pins with a real carrier connection but not in the table
    for sp, (loc, bank) in sorted(som.items()):
        if bank not in (43, 44, 45, 64, 65, 66, 224) or sp in seen_som:
            continue
        conn, p2, p1 = som_to_ref(sp)
        ref = som_refs[conn]
        net = pin2net.get((ref, p2)) or pin2net.get((ref, p1))
        if net is None:
            continue
        others = [r for r, _ in nets[net] if r != ref]
        if not others or net.split('/')[-1] in ('GND',) or 'VCC' in net or '3V3' in net or '1V2' in net or 'VADJ' in net:
            continue
        warn(f'not in table: {sp} ({loc}, bank {bank}) net {net} -> {", ".join(sorted(set(others)))}')


def check_som_block(c, board_dir, amd_preset):
    # The first len(K26_SOM_PS_PARAMS) PS parameters must equal AMD's preset, in order.
    def params(path):
        s = re.sub(r'<!--.*?-->', '', open(path, encoding='utf-8', errors='replace').read(), flags=re.S)
        m = re.search(r'<ip_preset\s+preset_proc_name="[^"]*mpsoc[^"]*".*?</ip_preset>', s, flags=re.S)
        return re.findall(r'<user_parameter\s+name\s*=\s*"([^"]+)"\s+value\s*=\s*"([^"]*)"', m.group(0))
    amd = params(amd_preset)
    ours = params(os.path.join(board_dir, 'preset.xml'))
    if ours[:len(amd)] != amd:
        for i, (a, o) in enumerate(zip(amd, ours)):
            if a != o:
                err(f'{board_dir}: SOM block differs from AMD at entry {i}: AMD {a}, ours {o}')
                break
        else:
            err(f'{board_dir}: SOM block has {len(ours)} entries, AMD has {len(amd)}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--amd-som-preset', help="AMD k26c preset.xml to compare the SOM PS block against")
    ap.add_argument('--carrier', default='aper_oculus_rev1')
    ap.add_argument('--netlist')
    ap.add_argument('--som-xdc')
    ap.add_argument('--som-refs', default='J17,J3', help='KiCad refs of SOM240_1,SOM240_2')
    args = ap.parse_args()
    c = importlib.import_module(args.carrier)
    for som in c.SOMS:
        d = os.path.join(ROOT, 'board_files', f'{c.BOARD["base_name"]}_{som["suffix"]}', c.BOARD['file_version'])
        n = check_generated(c, d)
        print(f'checked {os.path.relpath(d, ROOT)}: {n} part0 pins')
        if args.amd_som_preset:
            check_som_block(c, d, args.amd_som_preset)
            print(f'checked {os.path.relpath(d, ROOT)}: SOM PS block vs AMD preset')
    if args.netlist and args.som_xdc:
        r1, r2 = args.som_refs.split(',')
        check_against_sources(c, args.netlist, args.som_xdc, {'1': r1, '2': r2})
        print('checked table against netlist and SOM XDC')
    for w in warnings:
        print('WARN ', w)
    for e in errors:
        print('ERROR', e)
    print(f'{len(errors)} errors, {len(warnings)} warnings')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
