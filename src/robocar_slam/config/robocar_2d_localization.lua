-- Cartographer 2D para Robocar en modo PURE-LOCALIZATION.
-- Copia de robocar_2d.lua + pure_localization: carga un .pbstream CONGELADO y localiza
-- el robot casando el laser contra sus submaps (NO crece el mapa). Sustituye a AMCL:
-- publica map->odom (localizacion) y el occupancy_grid_node saca /map de los mismos submaps
-- (por eso el laser encaja con el mapa por construccion). Se usa con SLAM_LOAD_STATE=<pbstream>.

include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false,          -- el EKF publica odom->base_link; carto solo corrige map->odom
  publish_frame_projected_to_2d = true,
  use_odometry = true,                 -- /odometry/filtered como prior
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

TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.min_range = 0.2
TRAJECTORY_BUILDER_2D.max_range = 12.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 3.0
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

TRAJECTORY_BUILDER_2D.submaps.num_range_data = 35
POSE_GRAPH.optimize_every_n_nodes = 35
POSE_GRAPH.constraint_builder.sampling_ratio = 0.2
POSE_GRAPH.constraint_builder.min_score = 0.6
POSE_GRAPH.global_constraint_search_after_n_seconds = 20

-- ── PURE-LOCALIZATION ──
-- Mantiene solo unos pocos submaps recientes (no crece el mapa): localiza contra el
-- .pbstream congelado que se carga con -load_state_filename (SLAM_LOAD_STATE).
TRAJECTORY_BUILDER.pure_localization_trimmer = {
  max_submaps_to_keep = 3,
}
-- Busca su posicion global en el mapa cargado rapido al arrancar (re-localiza si va perdido).
POSE_GRAPH.global_constraint_search_after_n_seconds = 10.0

return options
