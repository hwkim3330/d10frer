#!/usr/bin/env python3
"""
FRER Traffic Generator
Generates test traffic with R-TAG for LAN9662 FRER testing

Frame Format:
DMAC (6) | SMAC (6) | VLAN (4) | R-TAG (6) | EtherType (2) | Payload
"""

import argparse
import time
import struct
import sys
from scapy.all import Ether, Dot1Q, Raw, sendp, get_if_hwaddr


class FRERTrafficGenerator:
    """Generate FRER-compatible traffic with R-TAG"""

    # R-TAG EtherType
    RTAG_ETHERTYPE = 0x893D

    def __init__(self, interface: str, stream_id: int = 1):
        self.interface = interface
        self.stream_id = stream_id
        self.sequence_number = 0
        self.src_mac = get_if_hwaddr(interface)

    def create_rtag(self, seq_num: int, stream_id: int) -> bytes:
        """Create 6-byte R-TAG"""
        # R-TAG format: EtherType (2) + Sequence (2) + Stream ID (2)
        rtag = struct.pack('>HHH',
                          self.RTAG_ETHERTYPE,  # EtherType 0x893D
                          seq_num & 0xFFFF,      # Sequence number
                          stream_id & 0xFFFF)    # Stream ID
        return rtag

    def generate_frame(self, dst_mac: str = "ff:ff:ff:ff:ff:ff",
                      vlan_id: int = 100, payload_size: int = 100) -> Ether:
        """Generate FRER frame with R-TAG"""

        # Base Ethernet + VLAN
        frame = (
            Ether(src=self.src_mac, dst=dst_mac) /
            Dot1Q(vlan=vlan_id, prio=6)  # High priority for TSN
        )

        # Create R-TAG
        rtag = self.create_rtag(self.sequence_number, self.stream_id)

        # Payload
        payload = b'FRER_TEST_' + struct.pack('>I', self.sequence_number)
        payload += b'X' * (payload_size - len(payload))

        # Combine: R-TAG + Payload
        frame = frame / Raw(load=rtag + payload)

        self.sequence_number += 1
        return frame

    def send_traffic(self, count: int = 1000, rate: int = 1000,
                    dst_mac: str = "ff:ff:ff:ff:ff:ff", vlan_id: int = 100):
        """Send FRER traffic"""

        print(f"\n📡 Starting FRER Traffic Generation")
        print(f"   Interface: {self.interface}")
        print(f"   Stream ID: {self.stream_id}")
        print(f"   Count: {count} packets")
        print(f"   Rate: {rate} pps")
        print(f"   Destination: {dst_mac}")
        print(f"   VLAN ID: {vlan_id}")
        print()

        interval = 1.0 / rate  # Time between packets
        start_time = time.time()
        sent_count = 0

        try:
            for i in range(count):
                frame = self.generate_frame(dst_mac=dst_mac, vlan_id=vlan_id)
                sendp(frame, iface=self.interface, verbose=False)
                sent_count += 1

                # Progress indicator
                if (i + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    actual_rate = sent_count / elapsed
                    print(f"   Sent: {sent_count}/{count} | "
                          f"Rate: {actual_rate:.1f} pps | "
                          f"Seq: {self.sequence_number}")

                # Rate limiting
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")

        # Statistics
        elapsed = time.time() - start_time
        actual_rate = sent_count / elapsed

        print(f"\n📊 Traffic Generation Complete")
        print(f"   Sent: {sent_count} packets")
        print(f"   Duration: {elapsed:.2f} seconds")
        print(f"   Actual Rate: {actual_rate:.1f} pps")
        print(f"   Final Sequence: {self.sequence_number - 1}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate FRER test traffic with R-TAG'
    )
    parser.add_argument('--interface', '-i', required=True,
                       help='Network interface (e.g., enp11s0)')
    parser.add_argument('--stream-id', '-s', type=int, default=1,
                       help='FRER Stream ID (default: 1)')
    parser.add_argument('--count', '-c', type=int, default=1000,
                       help='Number of packets (default: 1000)')
    parser.add_argument('--rate', '-r', type=int, default=1000,
                       help='Packets per second (default: 1000)')
    parser.add_argument('--dst-mac', '-d', default='ff:ff:ff:ff:ff:ff',
                       help='Destination MAC (default: broadcast)')
    parser.add_argument('--vlan', '-v', type=int, default=100,
                       help='VLAN ID (default: 100)')

    args = parser.parse_args()

    # Check for root privileges
    if sys.platform.startswith('linux'):
        import os
        if os.geteuid() != 0:
            print("❌ This script requires root privileges (use sudo)")
            sys.exit(1)

    print("=" * 60)
    print("  FRER Traffic Generator")
    print("  IEEE 802.1CB R-TAG Frame Generation")
    print("=" * 60)

    generator = FRERTrafficGenerator(
        interface=args.interface,
        stream_id=args.stream_id
    )

    generator.send_traffic(
        count=args.count,
        rate=args.rate,
        dst_mac=args.dst_mac,
        vlan_id=args.vlan
    )


if __name__ == "__main__":
    main()
