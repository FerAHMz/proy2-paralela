#!/usr/bin/env bash
# Arranca sshd y, si se provee una auth key de Tailscale, levanta la malla VPN
# para que este contenedor reciba una IP 100.x enrutable con los demás nodos.
# La llave SSH compartida ya viene horneada en la imagen (ver Dockerfile), así
# que no hace falta sincronizar llaves a mano.
set -e

# El banner de arranque va a stderr para no ensuciar la salida de comandos
# de un solo tiro (p. ej. `docker run --rm img mpicc --version`).
service ssh start >&2

# --- Tailscale ---
# Se activa solo si se pasa TS_AUTHKEY. TS_HOSTNAME nombra al nodo en la malla
# (node1/node2/node3); por defecto usa el hostname del contenedor.
if [ -n "$TS_AUTHKEY" ]; then
    mkdir -p /var/run/tailscale /var/lib/tailscale
    tailscaled \
        --state=/var/lib/tailscale/tailscaled.state \
        --socket=/var/run/tailscale/tailscaled.sock \
        >/var/log/tailscaled.log 2>&1 &
    # Esperar a que el demonio esté listo antes de autenticar.
    for i in $(seq 1 10); do
        [ -S /var/run/tailscale/tailscaled.sock ] && break
        sleep 1
    done
    if tailscale up --authkey="$TS_AUTHKEY" --hostname="${TS_HOSTNAME:-$(hostname)}" >&2; then
        echo "Tailscale IP: $(tailscale ip -4 2>/dev/null)" >&2
    else
        echo "ADVERTENCIA: 'tailscale up' falló (revisar /var/log/tailscaled.log)" >&2
    fi
fi

exec "$@"
