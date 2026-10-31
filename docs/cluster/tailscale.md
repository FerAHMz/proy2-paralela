# Clúster MPI distribuido con Docker + Tailscale

Forma de correr el ataque distribuido **con Docker** entre las tres Mac aunque
Docker Desktop en macOS no exponga los contenedores en la LAN. Tailscale es una
malla (VPN) que le da a cada contenedor una IP `100.x` enrutable entre máquinas,
incluso en redes/NAT distintos. Ventaja extra: **no hace falta estar en la misma
red física** — los integrantes pueden estar en lugares distintos.

La imagen ya trae todo horneado: Tailscale instalado y una **llave SSH compartida**
para que los contenedores se confíen entre sí sin copiar llaves a mano.

## 1. Auth key de Tailscale (una sola vez, el equipo)

1. Crear cuenta gratis en [tailscale.com](https://tailscale.com) (los tres se unen
   al **mismo** tailnet, con la misma cuenta o invitados a ella).
2. Admin console → **Settings → Keys → Generate auth key**.
   - Marcar **Reusable** (sirve para los tres nodos).
   - Opcional: **Ephemeral** (los nodos se borran solos al apagarse).
3. Copiar la key (`tskey-auth-...`). Una sola sirve para los tres.

## 2. Construir la imagen (los tres)

La llave SSH compartida (`docker/cluster_key`) **no está en git** (es privada).
Fernando H la comparte una sola vez como archivo (WhatsApp/USB); cada integrante
la coloca en `docker/cluster_key` antes de construir. Luego:

```bash
git pull
# colocar docker/cluster_key (el archivo privado que compartió el Maestro)
docker build -t mpi-cluster-image .
```

Si prefieren no compartir el archivo, cada equipo puede generar la suya una vez y
que los tres usen esa misma copia:
`ssh-keygen -t ed25519 -N "" -f docker/cluster_key`.

## 3. Levantar cada nodo

```bash
# Maestro (Fernando H)
./docker/run_node.sh tskey-auth-XXXXXXXX node1
# Felipe
./docker/run_node.sh tskey-auth-XXXXXXXX node2
# Rueda
./docker/run_node.sh tskey-auth-XXXXXXXX node3
```

El script corre el contenedor con `--cap-add=NET_ADMIN --device=/dev/net/tun`
(para que Tailscale cree la interfaz `tailscale0`) y arranca la malla. Al iniciar,
el contenedor imprime su `Tailscale IP: 100.x.y.z`.

> Equivale a:
> ```bash
> docker run -it --cap-add=NET_ADMIN --device=/dev/net/tun \
>   -e TS_AUTHKEY=tskey-auth-XXXX -e TS_HOSTNAME=node1 \
>   --name mpi_node mpi-cluster-image
> ```

## 4. Verificar la malla (desde el Maestro, dentro del contenedor)

```bash
tailscale status          # lista los 3 nodos y sus IP 100.x
ping -c 3 <IP-100.x-de-node2>
ping -c 3 <IP-100.x-de-node3>
```

Si el ping sobre `100.x` responde, MPI va a enrutar bien.

## 5. Ataque distribuido

Armar el hostfile con las IP `100.x` de cada nodo (las da `tailscale status`):

```bash
cat > /root/proy/cluster_hosts <<'EOF'
100.x.x.1 slots=14 max_slots=14
100.x.x.2 slots=14 max_slots=14
100.x.x.3 slots=12 max_slots=12
EOF

cd /root/proy
mpirun --hostfile cluster_hosts \
  --mca btl_tcp_if_include tailscale0 \
  --mca oob_tcp_if_include tailscale0 \
  -np 40 src/bruteforce_texto datos/grupo6/cifrado.bin "pan de banano rico y saludable"
```

`--mca ..._if_include tailscale0` fuerza a OpenMPI a usar solo la interfaz de
Tailscale, evitando que intente enrutar por `docker0` u otras interfaces internas.

## Notas

- La llave `docker/cluster_key` es **desechable**, solo para esta práctica; no
  protege nada real. No se versiona en git (está en `.gitignore`); se comparte
  por canal privado o se regenera con
  `ssh-keygen -t ed25519 -N "" -f docker/cluster_key` (reconstruyendo la imagen
  en las tres máquinas con la misma copia).
- Si el profesor exige **LAN física** (no VPN), usar el método de VM Linux
  puenteada por cable Ethernet (ver el runbook del equipo).
- Texto objetivo del grupo 6: `pan de banano rico y saludable` (llave 50000).
