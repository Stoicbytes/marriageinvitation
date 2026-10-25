# Synthesises the invitation soundtrack: a festive Tamil-wedding style piece with a
# nadaswaram-like lead in raga Mohanam, thavil and jalra percussion, and a modern layer of
# warm chord pads, bass and shaker, ending with a getti melam flourish.
# Usage: python3 music.py out.wav [seconds]
import sys, wave
import numpy as np

SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 47.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
SA = 293.66                      # sruthi: D4
MOHANAM = [0, 2, 4, 7, 9]        # S R2 G3 P D2

def deg(d):
    o, i = divmod(d, 5)
    return MOHANAM[i] + 12 * o

def hz(semi):
    return SA * 2 ** (semi / 12)

PAD = N + SR * 4
bus = {k: np.zeros(PAD) for k in ('lead', 'pad', 'bass', 'drums', 'bells')}

def add(name, start, sig, gain=1.0):
    s = int(start * SR)
    if s >= PAD:
        return
    e = min(s + len(sig), PAD)
    bus[name][s:e] += gain * sig[:e - s]

def box(x, n):
    """Moving average over n samples (centred), used for smooth glides and envelopes."""
    if n < 2:
        return x
    c = np.cumsum(np.concatenate([[0], np.pad(x, (n // 2, n - n // 2 - 1), mode='edge')]))
    return (c[n:] - c[:-n]) / n

# ---------------------------------------------------------------- score
# chords per bar: I=D, IV=G, V=A, vi=Bm  (semitones above Sa)
CH = {'I': [0, 4, 7], 'IV': [5, 9, 12], 'V': [7, 11, 14], 'vi': [9, 12, 16]}
ROOT = {'I': 0, 'IV': 5, 'V': 7, 'vi': 9}
bars = (['I', 'I'] +                                   # 0-1 intro
        ['I', 'IV', 'I', 'V', 'IV', 'I'] +             # 2-7 phrase A
        ['IV', 'I', 'vi', 'V', 'IV', 'I', 'V', 'I'] +  # 8-15 phrase B
        ['I', 'V'] +                                   # 16-17 getti melam
        ['I', 'I'])                                    # 18-19 ending

# melody as (scale degree, beats); None = rest.  Degrees: 0=S 1=R 2=G 3=P 4=D 5=S' 6=R' 7=G'
intro = [(None, 4), (0, 2), (1, 1), (2, 1)]
A = [(3, 1), (4, .5), (3, .5), (2, 1), (1, 1), (0, 2), (1, 1), (2, 1),
     (2, 1), (3, 1), (4, 1), (5, 1), (4, 1.5), (3, .5), (2, 2),
     (3, .5), (4, .5), (5, 1), (6, 1), (5, 1), (4, 1), (3, 1), (2, .5), (1, .5), (0, 1)]
B = [(5, 1), (5, .5), (4, .5), (3, 1), (4, 1), (5, 2), (7, 1), (6, 1),
     (5, 1), (4, 1), (3, 1), (2, 1), (3, 3), (2, .5), (3, .5),
     (4, 1), (5, .5), (4, .5), (3, 1), (2, 1), (1, 1), (2, 1), (3, 2),
     (2, .5), (3, .5), (4, 1), (3, 1), (2, 1), (1, 1), (0, 3)]
getti = [(6 if i % 2 else 5, .25) for i in range(28)] + [(7, 1)]
ending = [(5, 6), (None, 2)]
melody = intro + A + B + getti + ending

# ---------------------------------------------------------------- nadaswaram-style lead
logf = np.zeros(N)
amp = np.zeros(N)
vib_env = np.zeros(N)
t_beat = 0.0
prev_end = -1
for d, b in melody:
    s, e = int(t_beat * BEAT * SR), int((t_beat + b) * BEAT * SR)
    e = min(e, N)
    if d is not None and s < N:
        n = e - s
        tt = np.arange(n) / SR
        logf[s:e] = np.log(hz(deg(d)))
        env = np.minimum(1, tt / 0.035) * (0.82 + 0.18 * np.exp(-tt / 0.25))
        rel = np.clip((n - np.arange(n)) / (0.05 * SR), 0, 1)
        env *= rel if b >= 1 else np.clip((n - np.arange(n)) / (0.015 * SR), 0.55, 1)
        if prev_end == s:                     # slurred: gentle tonguing dip instead of silence
            env = np.maximum(env, 0.55 * rel)
        amp[s:e] = env
        vib_env[s:e] = np.clip((tt - 0.18) / 0.3, 0, 1)
        prev_end = e
    t_beat += b
# hold the last pitch through rests so glides start from the right place
idx = np.where(logf > 0, np.arange(N), 0)
np.maximum.accumulate(idx, out=idx)
filled = logf[idx]
filled[filled == 0] = np.log(SA)
filled = box(filled, int(0.045 * SR))          # portamento between notes
t = np.arange(N) / SR
filled += vib_env * 0.007 * np.sin(2 * np.pi * 5.6 * t)
f = np.exp(filled)
amp = box(amp, int(0.006 * SR))
phase = 2 * np.pi * np.cumsum(f) / SR
lead = np.zeros(N)
for k in range(1, 15):
    fk = f * k
    a = k ** -0.95 * (1 + 1.3 * np.exp(-((fk - 1400) / 700) ** 2))   # reedy formant
    a = a * (fk < 16000) * (1 - 0.35 * (k % 2 == 0))
    lead += a * np.sin(k * phase)
lead *= amp / 2.2
bus['lead'][:N] += lead

# ---------------------------------------------------------------- pads (modern layer)
def pad_note(freq, length):
    n = int(length * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    for det in (-0.004, 0, 0.004):
        ph = rng.uniform(0, 6.28, 9)
        for k in range(1, 9):
            sig += np.sin(2 * np.pi * freq * (1 + det) * k * tt + ph[k]) / k ** 1.7
    env = np.minimum(1, tt / 0.5) * np.clip((length - tt) / 0.7, 0, 1)
    return sig * env / 3

for i, c in enumerate(bars):
    start = i * BAR
    if start >= DUR:
        break
    for s in CH[c]:
        add('pad', start, pad_note(hz(s - 12), BAR + 0.7), 0.5)

# ---------------------------------------------------------------- bass
def bass_note(freq, length=0.9):
    n = int(length * SR)
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / 0.008) * np.exp(-tt / 0.35)
    return env * (np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(4 * np.pi * freq * tt))

for i, c in enumerate(bars):
    if 2 <= i <= 18:
        r = hz(ROOT[c] - 24)
        add('bass', i * BAR, bass_note(r))
        if i < 18:
            add('bass', i * BAR + 2.5 * BEAT, bass_note(r, 0.5), 0.7)
            add('bass', i * BAR + 3 * BEAT, bass_note(r * 1.5, 0.5), 0.6)

# ---------------------------------------------------------------- percussion
def noise(n):
    return rng.uniform(-1, 1, n)

def kick():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    fr = 55 + 95 * np.exp(-tt / 0.035)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt / 0.17)

def tha(pitch=330):                 # thavil right-hand stroke
    n = int(0.22 * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * pitch * tt * (1 + 0.15 * np.exp(-tt / 0.01))) * np.exp(-tt / 0.05)
    click = np.diff(noise(n + 1)) * np.exp(-tt / 0.006)
    return body + 0.35 * click

def shaker():
    n = int(0.06 * SR); tt = np.arange(n) / SR
    x = np.diff(np.diff(noise(n + 2)))
    return x * np.exp(-tt / 0.018) * np.minimum(1, tt / 0.004)

def jalra():                        # small hand cymbals
    n = int(0.5 * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * fq * tt + rng.uniform(0, 6.28)) for fq in (3120, 4250, 5390, 6830))
    return s * np.exp(-tt / 0.11) / 4

K, T, S, J = kick(), tha(), shaker(), jalra()
T2 = tha(250)
for i in range(len(bars)):
    t0 = i * BAR
    if t0 >= DUR:
        break
    e8 = lambda x: t0 + x * BEAT / 2          # eighth-note grid
    if 2 <= i <= 15:
        full = i >= 8
        for x in (0, 3, 4):
            add('drums', e8(x), K, 0.9 if full else 0.6)
        for x in (2, 6):
            add('drums', e8(x), T, 0.55 if full else 0.4)
        for x in (5, 7):
            add('drums', e8(x), T2, 0.25)
        if i >= 4:
            for x in range(16):
                add('drums', t0 + x * BEAT / 4, S, (0.16 if x % 2 else 0.09) * (1.3 if full else 1))
        add('drums', e8(0), J, 0.5 if full else 0.3)
        add('drums', e8(4), J, 0.3)
    elif i in (16, 17):                      # getti melam: rolling thavil + jalra, building up
        for x in range(16):
            prog = ((i - 16) * 16 + x) / 32
            add('drums', t0 + x * BEAT / 4, T if x % 2 == 0 else T2, 0.3 + 0.5 * prog)
        for x in range(4):
            add('drums', t0 + x * BEAT, K, 0.9)
            add('drums', t0 + x * BEAT, J, 0.6)
    elif i == 18:
        add('drums', t0, K, 1.0); add('drums', t0, J, 0.8)

# ---------------------------------------------------------------- bright temple bells
def bell(freq, length=2.5):
    n = int(length * SR); tt = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * tt) * np.exp(-tt / 1.3)
         + .35 * np.sin(2 * np.pi * 2 * freq * tt) * np.exp(-tt / .7)
         + .12 * np.sin(2 * np.pi * 3 * freq * tt) * np.exp(-tt / .4))
    return s * np.minimum(1, tt / 0.002)

for k, semi in enumerate([24, 28, 31, 36]):
    add('bells', 0.15 + k * 0.22, bell(hz(semi)), 0.5)
for k, semi in enumerate([24, 31, 36]):
    add('bells', 6.25 + k * 0.18, bell(hz(semi)), 0.4)
for k, semi in enumerate([36, 31, 28, 24, 36]):
    add('bells', 18 * BAR + 0.1 + k * 0.25, bell(hz(semi), 3), 0.45)

# ---------------------------------------------------------------- mix
gains = {'lead': 0.55, 'pad': 0.16, 'bass': 0.28, 'drums': 0.42, 'bells': 0.18}
mix = sum(g * bus[k] for k, g in gains.items())[:N]

# short, warm room reverb
ir_len = int(SR * 0.9)
ir = rng.normal(0, 1, ir_len) * np.exp(-np.arange(ir_len) / (SR * 0.18))
ir = box(ir, 8); ir[:int(0.012 * SR)] = 0
L = 1 << int(np.ceil(np.log2(N + ir_len)))
wet = np.fft.irfft(np.fft.rfft(mix, L) * np.fft.rfft(ir, L), L)[:N]
wet *= 0.22 * np.sqrt(np.mean(mix ** 2) / (np.mean(wet ** 2) + 1e-12))
mix = mix + wet

fade = np.ones(N)
fi, fo = int(SR * 0.05), int(SR * 2.2)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
mix *= fade
mix = np.tanh(1.6 * mix / np.abs(mix).max()) / np.tanh(1.6) * 0.9
stereo = np.stack([mix, np.roll(mix, 180)], 1)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
