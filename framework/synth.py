#!/usr/bin/env python3
"""Synthesize original chiptune lifecycle cues for an agent-island theme — pure stdlib (wave),
square-wave NES-ish blips, 44.1kHz mono 16-bit PCM. ALL ORIGINAL: no copyrighted game audio.

Generates the four cues a theme maps to lifecycle transitions:
  start.wav    coin blip      (working begins)
  waiting.wav  pause beep     (waiting on you)
  success.wav  victory arp    (finished OK)
  fail.wav     game-over tune (failed)

Usage:  python3 synth.py [OUT_DIR]   (default: ./sounds)
"""
import wave, struct, math, os, sys

SR = 44100

def square(freq, dur, amp=0.28, duty=0.5, decay=8.0):
    out = []
    n = int(SR * dur)
    for i in range(n):
        t = i / SR
        v = amp if (freq * t) % 1.0 < duty else -amp
        env = math.exp(-decay * t)
        atk = min(1.0, i / (SR * 0.004))          # tiny attack so it doesn't click
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
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    w.close()

# Equal-tempered note frequencies (A4=440) for the notes we use.
N = {"C4": 261.63, "E4": 329.63, "G4": 392.00, "C5": 523.25, "D5": 587.33, "E5": 659.25,
     "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77, "C6": 1046.50, "E6": 1318.51, "G6": 1567.98}

def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    # coin: short low blip → higher sustained note (the classic two-step coin gesture, original tuning)
    write_wav(os.path.join(out_dir, "start.wav"),
              seq(square(N["B5"], 0.06, amp=0.30, decay=2.0), square(N["E6"], 0.34, amp=0.30, decay=6.0)))
    # pause / waiting: a gentle two-tone "your move" beep (down a third)
    write_wav(os.path.join(out_dir, "waiting.wav"),
              seq(square(N["E5"], 0.11, amp=0.22, decay=5.0), silence(0.02), square(N["C5"], 0.16, amp=0.22, decay=6.0)))
    # success: bright ascending arpeggio (C-E-G-C) — a "course clear" feel, original
    write_wav(os.path.join(out_dir, "success.wav"),
              seq(square(N["C5"], 0.10, amp=0.26, decay=3.0), square(N["E5"], 0.10, amp=0.26, decay=3.0),
                  square(N["G5"], 0.10, amp=0.26, decay=3.0), square(N["C6"], 0.40, amp=0.28, decay=3.5)))
    # fail: descending tune ending low — a "game over" feel, original
    write_wav(os.path.join(out_dir, "fail.wav"),
              seq(square(N["G5"], 0.14, amp=0.26, decay=3.0), square(N["E5"], 0.14, amp=0.26, decay=3.0),
                  square(N["C5"], 0.16, amp=0.26, decay=3.0), silence(0.04),
                  square(N["G4"], 0.30, amp=0.24, decay=2.2), square(N["C4"], 0.45, amp=0.22, decay=2.0)))
    print("wrote start.wav waiting.wav success.wav fail.wav ->", out_dir)

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sounds")
