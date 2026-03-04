FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    tshark \
    iputils-ping \
    net-tools \
    iperf3 \
    curl \
    wget \
    iproute2 \
    iptables \
    byobu \
    && rm -rf /var/lib/apt/lists/*

COPY setup.sh /setup.sh
COPY cleanup.sh /cleanup.sh

RUN chmod +x /setup.sh /cleanup.sh

ENTRYPOINT ["/bin/bash"]