# Kontron D10 (LAN9668) FRER Bidirectional Configuration Guide
# 콘트론 D10 (LAN9668) FRER 양방향 설정 가이드

**IEEE 802.1CB Frame Replication and Elimination for Reliability (FRER) implementation on Kontron D10 i-STAX platform with Microchip LAN9668 TSN switch**

## 📋 Overview

This repository provides a comprehensive guide for configuring bidirectional FRER (Frame Replication and Elimination for Reliability) on the **Kontron D10 i-STAX** platform, which is based on the **Microchip LAN9668** 8-port Gigabit Ethernet managed TSN switch.

### Platform Information
- **Hardware**: Kontron D10 i-STAX
- **Switch IC**: Microchip LAN9668 (8-port Gigabit Ethernet)
- **TSN Features**: IEEE 802.1AS, 802.1Qav, 802.1Qbv, 802.1CB
- **Management**: NETCONF/YANG, Web UI, CLI

### Key Features
- ✅ **Bidirectional FRER**: Both directions protected with redundancy
- 🔄 **Dual Path Redundancy**: Automatic failover for critical traffic
- 📊 **Performance Testing**: Latency, throughput, and reliability metrics
- 🛠️ **Complete Configuration**: Step-by-step setup instructions
- 📈 **Visualization Tools**: Real-time monitoring and analysis

## 🏗️ Network Topology

```
┌─────────────────────────────────────────────────────────┐
│        Kontron D10 i-STAX FRER Test Environment          │
│              (LAN9668 8-Port TSN Switch)                 │
└─────────────────────────────────────────────────────────┘

         Device A                Kontron D10            Device B
      (Generator)                LAN9668 i-STAX       (Analyzer)
           │                                              │
           │                Port 4   Port 4              │
           ├──────────────┐        ┌────────────────────┤
           │              │        │                    │
           │         ┌────┴────────┴────┐              │
           │         │                  │              │
           │    P4   │   LAN9668 TSN    │  P4          │
           └────────▶│     Switch       │◀─────────────┘
                     │   (8 ports)      │
                ┌────┤  Port 1   Port 2 ├────┐
                │    └──────┬───┬────────┘    │
                │           │   │             │
         Path A │           └───┘             │ Path B
                │       Direct Link           │
                │      (Redundancy)           │
                └─────────────────────────────┘

Traffic Flow:
→ Device A sends to Port 4 (Left)
→ LAN9668 replicates to Port 1 & Port 2
→ Ports 1-2 connected to each other (loopback)
→ Traffic arrives back at Port 4 (Right)
→ Device B receives on Port 4
```

### Port Configuration
| Port | Function | Description |
|------|----------|-------------|
| **Port 1** | Path A | Primary redundant path |
| **Port 2** | Path B | Secondary redundant path |
| **Port 4 (Left)** | Input | Traffic ingress from Device A |
| **Port 4 (Right)** | Output | Traffic egress to Device B |

## 🚀 Quick Start

### 1. Hardware Requirements
- **Kontron D10 i-STAX** (LAN9668-based TSN switch)
- **2x Network Devices** (Traffic generator/analyzer)
- **3x Ethernet Cables**:
  - 1x Device A ↔ Port 4 (Left)
  - 1x Port 1 ↔ Port 2 (Direct connection)
  - 1x Port 4 (Right) ↔ Device B
- **USB or Ethernet Management** connection

### 2. Software Requirements
```bash
# Python dependencies
pip3 install --break-system-packages scapy pyserial netifaces
pip3 install --break-system-packages pandas matplotlib plotly

# Management access to D10
# - Web UI: http://<D10_IP>
# - CLI: ssh admin@<D10_IP>
# - NETCONF: port 830
```

### 3. Basic Setup
```bash
# Clone repository
git clone https://github.com/hwkim3330/d10frer.git
cd d10frer

# Configure D10 for FRER
# (via Web UI or scripts below)
python3 scripts/configure_d10_frer.py --ip <D10_IP>

# Verify FRER status
python3 scripts/check_frer_status.py --ip <D10_IP>
```

## 📖 Documentation

### Configuration Guides
1. **[Hardware Setup Guide](docs/01_hardware_setup.md)** - Physical connections and cabling for D10
2. **[D10 i-STAX Configuration](docs/02_d10_config.md)** - LAN9668 FRER settings via Web UI/CLI
3. **[Stream Identification](docs/03_stream_identification.md)** - Configuring stream matching rules
4. **[R-TAG Format](docs/04_rtag_format.md)** - Understanding IEEE 802.1CB R-TAG structure
5. **[Testing & Validation](docs/05_testing.md)** - Performance testing procedures
6. **[Troubleshooting](docs/06_troubleshooting.md)** - Common issues and solutions

### Reference Documents
- [AN1185: SW Configuration Guide TSN](docs/references/AN1185_summary.md) - Microchip official guide
- [IEEE 802.1CB-2017 Standard](docs/references/ieee_8021cb.md) - FRER specification
- [LAN9668 Datasheet](docs/references/lan9668_datasheet.md) - Hardware capabilities
- [Kontron D10 Manual](docs/references/kontron_d10.md) - Platform documentation

## 🔧 FRER Configuration Overview

### Stream Identification & Replication

**Direction A → B (Device A to Device B):**
```yaml
Stream ID: 0x0001
Input Port: Port 4 (Left)
Output Ports:
  - Port 1 (Path A)
  - Port 2 (Path B)
R-TAG Sequence: Enabled
```

