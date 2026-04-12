#!/bin/bash
set -e

NS1="ns1"
NS2="ns2"
BR="netrepBr"

ip link set $BR down 2>/dev/null || true
ip link delete $BR type bridge 2>/dev/null || true

for i in veth2 veth4 veth6; do
    ip link delete $i 2>/dev/null || true
done

ip netns delete $NS1 2>/dev/null || true
ip netns delete $NS2 2>/dev/null || true

# Remove only the rule setup.sh added to the host nat table.
# Never `iptables -t nat -F` here: if this script is ever run in a context
# that shares the host's iptables (e.g. accidentally run outside the
# container), flushing the whole table wipes Docker's port-forward and
# bridge-MASQUERADE rules and breaks all container networking.
# The $NS2 MASQUERADE rule is torn down automatically with the namespace.
iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true