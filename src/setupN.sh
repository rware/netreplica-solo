#!/bin/bash

#Configuration and naming
set -e
NUM_QUEUE=4
BR="netrepBr"

# Enable forwarding
sysctl -w net.ipv4.ip_forward=1


#Creates the names of the N downstream or client namespaces
for ((i=1; i < $1+1; i++))
do
    declare "NS$i=ns$i"
    nameSpace="NS$i"
    echo ${!nameSpace}
done

#ip comands to configure the Nth namespace
for ((j=1; j < $1+1; j++))
do
    nameSpace="NS$i"
    veth1=veth$((j*2-1))
    veth2=veth$((j*2))
    echo $veth1
    echo $veth2

    #ip comands to configure the Nth namespace
    ip netns add ${!nameSpace}

    ip link add $veth1 type veth peer name $veth2
    ip addr add 172.16.1.$((j*2))/30 dev $veth2
    ip link set $veth2 up


    ip link set $veth1 netns  ${!nameSpace}
    ip netns exec ${!nameSpace} ip addr add 172.16.1.$((j*2-1))/30 dev veth1
    ip netns exec ${!nameSpace} ip link set $veth1 up
    ip netns exec ${!nameSpace} ip route add default via 172.16.1.$((j*2-1))

    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
done

#Setting up the upstream namespace NS0
#The bottleneck veth on the bridge is named vethBottleneck
#The veth on NS0 that connects to the bridge is named vethBridgeConnector
#The veth on NS0 that connects to the internet is named vethInternet
#The veth on NS0 that serves as NS0's local IP is call vethIP
NS0="ns0"
ip netns add $NS0

#TODO updafe the copypasted code bellow this to actually fit the file
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




#Make sure to remeber to add everything to the bridge
