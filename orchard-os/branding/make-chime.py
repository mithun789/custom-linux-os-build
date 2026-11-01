#!/usr/bin/env python3
"""Generate the Orchard OS login chime (original, synthesized). Usage: make-chime.py OUT.wav"""
import math
import struct
import sys
import wave

RATE = 44100
DUR = 2.2
# A soft major chord (F major add9), notes start slightly staggered.
NOTES = [(349.23, 0.00), (440.00, 0.03), (523.25, 0.06), (783.99, 0.09)]


def sample(t):
    v = 0.0
    for f, start in NOTES:
        if t < start:
            continue
        tt = t - start
        env = (1 - math.exp(-tt * 60)) * math.exp(-tt * 2.2)
        v += env * (math.sin(2 * math.pi * f * tt) + 0.25 * math.sin(4 * math.pi * f * tt) * math.exp(-tt * 4))
    return v / len(NOTES)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "orchard-chime.wav"
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = bytearray()
        for i in range(int(RATE * DUR)):
            frames += struct.pack("<h", int(max(-1, min(1, sample(i / RATE) * 0.8)) * 32767))
        w.writeframes(bytes(frames))
    print("wrote", out)


if __name__ == "__main__":
    main()
