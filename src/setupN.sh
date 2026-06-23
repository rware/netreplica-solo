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
done

#ip comands to configure the Nth namespace
for ((j=1; j < $1+1; j++))
do
    nameSpace="NS$j"
    veth1=veth$((j*2-1))
    veth2=veth$((j*2))

    #ip comands to configure the Nth namespace
    ip netns add ${!nameSpace}

    ip link add $veth1 type veth peer name $veth2
    ip addr add 172.16.1.$((j*2))/24 dev $veth2
    ip link set $veth2 up


    ip link set $veth1 netns  ${!nameSpace}
    ip netns exec ${!nameSpace} ip addr add 172.16.1.$((j*2-1))/24 dev $veth1
    ip netns exec ${!nameSpace} ip link set $veth1 up
    ip netns exec ${!nameSpace} ip route add default via 172.16.1.$((j*2-1))

    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
done
echo Finished Creating N namespaces named ns1-nsN

#Setting up the upstream namespace NS0
#The bottleneck veth on the bridge is named vethBottleneck
#The veth on NS0 that connects to the bridge is named vethBC
#The veth on NS0 that connects to the internet is named vethInternet
#The veth on NS0 that serves as NS0's local IP is call vethIP
NS0="ns0"
ip netns add $NS0


ip link add vethBC type veth peer name vethBottleneck
ip link add vethIP type veth peer name vethInternet


ip addr add 172.16.2.2/24 dev vethBottleneck
ip addr add 172.16.3.2/24 dev vethInternet
ip link set vethBottleneck up
ip link set vethInternet up


ip link set vethBC netns $NS0
ip link set vethIP netns $NS0


ip netns exec $NS0 ip addr add 172.16.2.1/24 dev vethBC
ip netns exec $NS0 ip addr add 172.16.3.1/24 dev vethIP
ip netns exec $NS0 ip link set vethBC up
ip netns exec $NS0 ip link set vethIP up
ip netns exec $NS0 ip route add default via 172.16.3.2


iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
ip netns exec $NS0 iptables -t nat -A POSTROUTING -o vethIP -j MASQUERADE
echo Finished creating ns0
#End of NS0 setup


#Performing nessacary routing adjustments so that ARP can resolve ns1-N adress's
#This is the reasoning for the adjustments when their are only two namespaces and a bridge

# ns1's gateway is ns0's vethBC (172.16.2.1), which sits on the same L2 segment
# via the bridge. `onlink` is required because 172.16.2.1 is in a different /24
# than ns1's own veth1 address. The previous value 172.16.3.1 (ns2's vethIP)
# was on a separate, non-bridged subnet — ARP would never resolve it.

for ((k=1; k < $1+1; k++))
do
    nameSpace="NS$k"
    veth1=veth$((k*2-1))
    ip netns exec ${!nameSpace} ip route change default via 172.16.2.1 dev $veth1 onlink
done

#Performing nessacary routing adjustments for ns0
ip netns exec $NS0 ip route add 172.16.1.0/24 dev vethBC
ip netns exec $NS0 ip route change default via 172.16.3.2 dev vethIP
echo All routing adjustments performed succusfully
#All nessacary routing adjustments are complete

#Bridge setup
#All setup that does not depend on the value of N
ip link add $BR type bridge
ip link set dev vethBottleneck master $BR

#This is the part that sets the veth2 for ns1-N to be conected to the bridge
for ((l=1; l < $1+1; l++))
do
        veth2=veth$((l*2))
        ip link set dev $veth2 master $BR
done

#Turn the bridge on
ip link set dev $BR up

echo Bridge setup is complete
#End of Bridge Setup

echo
echo "======================================"
echo " Setup N completed successfully "
echo "======================================"
echo
