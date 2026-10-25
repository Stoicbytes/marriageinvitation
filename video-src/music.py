# Synthesises the invitation video's soundtrack: temple bell, tanpura drone and a
# veena-style melody in raga Mayamalavagowla (plucked-string Karplus-Strong synthesis).
# Usage: python3 music.py out.wav [seconds]
import sys, wave
import numpy as np

SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 47.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
out = np.zeros(N + SR * 10)

def pluck(freq, start, length=2.5, gain=0.3, bright=0.5, decay=0.996):
    """Karplus-Strong string, vectorised one period at a time."""
    p = int(SR / freq)
    n = int(SR * length)
    y = np.zeros(n + p + 1)
    burst = rng.uniform(-1, 1, p)
    # soften the excitation for a mellow veena tone
    for _ in range(int((1 - bright) * 4)):
        burst = 0.5 * (burst + np.roll(burst, 1))
    y[:p] = burst
    y[p] = burst[0]
    i = p + 1
    while i < n + p:
        j = min(i + p, n + p)
        y[i:j] = decay * 0.5 * (y[i - p:j - p] + y[i - p - 1:j - p - 1])
        i = j
    y = y[p:p + n]
    env = np.minimum(1, np.arange(n) / (SR * 0.004))
    s = int(start * SR)
    out[s:s + n] += gain * y * env

def bell(start, base=659.0, gain=0.22, length=5.0):
    t = np.arange(int(SR * length)) / SR
    tone = np.zeros_like(t)
    for ratio, amp, dec in [(1, 1, 1.4), (2.0, .55, 1.0), (2.76, .4, .8), (5.4, .25, .5), (8.93, .12, .3)]:
        tone += amp * np.sin(2 * np.pi * base * ratio * t) * np.exp(-t / dec)
    tone *= np.minimum(1, t / 0.002)
    s = int(start * SR)
    out[s:s + len(t)] += gain * tone / 2.3

SA = 196.0  # sruthi (G3)
# Mayamalavagowla: S R1 G3 M1 P D1 N3 S'
ratios = [1, 16/15, 5/4, 4/3, 3/2, 8/5, 15/8, 2]
note = lambda k: SA * (ratios[k % 7] * (2 ** (k // 7)) if k >= 0 else ratios[k % 7] / 2)

# tanpura: P S' S' S cycle throughout
t = 0.0
while t < DUR + 1:
    for k, f in enumerate([SA * 3/4, SA, SA, SA / 2]):
        pluck(f, t + k * 0.62, length=3.6, gain=0.09, bright=0.9, decay=0.9993)
    t += 2.6

# melody phrases (scale degrees, beats)
phrases = [
    [(0, 2), (1, 1), (2, 1), (3, 2), (4, 2)],
    [(5, 1), (4, 1), (3, 1), (2, 1), (3, 2), (2, 1), (1, 1), (0, 4)],
    [(4, 2), (5, 1), (7, 1), (8, 2), (7, 1), (6, 1), (5, 2), (4, 2)],
    [(3, 1), (4, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 2), (0, 4)],
    [(0, 1), (2, 1), (4, 1), (7, 1), (9, 2), (8, 1), (7, 1), (7, 4)],
    [(6, 1), (5, 1), (4, 2), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1), (2, 1), (0, 4)],
]
beat = 0.5
t = 2.2
while t < DUR - 5:
    for ph in phrases:
        for k, b in ph:
            if t > DUR - 5:
                break
            pluck(note(k), t, length=2.2, gain=0.34, bright=0.55, decay=0.9975)
            # gentle octave shimmer on long notes
            if b >= 2:
                pluck(note(k) * 2, t + 0.02, length=1.4, gain=0.06, bright=0.4)
            t += b * beat
        t += beat
final = DUR - 4.2
for k, d in [(0, 0), (4, 0.25), (7, 0.5)]:
    pluck(note(k), final + d, length=4, gain=0.3, bright=0.5, decay=0.9985)

# temple bells: opening, at the names, and at the close
for s, b in [(0.05, 659.0), (0.85, 784.0), (6.3, 659.0), (40.1, 659.0), (DUR - 4.4, 784.0)]:
    bell(s, b)

y = out[:N]
# simple room reverb (exponentially decaying noise impulse response)
ir_len = int(SR * 1.8)
ir = rng.normal(0, 1, ir_len) * np.exp(-np.arange(ir_len) / (SR * 0.45))
ir[0] = 0
L = 1 << int(np.ceil(np.log2(len(y) + ir_len)))
wet = np.fft.irfft(np.fft.rfft(y, L) * np.fft.rfft(ir, L), L)[:len(y)]
wet *= 0.25 * np.abs(y).max() / (np.abs(wet).max() + 1e-9)
mix = y + wet
fade = np.ones(N); fi, fo = int(SR * 0.6), int(SR * 2.5)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade
mix = 0.85 * mix / np.abs(mix).max()
stereo = np.stack([mix, np.roll(mix, 220)], 1)  # light stereo width
pcm = (stereo * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
