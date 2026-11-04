# ---------------------------------------------------------------------------
# Board-file smoke test for the Aper-Oculus Vivado board files.
#
#   vivado -mode batch -source tests/smoke_test.tcl -tclargs <repo_root> [k26c|k26i] [synth|impl]
#
# Builds a block design that touches every board interface:
#   - Zynq UltraScale+ PS with the board preset (DDR4, QSPI, eMMC, SD, USB3, DP, SATA, UART, I2C)
#   - clk_wiz on sys_clk_200mhz, util_ds_buf on gth_refclk0
#   - MIPI CSI-2 RX on cam0 (4 lane) and cam1 (4 lane)
#   - AXI GPIO / IIC / Quad SPI on every GPIO, I2C and SPI interface
# then validates it. With "synth" or "impl" it also runs that far, which is
# where pin-placement problems (for example the bank 66 nibble sharing noted
# in docs/PINOUT.md) show up.
# ---------------------------------------------------------------------------
set repo  [file normalize [lindex $argv 0]]
set som   [expr {[llength $argv] > 1 ? [lindex $argv 1] : "k26c"}]
set depth [expr {[llength $argv] > 2 ? [lindex $argv 2] : "validate"}]

set_param board.repoPaths [list [file join $repo board_files]]
set bp [lindex [lsort [get_board_parts -quiet "apotheotech.com:aper_oculus_${som}:*"]] end]
if {$bp eq ""} { error "Board apotheotech.com:aper_oculus_${som} not found under $repo/board_files" }
puts "SMOKE: using board part $bp"

set work [file join [pwd] smoke_aper_oculus_${som}]
create_project smoke $work -force -part [get_property PART_NAME [get_board_parts $bp]]
set_property board_part $bp [current_project]
create_bd_design smoke

set results {}
proc step {name script} {
    upvar results results
    if {[catch {uplevel 1 $script} msg]} {
        lappend results [list FAIL $name $msg]
        puts "SMOKE FAIL: $name: $msg"
    } else {
        lappend results [list PASS $name ""]
        puts "SMOKE PASS: $name"
    }
}

# --- PS with board preset -----------------------------------------------------
step "ps preset" {
    create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e ps
    apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e -config {apply_board_preset "1"} [get_bd_cells ps]
    set_property CONFIG.PSU__USE__M_AXI_GP0 1 [get_bd_cells ps]
    # The SOM preset also enables HPM1; clock it so validate stays clean.
    foreach clkpin {maxihpm0_fpd_aclk maxihpm1_fpd_aclk} {
        catch { connect_bd_net [get_bd_pins ps/pl_clk0] [get_bd_pins ps/$clkpin] }
    }
}
step "ps ddr4 settings" {
    set ps [get_bd_cells ps]
    foreach {k want} {PSU__DDRC__MEMORY_TYPE {DDR 4} PSU__DDRC__BUS_WIDTH {64 Bit} PSU__DDRC__SPEED_BIN DDR4_2400R
                      PSU__DDRC__DEVICE_CAPACITY {8192 MBits} PSU__DDRC__DRAM_WIDTH {16 Bits}
                      PSU__UART1__PERIPHERAL__ENABLE 1 PSU__SD1__PERIPHERAL__ENABLE 1 PSU__USB3_0__PERIPHERAL__ENABLE 1
                      PSU__DISPLAYPORT__PERIPHERAL__ENABLE 1 PSU__SATA__PERIPHERAL__ENABLE 1 PSU__I2C0__PERIPHERAL__ENABLE 1} {
        set got [get_property CONFIG.$k $ps]
        if {$got ne $want} { error "$k = '$got', expected '$want'" }
    }
}

# --- clocks -----------------------------------------------------------------
step "sys_clk_200mhz -> clk_wiz" {
    create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz clk_200
    if {[catch {apply_board_connection -board_interface "sys_clk_200mhz" -ip_intf "clk_200/clock_CLK_IN1" -diagram "smoke"}]} {
        # Older/newer Vivado name the clk_wiz board pin differently; fall back to the board rule.
        set_property CONFIG.CLK_IN1_BOARD_INTERFACE {sys_clk_200mhz} [get_bd_cells clk_200]
        apply_bd_automation -rule xilinx.com:bd_rule:board -config {Board_Interface {sys_clk_200mhz} Manual_Source {Auto}} \
            [get_bd_intf_pins clk_200/CLK_IN1_D]
    }
    set_property -dict [list CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {200.000} CONFIG.USE_RESET {false}] [get_bd_cells clk_200]
    if {[get_property CONFIG.PRIM_IN_FREQ [get_bd_cells clk_200]] != 200} { error "clk_wiz input is not 200 MHz" }
}
step "gth_refclk0 -> util_ds_buf" {
    create_bd_cell -type ip -vlnv xilinx.com:ip:util_ds_buf gtclk0
    apply_board_connection -board_interface "gth_refclk0" -ip_intf "gtclk0/CLK_IN_D" -diagram "smoke"
}

