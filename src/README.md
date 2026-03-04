# Docker for netreplica Solo Version

This project builds a privileged Ubuntu 22.04 container that creates two Linux network namespaces connected through a bridge. It is designed for controlled networking experiments using `ip netns`, `veth`, `tc`, and `iptables`.

---`

## Project Structure

- `Dockerfile` – Builds the container image  
- `setup.sh` – Creates namespaces, veth pairs, routing, NAT, and bridge  
- `cleanup.sh` – Removes namespaces, bridge, veth interfaces, and flushes NAT rules  

---

## 1. Create Docker Network

The subnet must **not** be `172.16.0.0/16`.

```bash
docker network create --subnet 10.10.0.0/16 docBr
```

---

## 2. Build Image

```bash
docker build -t netreplica-solo .
```

---

## 3. Run Container

```bash
docker rm -f solo 2>/dev/null

docker run -it \
  --name solo \
  --network docBr \
  --privileged \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_ADMIN \
  --sysctl net.ipv4.ip_forward=1 \
  netreplica-solo
```

---

## 4. Setup Networking

Inside the container:

```bash
/setup.sh
```

This creates:

- Namespace `ns1` (downstream)  
- Namespace `ns2` (upstream)  
- Bridge `netrepBr`  
- veth pairs between namespaces and root  
- Routing configuration  
- NAT rules  

Verify setup:

```bash
ip netns list
ip link show
```

---

## 6. Cleanup

Inside the container:

```bash
/cleanup.sh
```

This removes:

- All namespaces  
- Bridge  
- veth interfaces  
- NAT rules  

---

## Requirements

- Docker installed  
- Container must run with `--privileged`  
- Uses `iproute2`, `iptables`, and `tc`  