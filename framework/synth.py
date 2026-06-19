#!/usr/bin/env python3
"""Synthesize original chiptune lifecycle cues for a data theme.

Pure stdlib (wave), square-wave handheld-ish blips, 44.1kHz mono 16-bit PCM.
ALL ORIGINAL: no copyrighted game audio or copied melody.

Generates the four cues a theme maps to lifecycle transitions:
  start.wav    route pickup               (working begins)
  waiting.wav  soft chime cue             (waiting on you)
  success.wav  victory arpeggio           (finished OK)
  fail.wav     low descent                (failed)

Usage:  python3 synth.py [OUT_DIR]   (default: ./sounds)
"""
import math
import os
import struct
import sys
import wave

SR = 44100


def square(freq, dur, amp=0.28, duty=0.5, decay=8.0):
    out = []
    n = int(SR * dur)
    for i in range(n):
        t = i / SR
        v = amp if (freq * t) % 1.0 < duty else -amp
        env = math.exp(-decay * t)
        atk = min(1.0, i / (SR * 0.004))
        out.append(v * env * atk)
    return out


def silence(dur):
    return [0.0] * int(SR * dur)


def seq(*chunks):
    out = []
    for c in chunks:
        out += c
    return out


def write_wav(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    w.close()


# Equal-tempered note frequencies (A4=440) for the original short cues.
N = {
    "G3": 196.00, "A3": 220.00, "Bb3": 233.08,
    "D4": 293.66, "F4": 349.23, "G4": 392.00, "A4": 440.00, "Bb4": 466.16,
    "D5": 587.33, "F5": 698.46,
}


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write_wav(os.path.join(out_dir, "start.wav"),
              seq(square(N["G3"], 0.08, amp=0.24, duty=0.38, decay=3.0), silence(0.04),
                  square(N["Bb3"], 0.08, amp=0.24, duty=0.38, decay=3.0), silence(0.04),
                  square(N["D4"], 0.16, amp=0.25, duty=0.44, decay=3.5),
                  square(N["A4"], 0.22, amp=0.22, duty=0.30, decay=5.0)))
    write_wav(os.path.join(out_dir, "waiting.wav"),
              seq(square(N["F4"], 0.11, amp=0.18, duty=0.42, decay=5.0), silence(0.03),
                  square(N["D4"], 0.18, amp=0.18, duty=0.42, decay=6.0)))
    write_wav(os.path.join(out_dir, "success.wav"),
              seq(square(N["G4"], 0.09, amp=0.24, duty=0.45, decay=3.0),
                  square(N["Bb4"], 0.09, amp=0.24, duty=0.45, decay=3.0),
                  square(N["D5"], 0.09, amp=0.25, duty=0.45, decay=3.0),
                  square(N["F5"], 0.32, amp=0.27, duty=0.38, decay=3.4)))
    write_wav(os.path.join(out_dir, "fail.wav"),
              seq(square(N["D4"], 0.18, amp=0.22, duty=0.35, decay=2.4),
                  square(N["Bb3"], 0.18, amp=0.21, duty=0.35, decay=2.2),
                  square(N["G3"], 0.26, amp=0.20, duty=0.33, decay=1.8), silence(0.08),
                  square(N["G3"], 0.38, amp=0.16, duty=0.30, decay=1.4)))
    print("wrote start.wav waiting.wav success.wav fail.wav ->", out_dir)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sounds")