# --- MIPI -------------------------------------------------------------------
foreach {cam itf} {cam0 cam0_mipi_4lane cam1 cam1_mipi_4lane} {
    step "$itf -> mipi_csi2_rx_subsystem" {
        create_bd_cell -type ip -vlnv xilinx.com:ip:mipi_csi2_rx_subsystem csi_$cam
        apply_board_connection -board_interface $itf -ip_intf "csi_$cam/mipi_phy_if" -diagram "smoke"
        connect_bd_net [get_bd_pins clk_200/clk_out1] [get_bd_pins csi_$cam/dphy_clk_200M]
        connect_bd_net [get_bd_pins ps/pl_clk0] [get_bd_pins csi_$cam/video_aclk]
    }
}

# --- GPIO / IIC / SPI --------------------------------------------------------
foreach {itf vlnv cell ipif} {
    cam_ctrl_4bits     xilinx.com:ip:axi_gpio     gpio_cam    GPIO
    slvs_ec_ctrl       xilinx.com:ip:axi_gpio     gpio_slvs   GPIO
    imu_int_2bits      xilinx.com:ip:axi_gpio     gpio_imu    GPIO
    board_ctrl_3bits   xilinx.com:ip:axi_gpio     gpio_ctrl   GPIO
    board_status_5bits xilinx.com:ip:axi_gpio     gpio_status GPIO
    slvs_ec_iic        xilinx.com:ip:axi_iic      iic_slvs    IIC
    imu_spi            xilinx.com:ip:axi_quad_spi spi_imu     SPI_0
    baro_spi           xilinx.com:ip:axi_quad_spi spi_baro    SPI_0
} {
    step "$itf -> $cell" {
        create_bd_cell -type ip -vlnv $vlnv $cell
        apply_board_connection -board_interface $itf -ip_intf "$cell/$ipif" -diagram "smoke"
    }
}

# --- AXI + clock/reset automation ---------------------------------------------
step "axi automation" {
    set intc {New AXI Interconnect}
    foreach slave [get_bd_intf_pins -quiet -of_objects [get_bd_cells -filter {VLNV !~ *zynq_ultra_ps_e*}] -filter {MODE == Slave && VLNV =~ *aximm*}] {
        apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
            -config [list Clk_master {/ps/pl_clk0 (100 MHz)} Clk_slave {Auto} Clk_xbar {Auto} \
                          Master {/ps/M_AXI_HPM0_FPD} Slave {Auto} ddr_seg {Auto} intc_ip $intc master_apm {0}] $slave
        set intc {Auto}
    }
    foreach spi {spi_imu spi_baro} {
        catch { connect_bd_net [get_bd_pins ps/pl_clk0] [get_bd_pins $spi/ext_spi_clk] }
    }
}
step "validate_bd_design" {
    regenerate_bd_layout
    validate_bd_design
}

if {$depth ne "validate"} {
    step "generate + wrapper" {
        make_wrapper -files [get_files smoke.bd] -top -import
        generate_target all [get_files smoke.bd]
    }
    step "synth" {
        launch_runs synth_1 -jobs 4
        wait_on_run synth_1
        if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} { error "synth_1 did not finish" }
    }
    if {$depth eq "impl"} {
        step "impl" {
            launch_runs impl_1 -to_step route_design -jobs 4
            wait_on_run impl_1
            if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} { error "impl_1 did not finish" }
        }
    }
}

puts "\n================ SMOKE TEST SUMMARY ($bp) ================"
set fails 0
foreach r $results {
    puts [format "%-5s %s %s" [lindex $r 0] [lindex $r 1] [lindex $r 2]]
    if {[lindex $r 0] eq "FAIL"} { incr fails }
}
puts "=========================================================="
puts "$fails failure(s)"