**Direction B → A (Device B to Device A):**
```yaml
Stream ID: 0x0002
Input Port: Port 4 (Right)
Output Ports:
  - Port 1 (Path A)
  - Port 2 (Path B)
R-TAG Sequence: Enabled
```

### Frame Elimination

Both paths (Port 1 and Port 2) are connected directly. The receiving side:
1. Receives duplicate frames on Port 1 and Port 2
2. Checks R-TAG sequence number
3. Accepts first frame, discards duplicates
4. Forwards to destination Port 4

## 📊 Performance Metrics

Expected performance with FRER enabled on LAN9668:

| Metric | Without FRER | With FRER |
|--------|--------------|-----------|
| **Latency** | ~30 µs | ~80 µs |
| **Throughput** | 1 Gbps | 500 Mbps per path |
| **Packet Loss** | Varies | 0% (with redundancy) |
| **Failover Time** | N/A | < 1 ms |
| **Overhead** | 0 bytes | 6 bytes (R-TAG) |

## 🧪 Testing Scripts

### 1. FRER Configuration (via Web UI or CLI)
```bash
# Access D10 Web UI
firefox http://<D10_IP>
# Navigate to: TSN → FRER Configuration

# Or use Python automation script
python3 scripts/configure_d10_frer.py \
  --ip <D10_IP> \
  --user admin \
  --password <password>
```

### 2. Traffic Generation
```bash
# Send test traffic (Device A)
sudo python3 scripts/generate_frer_traffic.py \
  --interface enp11s0 \
  --stream-id 1 \
  --rate 1000  # packets/sec
```

### 3. Traffic Analysis
```bash
# Capture and analyze FRER frames (Device B)
sudo python3 scripts/analyze_frer_traffic.py \
  --interface enp15s0 \
  --stream-id 1
```

### 4. Performance Testing
```bash
# Run comprehensive FRER performance test
sudo python3 scripts/run_frer_performance_test.py \
  --duration 60 \
  --report html
```

## 📈 Visualization & Monitoring

### Real-time Dashboard
```bash
# Start web-based monitoring dashboard
python3 scripts/frer_dashboard.py --d10-ip <D10_IP>
# Access at http://localhost:8080
```

### Performance Graphs
- **Latency Distribution**: Histogram of frame latencies
- **Sequence Number Tracking**: R-TAG sequence progression
- **Duplicate Detection**: Percentage of eliminated duplicates
- **Path Utilization**: Traffic distribution across paths

## 🔍 R-TAG Frame Format

```
┌─────────┬─────────┬─────────┬──────────┬─────────┬─────────┐
│  DMAC   │  SMAC   │  VLAN   │  R-TAG   │ EtherType│ Payload │
│ 6 bytes │ 6 bytes │ 4 bytes │  6 bytes │ 2 bytes  │   ...   │
└─────────┴─────────┴─────────┴──────────┴─────────┴─────────┘

R-TAG Structure (6 bytes):
┌──────────┬─────────────┬────────────────┐
│  EtherType│ Sequence #  │  Stream ID     │
│  0x893D   │  2 bytes    │  2 bytes       │
└──────────┴─────────────┴────────────────┘
```

### Wireshark Dissector
```bash
# Install R-TAG dissector for Wireshark
cp scripts/rtag_dissector.lua ~/.local/lib/wireshark/plugins/
# Restart Wireshark
```

## 🛠️ Configuration via D10 Web UI

### Access Management Interface
```bash
# Default credentials (check D10 documentation)
URL: http://<D10_IP>
User: admin
Password: <your_password>
```

### Navigation Path
1. Login to D10 Web UI
2. Navigate to: **Configuration → TSN → FRER**
3. Configure Stream Identification
4. Enable R-TAG Encoding
5. Configure Sequence Recovery (Elimination)

### CLI Alternative
```bash
# SSH to D10
ssh admin@<D10_IP>

# Enter configuration mode
configure

# Configure FRER (see docs/02_d10_config.md for details)
```

## 📚 Additional Resources

### Kontron D10 i-STAX
- **Product Page**: Kontron D10 i-STAX Documentation
- **LAN9668**: Microchip LAN9668 8-Port Managed Switch
- **Management**: NETCONF/YANG, SNMP, Web UI

### Community & Support
- **GitHub Issues**: [Issues](https://github.com/hwkim3330/d10frer/issues)
- **GitHub Wiki**: [Wiki](https://github.com/hwkim3330/d10frer/wiki)
- **Microchip Forum**: TSN Community Support

## 🎯 Use Cases

1. **Industrial Automation**: Critical control systems requiring zero packet loss
2. **Automotive Ethernet**: In-vehicle networking with path redundancy
3. **Smart Grid**: Power system communication with high reliability
4. **5G Fronthaul**: Low-latency mobile network backhaul
5. **Railway Signaling**: Safety-critical train control systems

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## ✨ Contributors

- **Hardware Testing**: Kontron D10 i-STAX platform validation
- **Software Development**: Python test scripts and automation
- **Documentation**: Configuration guides and reference materials

## 🔗 Links

- **GitHub Repository**: https://github.com/hwkim3330/d10frer
- **GitHub Pages**: https://hwkim3330.github.io/d10frer/
- **Kontron**: https://www.kontron.com/
- **Microchip LAN9668**: https://www.microchip.com/LAN9668
- **IEEE 802.1CB**: https://standards.ieee.org/standard/802_1CB-2017.html

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0 - Initial Release: Kontron D10 FRER Bidirectional Configuration

**Platform**: Kontron D10 i-STAX with Microchip LAN9668 TSN Switch

For questions or contributions, please open an issue or pull request.
