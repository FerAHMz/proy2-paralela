# Parte 2 — Virtualización del entorno con Docker

Para interconectar máquinas con Windows, macOS y Linux sin pelear con las
diferencias de cada sistema, estandarizamos el entorno de compilación y de
comunicación en una imagen de Docker idéntica para todos. El
[`Dockerfile`](../../Dockerfile) está en la raíz del proyecto.

## Qué hace la imagen

Partiendo de `ubuntu:22.04`:

1. **Dependencias base** (`apt-get`): `build-essential`, `openmpi-bin`,
   `libopenmpi-dev`, `openssh-server`. Se agrega `libssl-dev` y utilidades de
   red (`iproute2`, `iputils-ping`, `net-tools`) para el *troubleshooting*.
2. **SSH sin intervención**: `PermitRootLogin yes` en `sshd_config` y
   `StrictHostKeyChecking no` (más `UserKnownHostsFile /dev/null`) en
   `ssh_config`, para que `mpirun` abra sesiones a los workers sin bloqueos ni
   confirmaciones manuales de huellas.
3. **Ejecución como root en OpenMPI**: `OMPI_ALLOW_RUN_AS_ROOT=1` y
   `OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1`, porque OpenMPI prohíbe correr procesos
   como root y en contenedores sin volúmenes el usuario es root.
4. **Compila el proyecto** (`make -C src`) y copia `datos/` (incluye el texto
   cifrado del otro equipo para el ataque).
5. **Entrypoint** ([`docker/entrypoint.sh`](../../docker/entrypoint.sh)):
   arranca `sshd` y genera la llave local del nodo.

### Detalle que hubo que resolver: DES en Ubuntu 22.04

El código incluye `<rpc/des_crypt.h>` y usa `ecb_crypt`/`des_setparity`. Esas
funciones **ya no están en glibc** (se quitaron en la 2.28) y `libtirpc` trae el
header pero tampoco exporta los símbolos (falla el *link*, no la compilación).
La solución fue reutilizar la capa [`src/compat/`](../../src/compat/) que ya
existía para macOS —que implementa `ecb_crypt`/`des_setparity` sobre OpenSSL— y
hacer que el [`Makefile`](../../src/Makefile) la use también en Linux.

## Construcción

```bash
# En la raíz del proyecto
docker build -t mpi-cluster-image .
```

## Tabla de validaciones (sección IV)

| Validar | Esperado | ¿Funcionó? | Qué se tuvo que hacer |
|---|---|---|---|
| `docker run --rm mpi-cluster-image mpicc --version` | gcc (Ubuntu … 11.4.0) | ✅ `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` | Instalar `build-essential` + `openmpi-bin`. |
| `docker run --rm mpi-cluster-image mpirun -np 2 echo "Proceso MPI ejecutado"` | Imprime 2 veces | ✅ se imprime 2 veces | Variables `OMPI_ALLOW_RUN_AS_ROOT*` para correr como root. |
| `docker run -it --rm mpi-cluster-image /bin/bash` | Entra a la terminal | ✅ | `ENTRYPOINT` arranca `sshd` y deja `bash`. |
| `service ssh start` | Arranca sshd | ✅ | `mkdir /var/run/sshd`; lo hace el entrypoint. |
| `ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa` + `cat … >> authorized_keys` | Genera llave local | ✅ | El entrypoint lo automatiza al primer arranque. |
| `ssh localhost echo "Conexion SSH sin contrasena exitosa"` | Imprime el mensaje | ✅ `Conexion SSH sin contrasena exitosa` | `PermitRootLogin yes` + `StrictHostKeyChecking no`. |

Prueba de humo del binario dentro del contenedor (llave conocida `3141592`):

```bash
docker run --rm mpi-cluster-image \
  bash -lc 'cd /root/proy/src && mpirun -np 4 ./bruteforce_texto ../datos/texto_cifrado.bin "paralela"'
# -> Llave = 3141592, recupera el texto plano completo.
```

## Despliegue en red física (sección V)

En cada máquina, lanzar el contenedor compartiendo la red del host (sale del NAT
de Docker para que los demás nodos lo alcancen):

```bash
docker run -it --network host --name mpi_node mpi-cluster-image /bin/bash
```

En Windows (WSL2) y macOS: Docker Desktop ≥ 4.34 y activar **Settings > Resources
> Network > Enable Host Networking**. Abrir el firewall para conexiones entrantes
en la red privada.

### Paso A — Sincronización de llaves SSH inter-nodo

El entrypoint ya generó la llave local de cada nodo. Desde el **Nodo Maestro**,
copiar su pubkey al `authorized_keys` de cada **Worker** (sincronización manual):

```bash
# En el Maestro: mostrar la pubkey
cat ~/.ssh/id_rsa.pub

# En cada Worker: pegarla en authorized_keys
echo "<pubkey del maestro>" >> ~/.ssh/authorized_keys

# Verificar desde el Maestro (IP real del router)
ssh 192.168.1.11 echo "Maestro -> Worker OK"
```

### Paso B — Ejecución del ataque distribuido

Editar [`docker/cluster_hosts`](../../docker/cluster_hosts) con las IPs reales y
los `slots`/`max_slots` de cada máquina, y lanzar desde el Maestro limitando el
tráfico a la subred física del router (cambiar `192.168.1.0/24` según la IP real):

```bash
mpirun --hostfile cluster_hosts \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  --mca oob_tcp_if_include 192.168.1.0/24 \
  -np <TOTAL_SLOTS> \
  /root/proy/src/bruteforce_texto /root/proy/datos/grupo6/cifrado.bin "<frase objetivo>"
```

Los flags `--mca …_tcp_if_include` son **obligatorios**: sin ellos OpenMPI
inspecciona todas las interfaces (incluidas las virtuales `docker0`/VirtualBox),
asume que puede enrutar tráfico por ahí, los paquetes no llegan y el programa se
cuelga indefinidamente sin reportar error.
