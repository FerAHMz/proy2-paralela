# Imagen estandarizada del clúster MPI para el ataque de fuerza bruta DES.
# Encapsula el compilador, OpenMPI y el demonio SSH para que el entorno sea
# idéntico en Windows, macOS y Linux (Proyecto 2 Parte 2, sección IV).
FROM ubuntu:22.04

# Evita prompts interactivos de apt (tzdata, etc.) durante el build.
ENV DEBIAN_FRONTEND=noninteractive

# Dependencias base obligatorias + libssl-dev (la capa compat implementa
# ecb_crypt/des_setparity sobre OpenSSL, ya que glibc y libtirpc no los exportan
# en Ubuntu 22.04) y utilidades de red para el troubleshooting (ping, ip, ss).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        openmpi-bin \
        libopenmpi-dev \
        openssh-server \
        libssl-dev \
        iproute2 \
        iputils-ping \
        net-tools \
        nano \
        curl \
        ca-certificates \
        iptables \
    && rm -rf /var/lib/apt/lists/*

# --- Tailscale (malla VPN) ---
# Da a cada contenedor una IP 100.x enrutable entre máquinas aunque estén en
# redes/NAT distintos. Resuelve que Docker Desktop en macOS no exponga el
# contenedor en la LAN. Se activa en runtime con -e TS_AUTHKEY=... (ver entrypoint).
RUN curl -fsSL https://tailscale.com/install.sh | sh

# --- Comunicación SSH sin intervención (sección IV.2) ---
# Permitir login de root y deshabilitar la verificación manual de host keys,
# para que mpirun pueda abrir sesiones SSH a los workers sin bloqueos.
RUN mkdir -p /var/run/sshd /root/.ssh \
    && chmod 700 /root/.ssh \
    && sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && printf '\n# Clúster MPI: sin verificación manual de huellas de host\nHost *\n    StrictHostKeyChecking no\n    UserKnownHostsFile /dev/null\n' >> /etc/ssh/ssh_config

# Llave SSH COMPARTIDA del clúster: horneada en la imagen para que todos los
# contenedores se confíen entre sí sin copiar llaves a mano. Es una llave
# DESECHABLE, solo para esta práctica (no protege nada real).
COPY docker/cluster_key     /root/.ssh/id_ed25519
COPY docker/cluster_key.pub /root/.ssh/id_ed25519.pub
RUN cat /root/.ssh/id_ed25519.pub > /root/.ssh/authorized_keys \
    && chmod 600 /root/.ssh/id_ed25519 /root/.ssh/id_ed25519.pub /root/.ssh/authorized_keys

# --- Ejecución como root en OpenMPI (sección IV) ---
# OpenMPI bloquea correr como root; en contenedores sin volúmenes lo permitimos.
ENV OMPI_ALLOW_RUN_AS_ROOT=1 \
    OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# --- Código del proyecto ---
WORKDIR /root/proy
COPY src/   ./src/
COPY datos/ ./datos/

# Compila bruteforce, bruteforce_texto y cifrar dentro del contenedor.
RUN make -C src

# Hostfile de ejemplo y entrypoint que arranca sshd.
COPY docker/cluster_hosts ./cluster_hosts
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
