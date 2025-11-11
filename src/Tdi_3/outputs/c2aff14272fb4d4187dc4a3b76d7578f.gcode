;FLAVOR:Marlin
;TIME:6666
;Filament used: 0m
;Layer height: 0.1
;MINX:2.14748e+06
;MINY:2.14748e+06
;MINZ:2.14748e+06
;MAXX:-2.14748e+06
;MAXY:-2.14748e+06
;MAXZ:-2.14748e+06
;TARGET_MACHINE.NAME:Unknown

;Generated with Cura_SteamEngine 5.10.1
M104 S215
M105
M109 S215
G28 ;Home
G1 Z15.0 F6000 ;Move the platform down 15mm
;Prime the extruder
G92 E0
G1 F200 E3
G92 E0
M82 ;absolute extrusion mode
G92 E0
G92 E0
G1 F1500 E-6.5
;LAYER_COUNT:0
M107
M104 S0
M140 S0
;Retract the filament
G92 E1
G1 E-1 F300
G28 X0 Y0
M84
M82 ;absolute extrusion mode
M104 S0
;End of Gcode
