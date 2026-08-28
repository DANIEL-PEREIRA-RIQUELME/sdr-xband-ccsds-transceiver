#!/usr/bin/env python3
"""
CCSDS CADU Transfer Frame Generator
====================================
Generates standard CCSDS 131.0-B-3 Transfer Frames (1784 bytes payload)
with 6-byte primary header, sequence count, pseudo-random data, and CRC-16 CCITT.

Usage:
    python3 generate_test_frames.py --frames 1000 --output ../data/test_signal_sample.bin
"""

import argparse
from pathlib import Path
import numpy as np


def crc16_ccitt(data: bytes) -> int:
    """Calculates CRC-16-CCITT (polynomial 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def generate_ccsds_frames(num_frames: int, output_path: Path, frame_size: int = 1784, padding_frames: int = 10):
    """Generates synthetic CCSDS transfer frames with CRC-16."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    header_length = 6
    crc_length = 2
    payload_length = frame_size - header_length - crc_length
    seq_bytes_length = 4
    random_payload_length = payload_length - seq_bytes_length

    print(f"Generating {num_frames:,} CCSDS Transfer Frames ({frame_size} bytes each) -> {output_path}...")

    with open(output_path, "wb") as f:
        for seq in range(num_frames):
            # 6-byte CCSDS Space Packet / CADU Primary Header
            header_id = b'\x08\x41'
            mcfc = (seq % 256).to_bytes(1, byteorder='big')
            length_word = (frame_size - 1).to_bytes(2, byteorder='big')
            flags = b'\x00'
            header = header_id + mcfc + length_word + flags

            # Sequence counter + random payload
            abs_seq_bytes = seq.to_bytes(seq_bytes_length, byteorder='big')
            random_payload = np.random.bytes(random_payload_length)
            payload = abs_seq_bytes + random_payload

            # Frame Data + CRC-16
            data_to_crc = header + payload
            crc_val = crc16_ccitt(data_to_crc)
            crc_bytes = crc_val.to_bytes(crc_length, byteorder='big')

            full_frame = data_to_crc + crc_bytes
            f.write(full_frame)

            if (seq + 1) % 10000 == 0 or (seq + 1) == num_frames:
                print(f"  [Progress] {seq + 1:,} / {num_frames:,} frames written.")

        # Optional trailing padding
        if padding_frames > 0:
            f.write(b'\x00' * (padding_frames * frame_size))

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[Done] Generated {file_size_mb:.2f} MB test file at {output_path}.")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic CCSDS CADU transfer frames.")
    parser.add_argument("--frames", type=int, default=1000, help="Number of CCSDS frames to generate (default: 1000)")
    parser.add_argument("--output", type=str, default="../data/test_signal_sample.bin", help="Output file path")
    parser.add_argument("--frame-size", type=int, default=1784, help="Frame size in bytes (default: 1784)")
    args = parser.parse_args()

    generate_ccsds_frames(args.frames, Path(args.output), args.frame_size)


if __name__ == "__main__":
    main()
