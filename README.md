# ApotheoTech Vivado Board Files

Vivado board files for ApotheoTech Kria carriers. Select the board when you create a project and Vivado sets up the part, the whole processing system (including the K26 SOM's 4 GB DDR4), and drag-and-drop board interfaces for the carrier peripherals.

| Board (vendor `apotheotech.com`) | SOM | Part | Carrier PCB |
|---|---|---|---|
| `aper_oculus_k26c` | Kria K26C | `xck26-sfvc784-2LV-c` | Aper-Oculus, APT-KRIA-FMC Rev 1.00 |
| `aper_oculus_k26i` | Kria K26I | `xck26-sfvc784-2LVI-i` | Aper-Oculus, APT-KRIA-FMC Rev 1.00 |

Both boards are self-contained. They do not need AMD's K26 SOM board files from the XHub store.

## Install

**Option 1 (recommended): point Vivado at this repo.** Run this in the Vivado Tcl console before creating or opening a project:

```tcl
set_param board.repoPaths [list "/path/to/apotheotech-vivado-boards/board_files"]
```

To make it permanent, copy `utility/Vivado_init.tcl` into your Vivado user scripts folder (`~/.Xilinx/Vivado/` on Linux, `%APPDATA%\Xilinx\Vivado\` on Windows), edit the path, and restart Vivado.

**Option 2: copy into the Vivado install.** Copy the folders under `board_files/` into `<Vivado install>/data/boards/board_files/`.

## Use

1. **Create Project → Default Part → Boards**, filter on "Aper-Oculus", and pick the K26C or K26I board.
2. In a block design, add **Zynq UltraScale+ MPSoC** and click **Run Block Automation** with "Apply Board Preset" ticked. That configures:

   | PS peripheral | Where |
   |---|---|
   | DDR4, 4 GB, 64-bit, DDR4-2400 | SOM (AMD's K26 settings) |
   | QSPI boot flash, 16 GB eMMC | SOM |
   | UART1 console | MIO 36-37 → FT4232H, micro-USB J8 |
   | I2C0 | MIO 74-75 → TCA9548A mux at 0x76 (clocks, EEPROM, cameras, FMC, VADJ) |
   | microSD (SD 3.0) | MIO 39-51 |
   | USB 2.0 + USB 3.0 | MIO 52-63 + GTR2 |
   | Mini DisplayPort, 2 lanes | GTR1/GTR0, AUX on MIO 27-30 |
   | SATA | GTR3, 125 MHz on GTR REFCLK3 |
   | GPIO, PMU, watchdog | MIO 12, 26, 31, 35, 44 |

3. Open the **Board** tab and drag interfaces onto the canvas (or onto an IP):

   | Interface | Connects to | What it is |
   |---|---|---|
   | `sys_clk_200mhz` | Clocking Wizard | 200 MHz LVDS oscillator on bank 66 |
   | `gth_refclk0` | Utility Buffer (IBUFDSGTE) | Si570 into GTH MGTREFCLK0 (300 MHz at power-up) |
   | `cam0_mipi_4lane` / `cam0_mipi_2lane` | MIPI CSI-2 RX Subsystem | Camera 0, J13 |
   | `cam1_mipi_4lane` / `cam1_mipi_2lane` | MIPI CSI-2 RX Subsystem | Camera 1, J14 |
   | `cam_ctrl_4bits` | AXI GPIO | Camera resets and GPIO1 |
   | `slvs_ec_iic` | AXI IIC | FRAMOS SLVS-EC sensor I2C |
   | `slvs_ec_ctrl` | AXI GPIO (15-bit tri-state) | SLVS-EC sensor control, sync and triggers |
   | `imu_spi`, `imu_int_2bits` | AXI Quad SPI, AXI GPIO | ICM-42688-P IMU |
   | `baro_spi` | AXI Quad SPI | MS5611 barometer |
   | `board_ctrl_3bits` | AXI GPIO | DP power enable, fan (active low), barometer mode |
   | `board_status_5bits` | AXI GPIO with interrupt | FMC present, DP power fault, power-monitor alerts |
   | `fmc` connector | FMC daughter-card board files | LA00-LA33, CLK0/1, GBTCLK0, DP0-DP3 |

   The MIPI presets set 4 or 2 lanes, RAW10, 912 Mb/s and the bank 66 pin locations, and turn off the subsystem's built-in IIC because camera I2C runs on PS I2C0. Change the line rate and pixel format to suit your sensor.

4. For RTL-only designs, or for signals that are not a board interface (SLVS-EC GTH lanes, sensor MCLK, FMC GTH lanes), use `xdc/Aper-Oculus-Master.xdc`. Port names there match the board-file pin names.

Full pin tables, the I2C mux map and the GTH channel map are in [`docs/PINOUT.md`](docs/PINOUT.md).

## Things to know about the hardware

- **VADJ (banks 43, 64, 65) defaults to 1.8 V and must stay at 1.8 V when the SLVS-EC connector is used.** All VADJ pins are LVCMOS18 in these files.
- **Fan control is active low.** Leaving `fan_pwm_n` low or unused runs the fan at full speed; driving it high turns the fan off.
- **FMC LA30, LA32 and LA33 are single-ended only** (HD bank 43, and LA32/LA33 are not on P/N pairs).
- **The Si570 GTH reference clock starts at 300 MHz.** Reprogram it over PS I2C0, mux channel 2, before using it at another rate.
- **The 200 MHz clock shares a bank 66 nibble with camera 1 lanes 2 and 3.** If you use camera 1 in 4-lane mode with the 200 MHz clock, run placement early.

`docs/PINOUT.md` has the rest of the notes.

## FMC daughter cards

The board declares FMC J1 as an `fmc_hpc` connector, indexed by VITA 57.1 position, so FMC card board files (for example AMD's XM105) can be attached through the board's **Connections** setting in the board selection page. Only the pins that reach the FPGA are listed: LA00-LA33, CLK0_M2C, CLK1_M2C, GBTCLK0_M2C, DP0/DP1 transmit and receive, and DP2/DP3 transmit. FMC I2C goes to PS I2C0 (mux channel 6), not to the PL.

## Smoke test

`tests/smoke_test.tcl` builds a block design that uses the PS preset and every board interface, validates it, and prints a PASS/FAIL line per interface. Add `synth` or `impl` to go further:

```sh
vivado -mode batch -source tests/smoke_test.tcl -tclargs /path/to/apotheotech-vivado-boards k26c
vivado -mode batch -source tests/smoke_test.tcl -tclargs /path/to/apotheotech-vivado-boards k26c impl
```

## Editing and adding boards

Everything under `board_files/`, `xdc/` and `docs/PINOUT.md` is generated. Do not hand-edit it.

```sh
python3 tools/gen_board_files.py                 # regenerate from tools/aper_oculus_rev1.py
python3 tools/check_board_files.py \
    --netlist APT-KRIA-FMC.xml --som-xdc Kria_K26_SOM_Rev1.xdc \
    --amd-som-preset XilinxBoardStore/boards/Xilinx/k26c/1.4/preset.xml   # cross-check against KiCad, SOM XDC, AMD preset
```

- `tools/aper_oculus_rev1.py` holds the carrier: signal table, interfaces, FMC map, carrier PS settings, notes.
- `tools/k26_som_ps_preset.py` holds AMD's K26 SOM PS settings (DDR4 and the rest), copied verbatim.
- `images/` holds the source board picture. `BOARD['image']` in the carrier module points at it; the generator converts it to an RGB JPEG (Vivado's board files all ship JPEG), resizes it to 1280 px wide, and copies it into every board directory. Needs Pillow (`pip install pillow`).
- For a new carrier or FMC card, copy the carrier module, give it a new `base_name`, edit the tables, then run `gen_board_files.py --carrier <module>` and `check_board_files.py --carrier <module> --netlist <its netlist>`.
- The checker verifies every row against the netlist and the SOM XDC and lists any wired PL/GTH pins that are missing from the table.
- Bump `file_version` in the carrier module when you release a change, so Vivado treats it as a new board revision.

## License

Apache License 2.0, see `LICENSE`. The K26 SOM PS configuration is AMD's (Apache 2.0); see `NOTICE`.
