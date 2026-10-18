"""Original, royalty-free soundtrack synthesized for each Nubi video.
make_music(duration, timeline, seed, out_path) -> writes a 44.1 kHz stereo WAV."""
import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile

SR = 44100
PROGS = [
    [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]],  # C G Am F
    [[45, 48, 52], [41, 45, 48], [48, 52, 55], [43, 47, 50]],  # Am F C G
    [[50, 53, 57], [46, 50, 53], [41, 45, 48], [48, 52, 55]],  # Dm Bb F C
    [[43, 47, 50], [40, 43, 47], [48, 52, 55], [50, 54, 57]],  # G Em C D
]

def make_music(duration, timeline, seed=1, out_path='music.wav'):
    rng = np.random.default_rng(seed)
    N = int(SR * duration)
    L = np.zeros(N); Rr = np.zeros(N)
    bpm = [118, 120, 122, 124][seed % 4]
    BEAT = 60 / bpm
    PROG = PROGS[seed % len(PROGS)]
    t_ = lambda d: np.arange(int(SR * d)) / SR
    def add(sig, start, gain=1.0, pan=0.0):
        i = int(start * SR)
        if i >= N or i < 0: return
        s = sig[:N - i] * gain
        L[i:i + len(s)] += s * (1 - max(0, pan)); Rr[i:i + len(s)] += s * (1 + min(0, pan))
    def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
    def lp(x, f, o=2): b, a = butter(o, f / (SR / 2), 'low'); return lfilter(b, a, x)
    def hp(x, f, o=2): b, a = butter(o, f / (SR / 2), 'high'); return lfilter(b, a, x)
    note = lambda m: 440 * 2 ** ((m - 69) / 12)
    bar_len = 4 * BEAT
    chord_at = lambda t: PROG[int(t // bar_len) % 4]
    def kick():
        t = t_(.35); f = 45 + 90 * np.exp(-t * 28); ph = 2 * np.pi * np.cumsum(f) / SR
        return np.sin(ph) * np.exp(-t * 9) + 0.15 * np.sin(ph * 2) * np.exp(-t * 30)
    def clap():
        t = t_(.22); n = rng.standard_normal(len(t)); env = np.exp(-t * 22)
        for d in (0.0, 0.012, 0.024): env += np.exp(-np.maximum(0, t - d) * 90) * (t >= d) * 0.6
        return bp(n, 900, 3500) * env * 0.5
    def hat():
        t = t_(.05); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * 80) * 0.35
    def bass(m, d):
        t = t_(d); f = note(m); saw = 2 * ((t * f) % 1) - 1
        return (lp(saw, 500) + 0.6 * np.sin(2 * np.pi * f * t)) * np.minimum(1, t * 200) * np.exp(-t * 3.5) * 0.55
    def pluck(m, d=.45):
        t = t_(d); f = note(m); tri = 2 * np.abs(2 * ((t * f) % 1) - 1) - 1
        return (tri * 0.7 + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 7) * np.minimum(1, t * 300) * 0.22
    def pad(ch, d):
        t = t_(d); s = np.zeros(len(t))
        for m in ch:
            for det in (-0.08, 0, 0.08):
                f = note(m + 12) * 2 ** (det / 12); s += 2 * ((t * f + rng.random()) % 1) - 1
        return lp(s, 1400) / 9 * np.minimum(1, t / 0.25) * np.minimum(1, np.maximum(0, (d - t)) / 0.3) * 0.35
    def whoosh(d=.65):
        t = t_(d); n = rng.standard_normal(len(t)); seg = len(t) // 16; out = np.zeros(len(t))
        for k in range(16):
            c = 600 + k / 15 * 5000; sl = slice(k * seg, (k + 1) * seg if k < 15 else len(t))
            out[sl] = bp(n, max(100, c * .6), min(18000, c * 1.6), 1)[sl]
        return out * np.sin(np.pi * t / d) ** 2 * 0.5
    def click():
        t = t_(.06); return (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) + bp(rng.standard_normal(len(t)), 2000, 6000) * np.exp(-t * 120) * .4) * .35
    def chime(ms, step=.09, dec=2.2, g=.3):
        out = np.zeros(int(SR * (step * len(ms) + 1.6)))
        for i, m in enumerate(ms):
            t = t_(1.5); f = note(m)
            s = (np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t) + .12 * np.sin(2 * np.pi * 3.01 * f * t)) * np.exp(-t * dec)
            j = int(i * step * SR); out[j:j + len(s)] += s
        return out * g
    def riser(d):
        t = t_(d); return bp(rng.standard_normal(len(t)), 800, 9000, 1) * (t / d) ** 2 * .35
    def crash():
        t = t_(2.2); return hp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 2.2) * .28

    cuts = timeline['cuts']; groove_start = cuts[0]; end_t = timeline['end']
    sidechain = np.ones(N)
    def duck(at):
        i = int(at * SR); t = t_(.3); env = 1 - .55 * np.exp(-t * 12); j = min(N, i + len(t))
        if i < N: sidechain[i:j] = np.minimum(sidechain[i:j], env[:j - i])
    padbus = np.zeros(N); st = 0.0; bar = 0
    while st < duration:
        p = pad(PROG[bar % 4], min(bar_len + .1, duration - st)); i = int(st * SR); padbus[i:i + len(p)] += p[:N - i]; st += bar_len; bar += 1
    b = 0.0
    while b < duration:
        bi = int(round(b / BEAT)); inbar = bi % 4; ch = chord_at(b)
        full = groove_start <= b < end_t
        if full:
            add(kick(), b, .9); duck(b)
            if inbar in (1, 3): add(clap(), b, .8)
            add(hat(), b + BEAT / 2, .8, .3); add(hat(), b + BEAT / 4, .35, -.3); add(hat(), b + 3 * BEAT / 4, .35, -.3)
            add(bass(ch[0] - 12, BEAT / 2 * .95), b, 1); add(bass(ch[0] - 12, BEAT / 2 * .95), b + BEAT / 2, .8)
        arp = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24]; g = .9 if full else .6
        for k in range(2):
            m = arp[(bi * 2 + k) % 4]; add(pluck(m), b + k * BEAT / 2, g, .25 if k else -.25); add(pluck(m), b + k * BEAT / 2 + .1875, g * .35, -.4 if k else .4)
        b += BEAT
    for m in PROG[0]: add(pluck(m + 24, 2.5), max(0, duration - 2.6), .9)
    padbus *= sidechain; L += padbus; Rr += padbus
    add(riser(1.0), max(0, groove_start - 1.0), 1.0)
    for c in cuts: add(whoosh(), c - .4, .9)
    for tp in timeline.get('taps', []): add(click(), tp + .05, 1.0)
    add(riser(.8), timeline['reward'] - .8, 1.0); add(crash(), timeline['reward'], 1.0)
    for k in range(12): add(chime([84 + (k % 5)], 0, 9, .08), timeline['reward'] + .3 + k * .09, 1.0)
    add(chime([72, 76, 79, 84, 88], .07, 2.4, .28), timeline['levelup'], 1.0)
    add(crash(), end_t, .8); add(chime([79, 84, 88], .1, 2.0, .25), end_t + .1, 1.0)
    env = np.ones(N); fi = int(.05 * SR); env[:fi] = np.linspace(0, 1, fi); fo = int(1.5 * SR); env[-fo:] = np.linspace(1, 0, fo)
    stereo = np.tanh(np.stack([L * env, Rr * env], 1) * 1.2); stereo /= np.max(np.abs(stereo)) * 1.12
    wavfile.write(out_path, SR, (stereo * 32767).astype(np.int16))
    return out_path
