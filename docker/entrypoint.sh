#!/usr/bin/env bash
# Arranca el demonio SSH y genera la llave local del nodo (Paso A).
# El demonio es necesario para que mpirun lance procesos en este nodo vía SSH;
# la copia de la pubkey del Maestro hacia los workers se hace a mano (ver README).
set -e

# El banner de arranque va a stderr para no ensuciar la salida de comandos
# de un solo tiro (p. ej. `docker run --rm img mpicc --version`).
service ssh start >&2

# Llave propia del nodo: permite 'ssh localhost' (validación de la sección IV)
# y sirve de base para la sincronización inter-nodo del Paso A.
if [ ! -f /root/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa >/dev/null
    cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
fi

exec "$@"
