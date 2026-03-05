"""Mock EEG emotion pipeline for integration testing.

This script simulates EEG windows, predicts a 3-class emotion label,
and (optionally) sends the label to the chat collector via UDP.
"""

from __future__ import annotations

import argparse
import socket
from typing import Tuple

import numpy as np

EMOTION_MAP = {0: "neutral", 1: "nervous", 2: "happy"}


def simulate_eeg(
    mode: str,
    channels: int,
    samples: int,
    srate: int,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a mock EEG window with shape (channels, samples)."""
    rng = np.random.default_rng(seed)
    t = np.arange(samples) / float(srate)

    if mode == "calm":
        # low-amplitude alpha-like activity + weak noise
        base = 12.0 * np.sin(2 * np.pi * 10 * t)
        noise = rng.normal(0.0, 2.0, size=(channels, samples))
        signal = base + noise
    elif mode == "stress":
        # stronger beta-like activity + more noise
        base = 25.0 * np.sin(2 * np.pi * 22 * t)
        noise = rng.normal(0.0, 8.0, size=(channels, samples))
        signal = base + noise
    elif mode == "happy":
        # balanced rhythm + moderate noise
        base = 18.0 * np.sin(2 * np.pi * 14 * t)
        noise = rng.normal(0.0, 4.0, size=(channels, samples))
        signal = base + noise
    elif mode == "random":
        signal = rng.normal(0.0, 6.0, size=(channels, samples))
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    # channel-specific scaling
    ch_scale = rng.uniform(0.8, 1.2, size=(channels, 1))
    return signal * ch_scale


def classify_three_class(eeg: np.ndarray) -> Tuple[int, str, float]:
    """Rule-based 3-class mock classifier.

    Returns: (label_id, label_name, confidence)
    """
    std = float(np.std(eeg))

    # threshold-based labels for deterministic integration tests
    # label 0: neutral(calm), 1: nervous(stress), 2: happy(medium arousal)
    if std < 10.0:
        label_id = 0
        confidence = min(0.99, (10.0 - std) / 10.0 + 0.5)
    elif std > 18.0:
        label_id = 1
        confidence = min(0.99, (std - 18.0) / 10.0 + 0.5)
    else:
        label_id = 2
        confidence = min(0.99, 1.0 - abs(std - 14.0) / 8.0)

    return label_id, EMOTION_MAP[label_id], float(confidence)


def send_emotion(host: str, port: int, emotion: str, timeout: float = 5.0) -> None:
    """Send emotion text to UDP collector and wait for ack."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(emotion.encode("utf-8"), (host, port))
        data, _ = sock.recvfrom(1024)
        ack = data.decode("utf-8")
        if ack != "got it":
            raise RuntimeError(f"Unexpected collector ack: {ack}")
    finally:
        sock.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mock EEG -> 3-class emotion pipeline")
    parser.add_argument("--mode", choices=["calm", "stress", "happy", "random"], default="random")
    parser.add_argument("--channels", type=int, default=32)
    parser.add_argument("--samples", type=int, default=800)
    parser.add_argument("--srate", type=int, default=200)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--collector-host", default="127.0.0.1")
    parser.add_argument("--collector-port", type=int, default=4023)
    parser.add_argument("--dry-run", action="store_true", help="Only predict emotion; do not send UDP")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    eeg = simulate_eeg(args.mode, args.channels, args.samples, args.srate, args.seed)
    label_id, label_name, confidence = classify_three_class(eeg)

    print(f"[MockEEG] mode={args.mode} shape={eeg.shape}")
    print(f"[Emotion] label_id={label_id} label={label_name} confidence={confidence:.3f}")

    if not args.dry_run:
        send_emotion(args.collector_host, args.collector_port, label_name)
        print(f"[UDP] sent '{label_name}' to {args.collector_host}:{args.collector_port}")


if __name__ == "__main__":
    main()
