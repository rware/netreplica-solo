# NETREPLICA: A Programmable Substrate for Last-Mile Data Generation

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/paper-arXiv%3A2507.13476-b31b1b.svg)](https://arxiv.org/pdf/2507.13476)

**NETREPLICA** is a programmable substrate for generating realistic, reusable, and systematically varied network data for last-mile access networks. It addresses the critical need for representative datasets that capture the bursty and intermittent congestion patterns that dominate Internet application performance.

## Overview

Last-mile access networks (fiber, cable, DSL, LTE/5G, Wi-Fi) are often the dominant bottlenecks for Internet applications, creating demand for data-generation approaches that are both realistic and reusable. NETREPLICA provides a **thin-waist abstraction** that decouples static bottleneck attributes (capacity, latency, buffer size, shaping, AQM policies) from dynamic attributes derived from passive traces, enabling researchers to generate diverse, reproducible network conditions.

### Why NETREPLICA?

- **For ML Research**: Training datasets must capture the full range of last-mile network dynamics; otherwise, models fail when deployed in production
- **For Systems Research**: New congestion control and adaptive bitrate algorithms must be evaluated under conditions that mirror real user experiences
- **For Reproducibility**: Prior results are only meaningful if researchers can recreate the same underlying network conditions
- **For Benchmarking**: Standardized coverage of last-mile scenarios enables fair and trustworthy comparison of systems and AI-driven approaches

## Key Features

NETREPLICA achieves five critical properties for last-mile data generation:

### 🎯 **Fidelity**
Preserves authentic closed-loop interactions across congestion control, queue management, and application adaptation, capturing real network behaviors with high accuracy.

### 🎛️ **Controllability**
Exposes independent knobs for both static link attributes (capacity, latency, buffer size, shaping, AQM policies) and dynamic cross-traffic variability (intensity, burstiness, heterogeneity).

### 🌐 **Diversity**
Spans heterogeneous access technologies, operating regimes, and traffic patterns, enabling exploration of conditions absent from existing datasets or testbeds.

### 🧩 **Composability**
Supports modular construction of complex scenarios that combine multiple bottlenecks and traffic mixes, allowing researchers to build abstract last-mile topologies.

### 🔄 **Replicability**
Yields consistent outcomes under repeated runs, providing reproducible experimental conditions necessary for systematic domain adaptation in ML models.

## Architecture

NETREPLICA's design centers on a thin-waist abstraction that:

1. **Decouples Static and Dynamic Attributes**: Separates static bottleneck attributes (capacity, base latency, buffer size, shaping, AQM policies) from dynamic attributes derived from passive traces.

2. **Cross-Traffic Profiles (CTPs)**: Transforms passive production traces into reusable, parameterizable building blocks that preserve temporal burst structure while supporting trimming, scaling, and recombination.

3. **Programmable Interfaces**: Enables researchers to express diverse data-generation intents, represent last-mile networks as abstract topologies, and map specifications onto physical/virtual network infrastructures.

**Note**: This all-in-one implementation fully supports all NETREPLICA features using `tc` (traffic control) for shaping, AQM, latency, and buffer management. Parallel experiment execution is currently in development.

```
┌─────────────────────────────────────────────────────────┐
│         Programmable Data-Generation Interfaces          │
├─────────────────────────────────────────────────────────┤
│  Abstract Topology (one or more bottleneck links)       │
├─────────────────────────────────────────────────────────┤
│  Static Attributes  │  Dynamic Attributes (CTPs)        │
│  • Capacity         │  • Intensity                       │
│  • Base Latency     │  • Burstiness                      │
│  • Buffer Size      │  • Heterogeneity                │
│  • Shaping          │                                    │
│  • AQM Policies     │                                    │
├─────────────────────────────────────────────────────────┤
│  Physical/Virtual Network Infrastructure                 │
│  (LibreQoS, tc, Mahimahi, Docker, etc.)                  │
└─────────────────────────────────────────────────────────┘
```

> **⚠️ Important: All-in-One Implementation**
> 
> This repository provides an **all-in-one** implementation of NETREPLICA that differs from the distributed setup described in the paper. Instead of using three separate physical servers, this implementation uses:
> - **Namespace `ns1`** (or `downstream`) as the downstream server
> - **Namespace `ns2`** (or `upstream`) as the upstream server  
> - **Main namespace** (host) as the middle server/bottleneck
> 
> **Current Status:**
> - ✅ **Fully Supported**: All features and capabilities mentioned in the paper are supported in this all-in-one implementation using `tc` commands (traffic shaping, AQM, base latency, buffer size, CTP replay, etc.)
> - 🚧 **In Progress**: Parallel experiment execution (elastic scaling)
> 
> This single-machine approach enables researchers to run NETREPLICA experiments on a single host without requiring multiple physical servers, while maintaining the same programmable abstractions and capabilities.

## Cross-Traffic Profiles (CTPs)

CTPs are the core innovation that transforms raw packet traces into reusable building blocks:

- **Preserve Temporal Structure**: Maintains burst timing and patterns from original traces
- **Support Parameterization**: Enables trimming, scaling, and recombination of traffic patterns
- **Enable Non-Reactive Replay**: Replays cross traffic alongside reactive application workloads
- **Facilitate Controlled Exploration**: Allows systematic variation across intensity, burstiness, and heterogeneity

CTPs enable researchers to:
- Generate realistic yet tunable network conditions
- Explore regimes not present in existing datasets
- Construct heterogeneous scenarios from simpler elements
- Achieve reproducible outcomes across experimental runs

## Installation

### Requirements

- Linux system (tested on kernel 6.8+)
- `iproute2` (for network namespaces and routing)
- `tc` (traffic control, for shaping and AQM)
- `iptables` (for NAT and forwarding)
- Root privileges (for network namespace setup)

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/your-org/netreplica-solo.git
cd netreplica-solo
```

2. Set up the local namespace environment:
```bash
cd src
sudo ./setup.sh
```

This creates two network namespaces (`upstream`/`ns2` and `downstream`/`ns1`) connected through virtual interfaces with traffic shaping applied. The main namespace acts as the middle server/bottleneck, creating an all-in-one setup on a single machine.

3. Run cleanup when done:
```bash
sudo ./cleanup.sh
```

For detailed setup instructions, see [src/README.md](src/README.md).

## Usage

### Supported Applications

NETREPLICA supports various applications for testing and data generation:

- **Puffer** video streaming
- **M-Lab Speedtest** (local and default)
- **Ookla Speedtest**
- **Iperf3**
- **Ping**
- And more...

See [examples/README.md](examples/README.md) for application-specific examples.

### Supported Functionalities

- **Traffic Shaping**: Control bandwidth capacity
- **Base Latency**: Add configurable delay
- **Active Queue Management (AQM)**: Apply various queue management policies
- **Cross Traffic**: Replay CTPs alongside application traffic
- **End Hosts**: Support for Docker containers and GRE tunneling

### Example Workflow

1. **Configure Static Attributes**: Set capacity, latency, buffer size, and AQM policies
2. **Select CTPs**: Choose or create Cross-Traffic Profiles for dynamic variability
3. **Compose Scenario**: Combine multiple bottlenecks and traffic mixes
4. **Generate Data**: Run applications under specified conditions
5. **Analyze Results**: Collect metrics for ML training or systems evaluation

## Repository Structure

```
netreplica-solo/
├── src/              # Core setup and infrastructure code
│   ├── setup.sh      # Network namespace setup script
│   └── README.md     # Detailed setup instructions
├── examples/         # Example pipelines and applications
│   └── README.md     # Application-specific examples
├── traces/           # Cross-Traffic Profiles (CTPs)
│   └── README.md     # CTP documentation
├── LICENSE           # Apache 2.0 License
└── README.md         # This file
```

## Results & Validation

NETREPLICA has been validated through extensive empirical evaluation:

- **Fidelity**: Faithfully reproduces both static and dynamic network attributes
- **Diversity**: Broadens coverage relative to crowdsourced datasets
- **Composability**: Successfully combines multiple abstractions into complex scenarios
- **Replicability**: Achieves consistent outcomes across repeated runs (validated using Dynamic Time Warping)

In a case study on adaptive bitrate streaming, models trained with NETREPLICA-generated traces reduced transmission-time prediction error by **up to 47%** in challenging slow-path domains (≥400ms RTT, ≤6Mbps throughput) compared to models trained solely on production traces.

## Citation

If you use NETREPLICA in your research, please cite:

```bibtex
@article{daneshamooz2025netreplica,
  title={NETREPLICA: Toward a Programmable Substrate for Last-Mile Data Generation},
  author={Daneshamooz, Jaber and Guthula, Satyandra and Nguyen, Jessica and Chen, William and Chandrasekaran, Sanjay and Gupta, Ankit and Gupta, Arpit and Willinger, Walter},
  journal={arXiv preprint arXiv:2507.13476},
  year={2025}
}
```

**Paper**: [arXiv:2507.13476](https://arxiv.org/pdf/2507.13476)

## Contributing

We welcome contributions! Please feel free to submit issues, fork the repository, and create pull requests.


**Note**: NETREPLICA represents a first step toward a fully programmable data-generation substrate for networking. For questions, issues, or collaboration inquiries, please open an issue on GitHub.

