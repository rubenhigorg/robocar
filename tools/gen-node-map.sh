#!/bin/bash
# Genera un snapshot del grafo ROS2 (nodos + qué publican/consumen) para
# refrescar docs/tfm/nodos-ros2.html cuando cambien los nodos o los topics.
#
# Uso (con el stack en marcha):
#   bash tools/gen-node-map.sh                 # imprime por pantalla
#   bash tools/gen-node-map.sh > /tmp/graph.md # a fichero
#
# Introspecciona el grafo VIVO via `ros2 node info`, así que hay que tener los
# nodos corriendo (p.ej. panel + ekf + slam + teleop).

source /opt/ros/humble/setup.bash 2>/dev/null || true
source "$HOME/robocar/src/install/setup.bash" 2>/dev/null || true
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"

# Ruido a filtrar (infra ROS, no aporta al mapa)
NOISE='parameter_events|/rosout|describe_parameters|get_parameter|list_parameters|set_parameters|get_type_description'
# Nodos internos a omitir
SKIP='transform_listener_impl|/_ros2cli|rosapi'

echo "# Snapshot del grafo ROS2 — generado por tools/gen-node-map.sh"
echo
echo "> Volcado automático de \`ros2 node info\` del sistema en marcha ($(date -u '+%Y-%m-%d %H:%MZ')). "
echo "> Úsalo para verificar/actualizar el mapa curado \`docs/tfm/nodos-ros2.html\`."
echo

nodes=$(ros2 node list 2>/dev/null | sort -u | grep -vE "$SKIP")
[ -z "$nodes" ] && { echo "_(sin nodos: ¿está el stack en marcha?)_"; exit 0; }

while IFS= read -r n; do
  [ -z "$n" ] && continue
  info=$(ros2 node info "$n" 2>/dev/null)
  subs=$(printf '%s\n' "$info" | awk '/Subscribers:/{f=1;next} /Publishers:/{f=0} f' | sed 's/^ *//' | grep -vE "$NOISE")
  pubs=$(printf '%s\n' "$info" | awk '/Publishers:/{f=1;next} /Service Servers:/{f=0} f' | sed 's/^ *//' | grep -vE "$NOISE")
  echo "## \`$n\`"
  echo
  echo "**Consume ◀**"
  if [ -n "$subs" ]; then printf '%s\n' "$subs" | sed 's/^/- /'; else echo "- —"; fi
  echo
  echo "**Publica ▶**"
  if [ -n "$pubs" ]; then printf '%s\n' "$pubs" | sed 's/^/- /'; else echo "- —"; fi
  echo
done <<< "$nodes"
