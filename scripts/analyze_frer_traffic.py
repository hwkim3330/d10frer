#!/usr/bin/env python3
"""
FRER Traffic Analyzer
Captures and analyzes FRER frames with R-TAG
Detects duplicates, measures latency, and validates sequence numbers
"""

import argparse
import time
import struct
import sys
from collections import defaultdict
from typing import Dict, Set
from scapy.all import sniff, Ether, Dot1Q, Raw


class FRERAnalyzer:
    """Analyze FRER traffic and detect frame replication/elimination"""

    RTAG_ETHERTYPE = 0x893D

    def __init__(self, interface: str, stream_id: int = 1):
        self.interface = interface
        self.stream_id = stream_id

        # Statistics
        self.total_frames = 0
        self.rtag_frames = 0
        self.duplicate_frames = 0
        self.sequence_gaps = 0

        # Tracking
        self.seen_sequences: Set[int] = set()
        self.stream_stats: Dict[int, Dict] = defaultdict(lambda: {
            'count': 0,
            'sequences': set(),
            'duplicates': 0,
            'last_seq': -1
        })

        self.start_time = time.time()

    def extract_rtag(self, frame: Ether) -> tuple:
        """Extract R-TAG from frame"""
        try:
            if not frame.haslayer(Dot1Q):
                return None, None, None

            # Get payload after VLAN tag
            payload = bytes(frame[Dot1Q].payload)

            if len(payload) < 6:
                return None, None, None

            # Check for R-TAG EtherType
            ethertype = struct.unpack('>H', payload[0:2])[0]

            if ethertype != self.RTAG_ETHERTYPE:
                return None, None, None

            # Extract sequence number and stream ID
            seq_num = struct.unpack('>H', payload[2:4])[0]
            stream_id = struct.unpack('>H', payload[4:6])[0]

            return ethertype, seq_num, stream_id

        except Exception as e:
            return None, None, None

    def analyze_frame(self, frame: Ether):
        """Analyze a single frame"""
        self.total_frames += 1

        # Extract R-TAG
        ethertype, seq_num, stream_id = self.extract_rtag(frame)

        if ethertype is None:
            return  # Not an R-TAG frame

        self.rtag_frames += 1
        stats = self.stream_stats[stream_id]
        stats['count'] += 1

        # Check for duplicates
        if seq_num in stats['sequences']:
            self.duplicate_frames += 1
            stats['duplicates'] += 1
            status = "🔄 DUPLICATE"
        else:
            stats['sequences'].add(seq_num)
            status = "✅ NEW"

        # Check for sequence gaps
        if stats['last_seq'] != -1:
            expected_seq = (stats['last_seq'] + 1) & 0xFFFF
            if seq_num != expected_seq and seq_num not in stats['sequences']:
                gap = (seq_num - expected_seq) & 0xFFFF
                if gap < 1000:  # Reasonable gap
                    self.sequence_gaps += 1
                    status += f" ⚠️ GAP:{gap}"

        stats['last_seq'] = seq_num

        # Print frame info
        print(f"Frame #{self.total_frames:6d} | "
              f"Stream:{stream_id:4d} | "
              f"Seq:{seq_num:6d} | "
              f"{status}")

    def print_statistics(self):
        """Print final statistics"""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 60)
        print("📊 FRER Traffic Analysis Results")
        print("=" * 60)

        print(f"\n⏱️  Duration: {elapsed:.2f} seconds")
        print(f"📦 Total Frames: {self.total_frames}")
        print(f"🏷️  R-TAG Frames: {self.rtag_frames}")
        print(f"🔄 Duplicate Frames: {self.duplicate_frames}")
        print(f"⚠️  Sequence Gaps: {self.sequence_gaps}")

        if self.rtag_frames > 0:
            dup_rate = (self.duplicate_frames / self.rtag_frames) * 100
            print(f"📈 Duplication Rate: {dup_rate:.2f}%")

        print("\n🌊 Per-Stream Statistics:")
        for stream_id, stats in sorted(self.stream_stats.items()):
            print(f"\n   Stream {stream_id}:")
            print(f"      Total Frames: {stats['count']}")
            print(f"      Unique Sequences: {len(stats['sequences'])}")
            print(f"      Duplicates: {stats['duplicates']}")

            if stats['count'] > 0:
                dup_pct = (stats['duplicates'] / stats['count']) * 100
                print(f"      Duplication Rate: {dup_pct:.2f}%")

            if len(stats['sequences']) > 0:
                min_seq = min(stats['sequences'])
                max_seq = max(stats['sequences'])
                expected = (max_seq - min_seq + 1)
                actual = len(stats['sequences'])
                loss_pct = ((expected - actual) / expected * 100) if expected > 0 else 0

                print(f"      Sequence Range: {min_seq} - {max_seq}")
                print(f"      Expected: {expected}, Received: {actual}")
                print(f"      Loss Rate: {loss_pct:.2f}%")

        print("\n" + "=" * 60)

        # FRER effectiveness
        if self.duplicate_frames > 0:
            print("\n✅ FRER Replication Working: Duplicates detected")
        else:
            print("\n⚠️  No duplicates detected - Check FRER configuration")

        if self.sequence_gaps == 0 and len(self.seen_sequences) > 10:
            print("✅ FRER Elimination Working: No sequence gaps")
        elif self.sequence_gaps > 0:
            print(f"⚠️  Sequence gaps detected: {self.sequence_gaps}")

    def capture_traffic(self, count: int = 0, timeout: int = 60):
        """Capture and analyze FRER traffic"""
        print(f"\n🔍 Starting FRER Traffic Capture")
        print(f"   Interface: {self.interface}")
        print(f"   Target Stream ID: {self.stream_id}")
        print(f"   Count: {'Unlimited' if count == 0 else count}")
        print(f"   Timeout: {timeout} seconds")
        print(f"\n{'=' * 60}\n")

        try:
            sniff(
                iface=self.interface,
                prn=self.analyze_frame,
                count=count,
                timeout=timeout,
                filter="vlan",  # Only capture VLAN-tagged frames
                store=False
            )
        except KeyboardInterrupt:
            print("\n⚠️  Capture interrupted by user")
        except Exception as e:
            print(f"\n❌ Capture error: {e}")

        self.print_statistics()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze FRER traffic with R-TAG detection'
    )
    parser.add_argument('--interface', '-i', required=True,
                       help='Network interface (e.g., enp15s0)')
    parser.add_argument('--stream-id', '-s', type=int, default=1,
                       help='FRER Stream ID to monitor (default: 1)')
    parser.add_argument('--count', '-c', type=int, default=0,
                       help='Number of packets to capture (0=unlimited)')
    parser.add_argument('--timeout', '-t', type=int, default=60,
                       help='Capture timeout in seconds (default: 60)')

    args = parser.parse_args()

    # Check for root privileges
    if sys.platform.startswith('linux'):
        import os
        if os.geteuid() != 0:
            print("❌ This script requires root privileges (use sudo)")
            sys.exit(1)

    print("=" * 60)
    print("  FRER Traffic Analyzer")
    print("  IEEE 802.1CB Frame Analysis")
    print("=" * 60)

    analyzer = FRERAnalyzer(
        interface=args.interface,
        stream_id=args.stream_id
    )

    analyzer.capture_traffic(
        count=args.count,
        timeout=args.timeout
    )


if __name__ == "__main__":
    main()
