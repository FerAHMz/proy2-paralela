#!/usr/bin/env bash
# Levanta el nodo del clúster MPI con Tailscale.
# Uso: ./docker/run_node.sh <TS_AUTHKEY> <node1|node2|node3>
#   TS_AUTHKEY : auth key de Tailscale (empieza con tskey-auth-...)
#   nombre     : identifica al nodo en la malla (por defecto 'node')
set -e
KEY="$1"; NAME="${2:-node}"
if [ -z "$KEY" ]; then
    echo "Uso: $0 <TS_AUTHKEY> <node1|node2|node3>" >&2
    exit 1
fi
docker rm -f mpi_node 2>/dev/null || true
exec docker run -it --cap-add=NET_ADMIN --device=/dev/net/tun \
    -e TS_AUTHKEY="$KEY" -e TS_HOSTNAME="$NAME" \
    --name mpi_node mpi-cluster-image
