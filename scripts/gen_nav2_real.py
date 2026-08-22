#!/usr/bin/env python3
# Genera nav2_real.yaml a partir de nav2_bench.yaml aplicando los cambios de la NAVEGACION REAL:
#  - mapa desde map_server (/map) en vez de sim_map_grid; AMCL sobre /map, estatico.
#  - footprint/inflado reales; velocidad conservadora para los primeros arranques.
#  - collision_monitor con el LIDAR real (/scan) en vez del IR simulado.
#  - lifecycle de localizacion incluye map_server.
import sys, os
src = os.path.expanduser('~/robocar/src/robocar_pkg/config/nav2_bench.yaml')
dst = os.path.expanduser('~/robocar/src/robocar_pkg/config/nav2_real.yaml')
s = open(src).read()

def rep(a, b):
    global s
    if a not in s:
        print('AVISO: no encontrado -> ' + repr(a[:40]))
    s = s.replace(a, b)

# footprint e inflado reales (el bench estaba deshinchado a tope para el plano)
rep('robot_radius: 0.08', 'robot_radius: 0.10')
rep('inflation_radius: 0.02', 'inflation_radius: 0.05')
# velocidad conservadora para los primeros arranques reales
rep('desired_linear_vel: 0.450', 'desired_linear_vel: 0.250')
# AMCL: mapa del map_server en /map (estatico), no /map_amcl del banco
rep('map_topic: /map_amcl', 'map_topic: /map')
rep('first_map_only: false', 'first_map_only: true')
# collision_monitor con el LIDAR real (/scan) en vez del IR
rep('''    observation_sources: ["ir"]
    ir:
      type: "range"
      topic: "/ir_range"''', '''    observation_sources: ["scan"]
    scan:
      type: "scan"
      topic: "/scan"''')
# lifecycle de localizacion: arrancar tambien el map_server (antes de amcl)
rep('''    node_names:
      - amcl''', '''    node_names:
      - map_server
      - amcl''')

# bloque map_server (yaml_filename se pasa por CLI en el bringup)
s += '''
# ----------------------------------------------------------------------------
# MAP SERVER — sirve el mapa CARTOGRAFIADO guardado como /map (latched).
# yaml_filename se pasa por CLI en bringupNAVREAL.sh (-p yaml_filename:=...).
# ----------------------------------------------------------------------------
map_server:
  ros__parameters:
    topic_name: /map
    frame_id: map
    yaml_filename: ""
'''
open(dst, 'w').write(s)
print('escrito ' + dst)
