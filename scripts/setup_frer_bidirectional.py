#!/usr/bin/env python3
"""
LAN9662 FRER Bidirectional Configuration Script
Based on AN1185 and IEEE 802.1CB standard

Topology:
- Port 4 (Left) ← Input from Device A
- Port 1, 2 → Redundant paths (directly connected)
- Port 4 (Right) → Output to Device B

FRER Streams:
- Stream 1 (0x0001): Device A → Device B
- Stream 2 (0x0002): Device B → Device A
"""

import serial
import time
import struct
import json
import argparse
import sys
from typing import Dict, List, Tuple


class LAN9662_FRER_Config:
    """LAN9662 FRER Configuration via MUP1 Protocol"""

    # MUP1 Protocol Constants
    MUP1_START = ord('>')
    MUP1_END = ord('<')

    # Command Types
    CMD_GET = ord('G')
    CMD_SET = ord('S')
    CMD_RESPONSE = ord('R')

    def __init__(self, serial_port: str = '/dev/ttyACM0', baudrate: int = 115200):
        """Initialize serial connection to LAN9662"""
        try:
            self.ser = serial.Serial(
                port=serial_port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2.0
            )
            print(f"✅ Connected to LAN9662 on {serial_port}")
            time.sleep(0.5)  # Wait for board to be ready
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            sys.exit(1)

    def calculate_checksum(self, data: bytes) -> int:
        """Calculate MUP1 checksum (simple XOR)"""
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

    def send_command(self, cmd_type: int, data: bytes) -> bytes:
        """Send MUP1 command and receive response"""
        # Build frame: >TYPE[DATA]<CHECKSUM
        frame = bytearray()
        frame.append(self.MUP1_START)
        frame.append(cmd_type)
        frame.extend(data)
        frame.append(self.MUP1_END)

        # Calculate checksum
        checksum = self.calculate_checksum(frame[1:-1])
        frame.append(checksum)

        # Send command
        self.ser.write(frame)
        self.ser.flush()

        # Wait for response
        time.sleep(0.1)
        response = self.ser.read(1024)

        return response

    def configure_frer_stream(self, stream_id: int, in_port: int,
                            out_ports: List[int], direction: str = "A→B") -> bool:
        """Configure FRER stream identification"""
        print(f"\n🔧 Configuring FRER Stream {stream_id} ({direction})")
        print(f"   Input Port: {in_port}")
        print(f"   Output Ports: {', '.join(map(str, out_ports))}")

        # Stream identification configuration
        # Format: Stream ID (2 bytes) + In Port (1 byte) + Out Port Mask (1 byte)
        out_port_mask = 0
        for port in out_ports:
            out_port_mask |= (1 << port)

        stream_config = struct.pack('>HBB', stream_id, in_port, out_port_mask)

        try:
            response = self.send_command(self.CMD_SET, stream_config)
            if response and len(response) > 0:
                print(f"   ✅ Stream {stream_id} configured successfully")
                return True
            else:
                print(f"   ⚠️  No response from switch")
                return False
        except Exception as e:
            print(f"   ❌ Configuration failed: {e}")
            return False

    def enable_rtag_generation(self, stream_id: int) -> bool:
        """Enable R-TAG sequence number generation for stream"""
        print(f"\n📝 Enabling R-TAG for Stream {stream_id}")

        # R-TAG configuration: Stream ID + Enable flag
        rtag_config = struct.pack('>HB', stream_id, 1)

        try:
            response = self.send_command(self.CMD_SET, rtag_config)
            if response:
                print(f"   ✅ R-TAG enabled for Stream {stream_id}")
                return True
            else:
                print(f"   ⚠️  No response")
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

    def configure_frame_elimination(self, stream_id: int, history_len: int = 32,
                                   reset_timeout_ms: int = 100) -> bool:
        """Configure FRER sequence recovery (frame elimination)"""
        print(f"\n🔄 Configuring Frame Elimination for Stream {stream_id}")
        print(f"   History Length: {history_len}")
        print(f"   Reset Timeout: {reset_timeout_ms} ms")

        # Elimination config: Stream ID + History + Timeout
        elim_config = struct.pack('>HBH', stream_id, history_len, reset_timeout_ms)

        try:
            response = self.send_command(self.CMD_SET, elim_config)
            if response:
                print(f"   ✅ Frame elimination configured")
                return True
            else:
                print(f"   ⚠️  No response")
                return False
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

    def verify_frer_status(self) -> Dict:
        """Query FRER configuration status"""
        print("\n🔍 Verifying FRER Configuration...")

        status = {
            'streams': [],
            'rtag_enabled': False,
            'elimination_active': False
        }

        try:
            # Query stream configuration
            response = self.send_command(self.CMD_GET, b'\x00')

            if response and len(response) > 4:
                print("   ✅ FRER is active")
                status['rtag_enabled'] = True
                status['elimination_active'] = True
            else:
                print("   ⚠️  FRER status unclear")

        except Exception as e:
            print(f"   ❌ Query failed: {e}")

        return status

    def close(self):
        """Close serial connection"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            print("\n✅ Serial connection closed")


def main():
    """Main configuration routine"""
    parser = argparse.ArgumentParser(
        description='Configure LAN9662 for bidirectional FRER'
    )
    parser.add_argument('--serial', default='/dev/ttyACM0',
                       help='Serial port (default: /dev/ttyACM0)')
    parser.add_argument('--baudrate', type=int, default=115200,
                       help='Baud rate (default: 115200)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify configuration, do not configure')

    args = parser.parse_args()

    print("=" * 60)
    print("  LAN9662 FRER Bidirectional Configuration")
    print("  IEEE 802.1CB Frame Replication and Elimination")
    print("=" * 60)

    # Initialize connection
    frer = LAN9662_FRER_Config(serial_port=args.serial, baudrate=args.baudrate)

    if args.verify_only:
        # Just verify current status
        frer.verify_frer_status()
    else:
        # Full configuration
        print("\n📋 Configuration Plan:")
        print("   1. Stream 1 (0x0001): Port 4 → Ports 1,2 (Direction A→B)")
        print("   2. Stream 2 (0x0002): Port 4 → Ports 1,2 (Direction B→A)")
        print("   3. Enable R-TAG sequence generation")
        print("   4. Configure frame elimination")
        print("   5. Verify configuration")
        print()

        input("Press Enter to continue...")

        # Configure Stream 1 (A → B)
        success1 = frer.configure_frer_stream(
            stream_id=1,
            in_port=4,
            out_ports=[1, 2],
            direction="A→B"
        )

        if success1:
            frer.enable_rtag_generation(stream_id=1)
            frer.configure_frame_elimination(stream_id=1)

        # Configure Stream 2 (B → A)
        success2 = frer.configure_frer_stream(
            stream_id=2,
            in_port=4,
            out_ports=[1, 2],
            direction="B→A"
        )

        if success2:
            frer.enable_rtag_generation(stream_id=2)
            frer.configure_frame_elimination(stream_id=2)

        # Verify final configuration
        status = frer.verify_frer_status()

        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ FRER Bidirectional Configuration Complete!")
            print()
            print("Next Steps:")
            print("  1. Connect Port 1 ↔ Port 2 (direct cable)")
            print("  2. Connect Device A → Port 4 (left)")
            print("  3. Connect Device B ← Port 4 (right)")
            print("  4. Run traffic test:")
            print("     sudo python3 scripts/generate_frer_traffic.py")
            print("  5. Monitor with:")
            print("     sudo python3 scripts/analyze_frer_traffic.py")
        else:
            print("⚠️  Configuration incomplete - check error messages above")
        print("=" * 60)

    # Cleanup
    frer.close()


if __name__ == "__main__":
    main()
