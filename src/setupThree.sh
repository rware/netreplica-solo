#!/bin/bash
set -e

NS1="ns1"
NS2="ns2"
NS3="ns3"
NUM_QUEUE=4
BR="netrepBr"

# Enable forwarding
sysctl -w net.ipv4.ip_forward=1

########################
# Downstream namespace #
########################

ip netns add $NS1

ip link add veth1 type veth peer name veth2
ip addr add 172.16.1.2/30 dev veth2
ip link set veth2 up


ip link set veth1 netns $NS1
ip netns exec $NS1 ip addr add 172.16.1.1/30 dev veth1
ip netns exec $NS1 ip link set veth1 up
ip netns exec $NS1 ip route add default via 172.16.1.2

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
ip netns exec $NS1 sh -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
echo finished setting up NS1

#Set up NS3
ip netns add $NS3

ip link add veth7 type veth peer name veth8
ip addr add 172.16.1.4/30 dev veth8
ip link set veth8 up


ip link set veth7 netns $NS3
ip netns exec $NS3 ip addr add 172.16.1.3/30 dev veth7
ip netns exec $NS3 ip link set veth7 up
ip netns exec $NS3 ip route add default via 172.16.1.3
echo finshied seting up NS3
#End NS3 Setup



######################
# Upstream namespace #
######################

ip netns add $NS2

ip link add veth3 type veth peer name veth4
ip link add veth5 type veth peer name veth6

ip addr add 172.16.2.2/30 dev veth4
ip addr add 172.16.3.2/30 dev veth6
ip link set veth4 up
ip link set veth6 up

ip link set veth3 netns $NS2
ip link set veth5 netns $NS2

ip netns exec $NS2 ip addr add 172.16.2.1/30 dev veth3
ip netns exec $NS2 ip addr add 172.16.3.1/30 dev veth5
ip netns exec $NS2 ip link set veth3 up
ip netns exec $NS2 ip link set veth5 up
ip netns exec $NS2 ip route add default via 172.16.3.2

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
ip netns exec $NS2 iptables -t nat -A POSTROUTING -o veth5 -j MASQUERADE
ip netns exec $NS2 sh -c 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'
echo finished setting up NS2
########################
# Routing adjustments  #
########################

# ns1's gateway is ns2's veth3 (172.16.2.1), which sits on the same L2 segment
# via the bridge. `onlink` is required because 172.16.2.1 is in a different /30
# than ns1's own veth1 address. The previous value 172.16.3.1 (ns2's veth5)
# was on a separate, non-bridged subnet — ARP would never resolve it.
ip netns exec $NS1 ip route change default via 172.16.2.1 dev veth1 onlink

ip netns exec $NS3 ip route change default via 172.16.2.1 dev veth7 onlink

ip netns exec $NS2 ip route add 172.16.1.0/30 dev veth3

ip netns exec $NS2 ip route change default via 172.16.3.2 dev veth5

################
# Bridge setup #
################

ip link add $BR type bridge
ip link set dev veth2 master $BR
ip link set dev veth4 master $BR
ip link set dev veth8 master $BR
ip link set dev $BR up

#TODO add NS3's veth and make sure it works

echo
echo "======================================"
echo " netreplica solo setup completed successfully "
echo "======================================"
echo
