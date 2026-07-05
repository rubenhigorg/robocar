-- Cartographer 2D para Robocar (Raspberry Pi 4 + RPLidar C1).
-- Decisiones documentadas en el tablero (tarea 8) y en docs/tfm/slam.md.

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "base_link",
  odom_frame = "odom",
  -- Nadie publica odom: Cartographer crea la cadena map->odom->base_link (Nav2 la exige)
  provide_odom_frame = true,
  publish_frame_projected_to_2d = true,
  -- D2 = opcion A: sin odometria de ruedas; el scan-matching hace ese papel.
  -- Futuro plan B: cuando la fusion IMU+encoder (Antonio) de una odometria real,
  -- cambiar a true y publicar odom desde ese nodo.
  use_odometry = false,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true

-- El /imu actual no tiene header valido (hito 0.5); en 2D no es necesario.
TRAJECTORY_BUILDER_2D.use_imu_data = false

-- min_range 0.2: descarta los impactos contra el propio coche (radiador de la
-- RPi a ~10 cm del LIDAR) -> resuelve la oclusion trasera por configuracion.
TRAJECTORY_BUILDER_2D.min_range = 0.2
TRAJECTORY_BUILDER_2D.max_range = 12.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.0

-- Sin odometria, el scan matcher correlativo es imprescindible para robustez.
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

-- ── Tuning para Raspberry Pi 4 (submaps contenidos, optimizacion moderada) ──
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 35
POSE_GRAPH.optimize_every_n_nodes = 35
POSE_GRAPH.constraint_builder.sampling_ratio = 0.2
POSE_GRAPH.constraint_builder.min_score = 0.6
POSE_GRAPH.global_constraint_search_after_n_seconds = 20

return options
