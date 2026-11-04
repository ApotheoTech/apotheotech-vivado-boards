# Add the ApotheoTech board files to every Vivado session.
#
# 1. Replace the path below with where you cloned or unzipped this repo.
# 2. Save this file as Vivado_init.tcl in your Vivado user scripts folder:
#      Linux:   ~/.Xilinx/Vivado/Vivado_init.tcl
#      Windows: %APPDATA%\Xilinx\Vivado\Vivado_init.tcl
#    (If a Vivado_init.tcl is already there, add the line to it instead.)
# 3. Restart Vivado. The boards show up under vendor "apotheotech.com".
#
# To keep other board repos too, list them all in the same set_param call:
#   set_param board.repoPaths [list "/path/one/board_files" "/path/two/board_files"]

set_param board.repoPaths [list "<extracted path>/apotheotech-vivado-boards/board_files"]
